"""
認証エンドポイント定義。

各関数は薄いラッパーとして実装し、ロジックはサブモジュールに委譲する。
"""

import json as _json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ...core.errors import ErrorCode, raise_app_error
from ...core.messages import get_error
from ...core.security.auth import (
    _REFRESH_COOKIE_NAME,
    _decode_token,
    get_current_user,
    verify_refresh_token,
)
from ...core.security.dependencies import limiter
from ...db import get_db
from ...repositories import UserRepository
from ...schemas import GitHubCallbackRequest, TokenResponse
from .github_auth import authenticate_github_user
from .oauth_flow import (
    GITHUB_OAUTH_REDIRECT_COOKIE,
    GITHUB_OAUTH_STATE_COOKIE,
    begin_github_oauth,
    build_external_base_url,
    build_frontend_redirect_url,
    resolve_frontend_url_from_cookie,
    resolve_frontend_url_from_request,
    validate_github_oauth_state,
)
from .token_manager import (
    clear_auth_cookies,
    clear_github_oauth_cookies,
    set_auth_cookies,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _html_redirect(url: str) -> str:
    """Firebase Hosting proxy 経由でも Set-Cookie が失われないよう 200 + HTML リダイレクトを返す。

    303 レスポンスの Set-Cookie は Firebase Hosting CDN 層で除去されるため、
    200 の HTML で meta refresh + JS リダイレクトを使う。
    """
    js_url = _json.dumps(url)
    safe_url = url.replace('"', "&quot;")
    return (
        "<!DOCTYPE html><html><head>"
        f'<meta http-equiv="refresh" content="0;url={safe_url}">'
        "</head><body>"
        f"<script>window.location.replace({js_url});</script>"
        "</body></html>"
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """リフレッシュトークンで新しいアクセストークンを発行する。"""
    token = request.cookies.get(_REFRESH_COOKIE_NAME)
    if not token:
        raise_app_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.AUTH_REQUIRED,
            message=get_error("auth.login_required"),
            action="ログインし直してください",
        )
    username, jti = verify_refresh_token(token)

    user = UserRepository(db).get_by_username(username)
    if not user:
        raise_app_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.AUTH_REQUIRED,
            message=get_error("auth.user_not_found"),
            action="ログインし直してください",
        )

    # DB の refresh_jti と一致しない場合は失効済みとして拒否する
    if user.refresh_jti != jti:
        raise_app_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.AUTH_EXPIRED,
            message=get_error("auth.invalid_token"),
            action="ログインし直してください",
        )

    set_auth_cookies(response, user.username, db)
    return TokenResponse(
        username=user.username,
        is_github_user=user.username.startswith("github:"),
    )


@router.post("/logout", status_code=204)
@limiter.limit("20/minute")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> None:
    """ログアウト処理。DB の refresh_jti を無効化し Cookie を削除する。
    トークン解析が失敗した場合でも必ず Cookie を削除して 204 を返す。
    """
    token = request.cookies.get(_REFRESH_COOKIE_NAME)
    if token:
        try:
            payload = _decode_token(token)
            username: str | None = payload.get("sub")
            if username:
                user = UserRepository(db).get_by_username(username)
                if user:
                    UserRepository(db).update_refresh_jti(user, None)
        except HTTPException:
            logger.debug("ログアウト時のトークン解析に失敗（Cookie 削除を継続）", exc_info=True)
    clear_auth_cookies(response)


@router.get("/me", response_model=TokenResponse)
@limiter.limit("60/minute")
def me(request: Request, current_user=Depends(get_current_user)) -> TokenResponse:
    """現在のログインユーザー情報を返す。"""
    return TokenResponse(
        username=current_user.username,
        is_github_user=current_user.username.startswith("github:"),
    )


@router.get("/github/login-url")
@limiter.limit("10/minute")
def github_login_url(
    request: Request,
    response: Response,
    return_to: str | None = None,
) -> dict[str, str]:
    """GitHub OAuth 認可 URL を返す。"""
    frontend_url = resolve_frontend_url_from_request(request, return_to)
    authorization_url = begin_github_oauth(request, response, frontend_url)
    return {"authorization_url": authorization_url}


@router.get("/github/login")
@limiter.limit("10/minute")
def github_login(
    request: Request,
    return_to: str | None = None,
) -> RedirectResponse:
    """GitHub OAuth 認可 URL へリダイレクトする。"""
    frontend_url = resolve_frontend_url_from_request(request, return_to)
    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    redirect_url = begin_github_oauth(request, redirect, frontend_url)
    redirect.headers["location"] = redirect_url
    return redirect


@router.get("/github/callback")
@limiter.limit("10/minute")
async def github_callback_redirect(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """GitHub OAuth コールバックを処理し、フロントエンドへリダイレクトする。

    Firebase Hosting rewrite 経由では 303 の Set-Cookie が転送されないため
    200 + HTML リダイレクトで Cookie を確実にセットする。
    """
    frontend_url = resolve_frontend_url_from_cookie(
        request.cookies.get(GITHUB_OAUTH_REDIRECT_COOKIE)
    )

    try:
        if not code:
            raise_app_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code=ErrorCode.AUTH_EXPIRED,
                message=get_error("auth.github_code_missing"),
                action="GitHub ログインをやり直してください",
            )
        validate_github_oauth_state(
            request.cookies.get(GITHUB_OAUTH_STATE_COOKIE),
            state,
        )
        redirect_uri = f"{build_external_base_url(request)}/auth/github/callback"
        token_response = await authenticate_github_user(db, code, redirect_uri)
    except HTTPException as error:
        # error.detail は AppErrorResponse の dict 形式なので message フィールドを取り出す
        detail = error.detail
        error_message = detail.get("message") if isinstance(detail, dict) else str(detail)
        response = HTMLResponse(
            content=_html_redirect(build_frontend_redirect_url(frontend_url, error_message))
        )
        clear_github_oauth_cookies(response)
        return response

    response = HTMLResponse(content=_html_redirect(build_frontend_redirect_url(frontend_url)))
    set_auth_cookies(response, token_response.username, db)
    clear_github_oauth_cookies(response)
    return response


@router.post("/github/callback", response_model=TokenResponse)
@limiter.limit("5/minute")
async def github_callback(
    request: Request,
    response: Response,
    payload: GitHubCallbackRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """GitHub OAuth コードを受け取り、認証 Cookie を発行する。"""
    validate_github_oauth_state(
        request.cookies.get(GITHUB_OAUTH_STATE_COOKIE),
        payload.state,
    )
    redirect_uri = f"{build_external_base_url(request)}/auth/github/callback"
    token_response = await authenticate_github_user(db, payload.code, redirect_uri)
    set_auth_cookies(response, token_response.username, db)
    clear_github_oauth_cookies(response)
    return token_response
