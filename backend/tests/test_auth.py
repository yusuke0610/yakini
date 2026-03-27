import os
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from app.core.security.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.core.settings import get_cookie_samesite, get_cookie_secure
from jose import jwt

from conftest import _test_public_key, auth_header

# ── パスワードハッシュ ────────────────────────────────────────────


def test_hash_and_verify_password() -> None:
    hashed = hash_password("secret123")

    assert verify_password("secret123", hashed)


def test_verify_wrong_password() -> None:
    hashed = hash_password("secret123")

    assert not verify_password("wrong", hashed)


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
    token = create_refresh_token("alice")
    payload = jwt.decode(token, _test_public_key, algorithms=["RS256"])

    assert payload["type"] == "refresh"
    assert payload["sub"] == "alice"


def test_hs256_token_rejected_by_rs256_verification() -> None:
    """HS256 で署名したトークンが RS256 の検証で拒否されることを確認する。"""
    hs256_token = jwt.encode({"sub": "alice", "type": "access"}, "secret", algorithm="HS256")

    with pytest.raises(Exception):
        jwt.decode(hs256_token, _test_public_key, algorithms=["RS256"])


def test_access_token_cannot_be_used_as_refresh(client) -> None:
    """アクセストークンでリフレッシュエンドポイントを叩いて拒否されることを確認する。"""
    # ログインしてアクセストークンを取得
    client.post(
        "/auth/register",
        json={"username": "rftest", "email": "rftest@example.com", "password": "SecurePass123"},
    )
    client.post(
        "/auth/login",
        json={"email": "rftest@example.com", "password": "SecurePass123"},
    )
    # アクセストークンをリフレッシュ Cookie に偽装してリフレッシュを試みる
    access_token = client.cookies.get("access_token", "")
    client.cookies.set("refresh_token", access_token, path="/auth/refresh")

    response = client.post("/auth/refresh")

    assert response.status_code == 401


def test_refresh_token_cannot_access_api(client) -> None:
    """リフレッシュトークンで通常 API を叩いて拒否されることを確認する。"""
    client.post(
        "/auth/register",
        json={"username": "apitest", "email": "apitest@example.com", "password": "SecurePass123"},
    )
    client.post(
        "/auth/login",
        json={"email": "apitest@example.com", "password": "SecurePass123"},
    )
    refresh_token = create_refresh_token("apitest")
    client.cookies.set("access_token", refresh_token)

    response = client.get("/auth/me")

    assert response.status_code == 401


def test_refresh_issues_new_access_token(client) -> None:
    """有効なリフレッシュトークンで新しいアクセストークンが発行されることを確認する。"""
    client.post(
        "/auth/register",
        json={"username": "refuser", "email": "refuser@example.com", "password": "SecurePass123"},
    )
    client.post(
        "/auth/login",
        json={"email": "refuser@example.com", "password": "SecurePass123"},
    )

    response = client.post("/auth/refresh")

    assert response.status_code == 200
    assert response.json()["username"] == "refuser"
    assert "access_token=" in response.headers.get("set-cookie", "")


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


def test_post_without_csrf_token_is_rejected(client) -> None:
    """CSRFトークンなしの POST リクエストが 403 で拒否されることを確認する。"""
    auth_header(client, "csrftest1")
    client.cookies.delete("csrf_token")

    response = client.post(
        "/api/basic-info",
        json={
            "full_name": "テスト",
            "name_furigana": "てすと",
            "record_date": "2026-01-01",
            "qualifications": [],
        },
        # CSRF ヘッダーなし
    )

    assert response.status_code == 403


def test_post_with_invalid_csrf_token_is_rejected(client) -> None:
    """不正な CSRFトークンの POST リクエストが 403 で拒否されることを確認する。"""
    auth_header(client, "csrftest2")

    response = client.post(
        "/api/basic-info",
        json={
            "full_name": "テスト",
            "name_furigana": "てすと",
            "record_date": "2026-01-01",
            "qualifications": [],
        },
        headers={"X-CSRF-Token": "invalid-token"},
    )

    assert response.status_code == 403


def test_post_with_valid_csrf_token_succeeds(client) -> None:
    """正しい CSRF トークンの POST リクエストが成功することを確認する。"""
    headers = auth_header(client, "csrftest3")

    response = client.post(
        "/api/basic-info",
        json={
            "full_name": "テスト",
            "name_furigana": "てすと",
            "record_date": "2026-01-01",
            "qualifications": [],
        },
        headers=headers,
    )

    assert response.status_code == 201


def test_get_request_skips_csrf_check(client) -> None:
    """GET リクエストは CSRF チェックをスキップすることを確認する。"""
    auth_header(client, "csrftest4")

    response = client.get("/auth/me")

    assert response.status_code == 200


def test_login_sets_csrf_cookie(client) -> None:
    """ログイン成功時に csrf_token Cookie がセットされることを確認する。"""
    client.post(
        "/auth/register",
        json={
            "username": "csrflogin",
            "email": "csrflogin@example.com",
            "password": "SecurePass123",
        },
    )

    response = client.post(
        "/auth/login",
        json={"email": "csrflogin@example.com", "password": "SecurePass123"},
    )

    assert response.status_code == 200
    assert "csrf_token=" in response.headers.get("set-cookie", "")


# ── ブルートフォース対策 ───────────────────────────────────────────


def test_login_rate_limit_after_5_failures(client) -> None:
    """5回失敗後の6回目が 429 で拒否されることを確認する。"""
    client.post(
        "/auth/register",
        json={"username": "bfuser", "email": "bfuser@example.com", "password": "SecurePass123"},
    )

    for _ in range(5):
        client.post(
            "/auth/login",
            json={"email": "bfuser@example.com", "password": "WrongPass!"},
        )

    response = client.post(
        "/auth/login",
        json={"email": "bfuser@example.com", "password": "WrongPass!"},
    )

    assert response.status_code == 429


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

    assert response.status_code == 303
    assert mock_async_client.call_count == 0
    parsed = urlparse(response.headers["location"])
    assert parsed.scheme == "http"
    assert parsed.netloc == "localhost:5173"
    assert parsed.path == "/index.html"
    assert parse_qs(parsed.query)["github_error"] == ["OAuth state の検証に失敗しました。"]


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

    assert response.status_code == 303
    assert response.headers["location"] == "http://localhost:5173/index.html"
    assert "access_token=" in response.headers["set-cookie"]


# ── ログアウト ────────────────────────────────────────────────────


def test_logout_clears_cookies(client) -> None:
    """ログアウト時に認証 Cookie がすべて削除されることを確認する。"""
    auth_header(client, "logoutuser")

    response = client.post("/auth/logout")

    assert response.status_code == 204
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie

    # ログアウト後に /auth/me にアクセスすると 401 になる
    response = client.get("/auth/me")
    assert response.status_code == 401


# 使用しない環境変数を参照するだけのプレースホルダー（lint 対策）
_ = os.environ
