import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from app.core.security.auth import (
    create_access_token,
    create_refresh_token,
)
from app.core.settings import get_cookie_samesite, get_cookie_secure
from app.main import limiter
from jose import jwt

from conftest import _test_public_key, auth_header

# ── RS256 トークン生成・検証 ──────────────────────────────────────


def test_create_access_token_contains_username() -> None:
    token = create_access_token("alice")
    payload = jwt.decode(token, _test_public_key, algorithms=["RS256"])

    assert payload["sub"] == "alice"


def test_create_access_token_has_expiry() -> None:
    token = create_access_token("alice")
    payload = jwt.decode(token, _test_public_key, algorithms=["RS256"])

    assert "exp" in payload


def test_create_access_token_type_is_access() -> None:
    token = create_access_token("alice")
    payload = jwt.decode(token, _test_public_key, algorithms=["RS256"])

    assert payload["type"] == "access"


def test_create_refresh_token_type_is_refresh() -> None:
    token, jti = create_refresh_token("alice")
    payload = jwt.decode(token, _test_public_key, algorithms=["RS256"])

    assert payload["type"] == "refresh"
    assert payload["sub"] == "alice"
    assert payload["jti"] == jti


def test_hs256_token_rejected_by_rs256_verification() -> None:
    """HS256 で署名したトークンが RS256 の検証で拒否されることを確認する。"""
    hs256_token = jwt.encode({"sub": "alice", "type": "access"}, "secret", algorithm="HS256")

    with pytest.raises(Exception):
        jwt.decode(hs256_token, _test_public_key, algorithms=["RS256"])


def test_access_token_cannot_be_used_as_refresh(client) -> None:
    """アクセストークンでリフレッシュエンドポイントを叩いて拒否されることを確認する。"""
    auth_header(client, "rftest")
    # 既存の有効なリフレッシュトークンを削除してアクセストークンで置き換える
    access_token = client.cookies.get("access_token", "")
    del client.cookies["refresh_token"]
    client.cookies.set("refresh_token", access_token)

    response = client.post("/auth/refresh")

    assert response.status_code == 401


def test_refresh_token_cannot_access_api(client) -> None:
    """リフレッシュトークンで通常 API を叩いて拒否されることを確認する。"""
    auth_header(client, "apitest")
    refresh_token, _ = create_refresh_token("apitest")
    client.cookies.set("access_token", refresh_token)

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_refresh_issues_new_access_token(client) -> None:
    """有効なリフレッシュトークンで新しいアクセストークンが発行されることを確認する。"""
    auth_header(client, "refuser")

    response = client.post("/auth/refresh")

    assert response.status_code == 200
    assert response.json()["username"] == "refuser"
    assert "access_token=" in response.headers.get("set-cookie", "")


# ── ログアウト ────────────────────────────────────────────────────


def test_logout_clears_cookies(client) -> None:
    """ログアウト後に認証 Cookie が削除されることを確認する。"""
    auth_header(client, "logoutuser")

    response = client.post("/auth/logout")

    assert response.status_code == 204
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie


def test_logout_invalidates_refresh_token(client) -> None:
    """ログアウト後にリフレッシュトークンで再認証できないことを確認する。"""
    auth_header(client, "logoutuser2")

    client.post("/auth/logout")
    response = client.post("/auth/refresh")

    assert response.status_code == 401


def test_refresh_rejects_revoked_jti(client) -> None:
    """DB の refresh_jti と一致しないトークンでリフレッシュが拒否されることを確認する。"""
    auth_header(client, "revokeduser")
    # jti が DB と一致しない別トークンを発行してセット
    stale_token, _ = create_refresh_token("revokeduser")
    client.cookies.set("refresh_token", stale_token)

    response = client.post("/auth/refresh")

    assert response.status_code == 401


def test_logout_without_token_returns_204(client) -> None:
    """リフレッシュトークンなしでもログアウトが 204 を返すことを確認する。"""
    response = client.post("/auth/logout")

    assert response.status_code == 204


# ── Cookie 設定 ───────────────────────────────────────────────────


def test_cookie_secure_defaults_false_for_localhost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("COOKIE_SECURE", raising=False)
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")

    assert get_cookie_secure() is False


def test_cookie_secure_defaults_true_when_non_local_origin_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("COOKIE_SECURE", raising=False)
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "http://localhost:5173,https://app.example.com",
    )

    assert get_cookie_secure() is True


def test_cookie_samesite_defaults_lax_for_localhost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("COOKIE_SAMESITE", raising=False)
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")

    assert get_cookie_samesite() == "lax"


def test_cookie_samesite_defaults_none_for_non_local_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("COOKIE_SAMESITE", raising=False)
    monkeypatch.setenv("CORS_ORIGINS", "https://storage.googleapis.com")

    assert get_cookie_samesite() == "none"


# ── /auth/me ─────────────────────────────────────────────────────


def test_me_returns_current_user(client) -> None:
    auth_header(client, "alice")

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "username": "alice",
        "is_github_user": False,
    }


# ── CSRF ─────────────────────────────────────────────────────────


def _csrf_resume_payload() -> dict:
    return {
        "full_name": "テスト",
        "career_summary": "要約",
        "self_pr": "自己PR",
        "experiences": [],
        "qualifications": [],
    }


def test_post_without_csrf_token_is_rejected(client) -> None:
    """CSRFトークンなしの POST リクエストが 403 で拒否されることを確認する。"""
    auth_header(client, "csrftest1")
    client.cookies.delete("csrf_token")

    response = client.post(
        "/api/resumes",
        json=_csrf_resume_payload(),
        # CSRF ヘッダーなし
    )

    assert response.status_code == 403


def test_post_with_invalid_csrf_token_is_rejected(client) -> None:
    """不正な CSRFトークンの POST リクエストが 403 で拒否されることを確認する。"""
    auth_header(client, "csrftest2")

    response = client.post(
        "/api/resumes",
        json=_csrf_resume_payload(),
        headers={"X-CSRF-Token": "invalid-token"},
    )

    assert response.status_code == 403


def test_post_with_valid_csrf_token_succeeds(client) -> None:
    """正しい CSRF トークンの POST リクエストが成功することを確認する。"""
    headers = auth_header(client, "csrftest3")

    response = client.post(
        "/api/resumes",
        json=_csrf_resume_payload(),
        headers=headers,
    )

    assert response.status_code == 201


def test_get_request_skips_csrf_check(client) -> None:
    """GET リクエストは CSRF チェックをスキップすることを確認する。"""
    auth_header(client, "csrftest4")

    response = client.get("/auth/me")

    assert response.status_code == 200


# ── GitHub OAuth ──────────────────────────────────────────────────


def test_github_login_url_sets_state_cookie(client) -> None:
    response = client.get(
        "/auth/github/login-url",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    assert "https://github.com/login/oauth/authorize" in response.json()["authorization_url"]
    assert "github_oauth_state=" in response.headers["set-cookie"]


def test_github_login_url_uses_forwarded_https_scheme(client) -> None:
    response = client.get(
        "/auth/github/login-url",
        headers={
            "Origin": "http://localhost:5173",
            "Host": "devforge-dev-nktebahhoq-an.a.run.app",
            "X-Forwarded-Proto": "https",
        },
    )

    assert response.status_code == 200
    parsed = urlparse(response.json()["authorization_url"])
    redirect_uri = parse_qs(parsed.query)["redirect_uri"][0]
    assert redirect_uri == "https://devforge-dev-nktebahhoq-an.a.run.app/auth/github/callback"


def test_github_login_redirect_sets_cookies_and_redirects(client) -> None:
    response = client.get(
        "/auth/github/login",
        params={"return_to": "http://localhost:5173/index.html"},
        headers={
            "Host": "devforge-dev-nktebahhoq-an.a.run.app",
            "X-Forwarded-Proto": "https",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "https://github.com/login/oauth/authorize" in response.headers["location"]
    assert "github_oauth_state=" in response.headers["set-cookie"]
    parsed = urlparse(response.headers["location"])
    redirect_uri = parse_qs(parsed.query)["redirect_uri"][0]
    assert redirect_uri == "https://devforge-dev-nktebahhoq-an.a.run.app/auth/github/callback"


def test_github_callback_redirect_rejects_state_mismatch(client) -> None:
    client.cookies.set("github_oauth_state", "expected-state")
    client.cookies.set("github_oauth_redirect", "http://localhost:5173/index.html")

    with patch("httpx.AsyncClient") as mock_async_client:
        response = client.get(
            "/auth/github/callback?code=test-code&state=wrong-state",
            follow_redirects=False,
        )

    assert response.status_code == 200
    assert mock_async_client.call_count == 0
    # 200 + HTML リダイレクト: URL が HTML 本文に含まれていることを確認する
    assert "localhost:5173" in response.text
    assert "github_error=" in response.text


def test_github_callback_redirect_sets_auth_cookie(client) -> None:
    client.cookies.set("github_oauth_state", "expected-state")
    client.cookies.set("github_oauth_redirect", "http://localhost:5173/index.html")

    token_response = MagicMock()
    token_response.json.return_value = {"access_token": "github-access-token"}
    user_response = MagicMock()
    user_response.json.return_value = {"id": 12345, "login": "octocat"}

    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post.return_value = token_response
        mock_http.get.return_value = user_response
        mock_cls.return_value = mock_http

        response = client.get(
            "/auth/github/callback?code=test-code&state=expected-state",
            follow_redirects=False,
        )

    assert response.status_code == 200
    # 200 + HTML リダイレクト: フロントエンド URL が HTML 本文に含まれていることを確認する
    assert "localhost:5173/index.html" in response.text
    assert "access_token=" in response.headers["set-cookie"]


def test_begin_github_oauth_state_cookie_is_httponly(client) -> None:
    """begin_github_oauth が設定する state Cookie が HttpOnly であることを確認する。"""
    response = client.get(
        "/auth/github/login-url",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    # Set-Cookie ヘッダーに HttpOnly が含まれていることを確認する
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "github_oauth_state=" in set_cookie_header
    assert "httponly" in set_cookie_header.lower()


def test_begin_github_oauth_state_cookie_has_samesite(client) -> None:
    """begin_github_oauth が設定する state Cookie に SameSite 属性が含まれることを確認する。"""
    response = client.get(
        "/auth/github/login-url",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "github_oauth_state=" in set_cookie_header
    assert "samesite=" in set_cookie_header.lower()


# ── 不正アクセス追跡: 認証失敗ログ ────────────────────────────────


def _auth_failed_records(records: list[logging.LogRecord]) -> list[logging.LogRecord]:
    """auth_failed イベント (devforge ロガー WARNING) のみ抽出する。"""
    return [r for r in records if r.name == "devforge" and r.message == "auth_failed"]


def test_auth_failed_logged_when_cookie_missing(client, caplog) -> None:
    """Cookie 無しで保護 API を叩くと reason=missing_cookie の WARNING が出ることを確認する。"""
    client.cookies.clear()
    with caplog.at_level(logging.WARNING, logger="devforge"):
        response = client.get("/auth/me")

    assert response.status_code == 401
    records = _auth_failed_records(caplog.records)
    assert any(getattr(r, "reason", None) == "missing_cookie" for r in records)


def test_auth_failed_logged_for_invalid_jwt(client, caplog) -> None:
    """不正な JWT で 401 + reason=jwt_decode_error がログされることを確認する。"""
    client.cookies.clear()
    client.cookies.set("access_token", "not-a-valid-jwt")
    with caplog.at_level(logging.WARNING, logger="devforge"):
        response = client.get("/auth/me")

    assert response.status_code == 401
    records = _auth_failed_records(caplog.records)
    assert any(getattr(r, "reason", None) == "jwt_decode_error" for r in records)


def test_auth_failed_logged_for_user_not_found(client, caplog) -> None:
    """DB に存在しないユーザー名のトークンで reason=user_not_found がログされることを確認する。"""
    token = create_access_token("nonexistent-user-xyz")
    client.cookies.clear()
    client.cookies.set("access_token", token)
    with caplog.at_level(logging.WARNING, logger="devforge"):
        response = client.get("/auth/me")

    assert response.status_code == 401
    records = _auth_failed_records(caplog.records)
    assert any(getattr(r, "reason", None) == "user_not_found" for r in records)


# ── レートリミット ──────────────────────────────────────────────


def test_auth_me_rate_limited_after_threshold(client) -> None:
    """/auth/me が 60/分の上限を超えると 429 を返すことを確認する。"""
    auth_header(client, "rl-user")
    limiter.reset()
    statuses: list[int] = []
    for _i in range(65):
        resp = client.get("/auth/me")
        statuses.append(resp.status_code)
        if resp.status_code == 429:
            break
    assert 429 in statuses
    # 上限到達前に少なくとも数件は 200 を返している
    assert statuses.count(200) >= 50
    limiter.reset()


# 使用しない環境変数を参照するだけのプレースホルダー（lint 対策）
_ = os.environ
