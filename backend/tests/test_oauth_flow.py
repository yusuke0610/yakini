"""OAuth フロー（state 生成・検証・frontend URL 解決）のユニットテスト。"""

from unittest.mock import patch

import pytest
from app.routers.auth.oauth_flow import (
    normalize_frontend_url,
    resolve_frontend_url_from_cookie,
    validate_github_oauth_state,
)
from fastapi import HTTPException

# ── state 検証テスト ─────────────────────────────────────────────────────


def test_validate_state_success() -> None:
    """state が一致する場合は例外が発生しないこと。"""
    validate_github_oauth_state("abc123", "abc123")


def test_validate_state_mismatch_raises_401() -> None:
    """state が不一致の場合は HTTP 401 が発生すること。"""
    with pytest.raises(HTTPException) as exc_info:
        validate_github_oauth_state("abc123", "xyz789")
    assert exc_info.value.status_code == 401


def test_validate_state_missing_stored_raises_401() -> None:
    """stored_state が None の場合は HTTP 401 が発生すること。"""
    with pytest.raises(HTTPException) as exc_info:
        validate_github_oauth_state(None, "abc123")
    assert exc_info.value.status_code == 401


def test_validate_state_missing_provided_raises_401() -> None:
    """provided_state が None の場合は HTTP 401 が発生すること。"""
    with pytest.raises(HTTPException) as exc_info:
        validate_github_oauth_state("abc123", None)
    assert exc_info.value.status_code == 401


# ── malformed redirect_uri テスト ───────────────────────────────────────


def test_normalize_frontend_url_invalid_scheme_raises_400() -> None:
    """http/https 以外のスキームでは HTTP 400 が発生すること。"""
    with patch(
        "app.routers.auth.oauth_flow.get_cors_origins",
        return_value=["https://example.com"],
    ):
        with pytest.raises(HTTPException) as exc_info:
            normalize_frontend_url("ftp://example.com/path")
        assert exc_info.value.status_code == 400


def test_normalize_frontend_url_no_netloc_raises_400() -> None:
    """netloc が空の場合は HTTP 400 が発生すること。"""
    with patch(
        "app.routers.auth.oauth_flow.get_cors_origins",
        return_value=["https://example.com"],
    ):
        with pytest.raises(HTTPException) as exc_info:
            normalize_frontend_url("https://")
        assert exc_info.value.status_code == 400


# ── frontend URL 許可リスト外テスト ─────────────────────────────────────


def test_normalize_frontend_url_not_in_cors_origins_raises_400() -> None:
    """CORS_ORIGINS に含まれないオリジンでは HTTP 400 が発生すること。"""
    with patch(
        "app.routers.auth.oauth_flow.get_cors_origins",
        return_value=["https://allowed.example.com"],
    ):
        with pytest.raises(HTTPException) as exc_info:
            normalize_frontend_url("https://evil.example.com/page")
        assert exc_info.value.status_code == 400


def test_normalize_frontend_url_allowed_origin_succeeds() -> None:
    """CORS_ORIGINS に含まれるオリジンは正常に正規化されること。"""
    with patch(
        "app.routers.auth.oauth_flow.get_cors_origins",
        return_value=["https://allowed.example.com"],
    ):
        result = normalize_frontend_url("https://allowed.example.com/dashboard")
    assert result == "https://allowed.example.com/dashboard"


# ── cookie からの URL 解決テスト ────────────────────────────────────────


def test_resolve_frontend_url_from_cookie_valid() -> None:
    """有効な Cookie URL が正規化されて返ること。"""
    with patch(
        "app.routers.auth.oauth_flow.get_cors_origins",
        return_value=["https://example.com"],
    ):
        result = resolve_frontend_url_from_cookie("https://example.com/")
    assert result == "https://example.com/"


def test_resolve_frontend_url_from_cookie_none_returns_default() -> None:
    """Cookie が None の場合はデフォルト URL が返ること。"""
    with patch(
        "app.routers.auth.oauth_flow.get_cors_origins",
        return_value=["https://default.example.com"],
    ):
        result = resolve_frontend_url_from_cookie(None)
    assert result == "https://default.example.com/"


def test_resolve_frontend_url_from_cookie_invalid_returns_default() -> None:
    """Cookie に不正な URL がある場合はデフォルト URL が返ること。"""
    with patch(
        "app.routers.auth.oauth_flow.get_cors_origins",
        return_value=["https://default.example.com"],
    ):
        result = resolve_frontend_url_from_cookie("ftp://bad-url.com")
    assert result == "https://default.example.com/"
