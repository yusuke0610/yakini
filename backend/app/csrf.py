"""CSRF 対策モジュール（ダブルサブミット Cookie パターン）。"""
import secrets

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .messages import get_error
from .settings import get_cookie_secure

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"

# CSRF トークンの有効期間（リフレッシュトークンに合わせて 7 日）
CSRF_COOKIE_MAX_AGE = 7 * 24 * 60 * 60

# CSRF チェックをスキップするパス（認証確立・OAuth・ヘルスチェック）
_CSRF_SKIP_PATHS = {
    "/auth/login",
    "/auth/register",
    "/auth/logout",
    "/auth/refresh",
    "/auth/github/callback",
    "/auth/github/login",
    "/auth/github/login-url",
    "/health",
}

# CSRF チェックをスキップするメソッド
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def set_csrf_cookie(response: Response, token: str) -> None:
    """CSRF トークンを httpOnly=False Cookie にセットする（JS から読み取り可能）。"""
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        secure=get_cookie_secure(),
        samesite="strict",
        max_age=CSRF_COOKIE_MAX_AGE,
        path="/",
    )


def _generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


class CSRFMiddleware(BaseHTTPMiddleware):
    """POST/PUT/DELETE/PATCH で CSRF トークンを検証するミドルウェア。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in _SAFE_METHODS:
            return await call_next(request)

        path = request.url.path
        if path in _CSRF_SKIP_PATHS:
            return await call_next(request)

        # セッション Cookie がない場合は CSRF チェック不要（Bearer 認証など）
        if not request.cookies.get("access_token"):
            return await call_next(request)

        cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
        header_token = request.headers.get(CSRF_HEADER_NAME, "")

        if not cookie_token or not header_token:
            return JSONResponse(
                status_code=403,
                content={"detail": get_error("auth.csrf_token_missing")},
            )

        if not secrets.compare_digest(cookie_token, header_token):
            return JSONResponse(
                status_code=403,
                content={"detail": get_error("auth.csrf_token_invalid")},
            )

        return await call_next(request)
