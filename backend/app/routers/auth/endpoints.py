"""
認証エンドポイント定義。

各関数は薄いラッパーとして実装し、ロジックはサブモジュールに委譲する。
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ...core.errors import ErrorCode, raise_app_error
from ...core.messages import get_error
from ...core.security.auth import (
    _REFRESH_COOKIE_NAME,
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
    build_frontend_redirect_url,
    resolve_frontend_url_from_cookie,
    resolve_frontend_url_from_request,
    validate_github_oauth_state,
)
from .token_manager import (
    clear_github_oauth_cookies,
    set_auth_cookies,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/refresh", response_model=TokenResponse)
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
    username = verify_refresh_token(token)

    user = UserRepository(db).get_by_username(username)
    if not user:
        raise_app_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCode.AUTH_REQUIRED,
            message=get_error("auth.user_not_found"),
            action="ログインし直してください",
        )

    set_auth_cookies(response, user.username)
    return TokenResponse(
        username=user.username,
        is_github_user=user.username.startswith("github:"),
    )


@router.get("/me", response_model=TokenResponse)
def me(current_user=Depends(get_current_user)) -> TokenResponse:
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
) -> RedirectResponse:
    """GitHub OAuth コールバックを処理し、フロントエンドへリダイレクトする。"""
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
        token_response = await authenticate_github_user(db, code)
    except HTTPException as error:
        # error.detail は AppErrorResponse の dict 形式なので message フィールドを取り出す
        detail = error.detail
        error_message = detail.get("message") if isinstance(detail, dict) else str(detail)
        redirect = RedirectResponse(
            url=build_frontend_redirect_url(frontend_url, error_message),
            status_code=status.HTTP_303_SEE_OTHER,
        )
        clear_github_oauth_cookies(redirect)
        return redirect

    redirect = RedirectResponse(
        url=build_frontend_redirect_url(frontend_url),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    set_auth_cookies(redirect, token_response.username)
    clear_github_oauth_cookies(redirect)
    return redirect


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
    token_response = await authenticate_github_user(db, payload.code)
    set_auth_cookies(response, token_response.username)
    clear_github_oauth_cookies(response)
    return token_response
