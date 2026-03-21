import pytest
from jose import jwt
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

from conftest import auth_header
from app.auth import create_access_token, hash_password, verify_password
from app.settings import get_cookie_samesite, get_cookie_secure


def test_hash_and_verify_password() -> None:
    hashed = hash_password("secret123")

    assert verify_password("secret123", hashed)


def test_verify_wrong_password() -> None:
    hashed = hash_password("secret123")

    assert not verify_password("wrong", hashed)


def test_create_access_token_contains_username(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SECRET_KEY", "testsecret")

    token = create_access_token("alice")
    payload = jwt.decode(token, "testsecret", algorithms=["HS256"])

    assert payload["sub"] == "alice"


def test_create_access_token_has_expiry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SECRET_KEY", "testsecret")

    token = create_access_token("alice")
    payload = jwt.decode(token, "testsecret", algorithms=["HS256"])

    assert "exp" in payload


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


def test_me_returns_current_user(client) -> None:
    auth_header(client, "alice")

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "username": "alice",
        "is_github_user": False,
    }


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
    assert parse_qs(parsed.query)["github_error"] == ["OAuth state の検証に失敗しました"]


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
