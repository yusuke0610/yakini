import logging
import secrets
from urllib.parse import quote, urlencode

from fastapi import (
    APIRouter, Depends, HTTPException, Request, Response, status,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import (
    _COOKIE_MAX_AGE,
    _COOKIE_NAME,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..database import get_db
from ..dependencies import limiter
from ..encryption import encrypt_field
from ..logging_utils import log_event
from ..repositories import UserRepository
from ..schemas import (
    GitHubCallbackRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from ..settings import (
    get_cookie_samesite,
    get_cookie_secure,
    get_cors_origins,
    get_github_client_id,
    get_github_client_secret,
)

_GITHUB_OAUTH_STATE_COOKIE = "github_oauth_state"
_GITHUB_OAUTH_REDIRECT_COOKIE = "github_oauth_redirect"
_GITHUB_OAUTH_COOKIE_MAX_AGE = 10 * 60


def _set_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=get_cookie_secure(),
        samesite=get_cookie_samesite(),
        max_age=max_age,
        path="/",
    )


def _delete_cookie(response: Response, key: str) -> None:
    response.delete_cookie(key=key, path="/")


def _clear_github_oauth_cookies(response: Response) -> None:
    _delete_cookie(response, _GITHUB_OAUTH_STATE_COOKIE)
    _delete_cookie(response, _GITHUB_OAUTH_REDIRECT_COOKIE)


def _set_auth_cookie(response: Response, token: str) -> None:
    """認証トークンを HttpOnly Cookie にセットする。"""
    _set_cookie(response, _COOKIE_NAME, token, _COOKIE_MAX_AGE)


def _get_default_frontend_origin() -> str:
    origins = get_cors_origins()
    if not origins:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CORS_ORIGINS が設定されていません",
        )
    return origins[0]


def _resolve_frontend_origin_from_request(request: Request) -> str:
    request_origin = request.headers.get("origin")
    allowed_origins = get_cors_origins()

    if request_origin:
        if request_origin not in allowed_origins:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="許可されていないフロントエンドオリジンです",
            )
        return request_origin
    return _get_default_frontend_origin()


def _resolve_frontend_origin_from_cookie(stored_origin: str | None) -> str:
    allowed_origins = get_cors_origins()
    if stored_origin and stored_origin in allowed_origins:
        return stored_origin
    return _get_default_frontend_origin()


def _build_frontend_redirect_url(
    frontend_origin: str,
    error: str | None = None,
) -> str:
    base_url = f"{frontend_origin.rstrip('/')}/"
    if not error:
        return base_url
    return f"{base_url}?github_error={quote(error)}"


def _validate_github_oauth_state(
    stored_state: str | None,
    provided_state: str | None,
) -> None:
    if not stored_state or not provided_state:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OAuth state の検証に失敗しました",
        )
    if not secrets.compare_digest(stored_state, provided_state):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OAuth state の検証に失敗しました",
        )


def _build_github_authorization_url(
    client_id: str,
    redirect_uri: str,
    state: str,
) -> str:
    query = urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:user",
        "state": state,
    })
    return f"https://github.com/login/oauth/authorize?{query}"


async def _authenticate_github_user(db: Session, code: str) -> TokenResponse:
    client_id = get_github_client_id()
    client_secret = get_github_client_secret()
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth が設定されていません",
        )

    import httpx

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            log_event(
                logging.WARNING,
                "github_oauth_failed",
                error=token_data.get("error_description", "unknown"),
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub認証に失敗しました",
            )

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        github_user = user_resp.json()

    github_id = github_user.get("id")
    github_login = github_user.get("login")
    if not github_id or not github_login:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHubユーザー情報の取得に失敗しました",
        )

    repo = UserRepository(db)
    user = repo.get_by_github_id(github_id)
    if not user:
        user = repo.create_github_user(
            username=f"github:{github_login}",
            github_id=github_id,
        )
        log_event(logging.INFO, "github_user_created", username=user.username)

    user.github_token = encrypt_field(access_token)
    db.commit()

    return TokenResponse(username=user.username, is_github_user=True)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")
def register(
    request: Request,
    response: Response,
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    repo = UserRepository(db)
    if repo.get_by_username(payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="このユーザー名は既に使用されています",
        )
    if repo.get_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="このメールアドレスは既に使用されています",
        )
    user = repo.create(
        payload.username,
        hash_password(payload.password),
        email=payload.email,
    )
    token = create_access_token(user.username)
    _set_auth_cookie(response, token)
    return TokenResponse(username=user.username)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = UserRepository(db).get_by_email(payload.email)
    if not user or not verify_password(
        payload.password,
        user.hashed_password,
    ):
        log_event(
            logging.WARNING,
            "login_failed",
            email=payload.email,
            reason="invalid email or password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )
    token = create_access_token(user.username)
    _set_auth_cookie(response, token)
    return TokenResponse(username=user.username)


@router.get("/me", response_model=TokenResponse)
def me(current_user=Depends(get_current_user)) -> TokenResponse:
    return TokenResponse(
        username=current_user.username,
        is_github_user=current_user.username.startswith("github:"),
    )


@router.get("/github/login-url")
@limiter.limit("10/minute")
def github_login_url(
    request: Request,
    response: Response,
) -> dict[str, str]:
    client_id = get_github_client_id()
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth が設定されていません",
        )

    frontend_origin = _resolve_frontend_origin_from_request(request)
    redirect_uri = f"{str(request.base_url).rstrip('/')}/auth/github/callback"
    state = secrets.token_urlsafe(32)

    _set_cookie(
        response,
        _GITHUB_OAUTH_STATE_COOKIE,
        state,
        _GITHUB_OAUTH_COOKIE_MAX_AGE,
    )
    _set_cookie(
        response,
        _GITHUB_OAUTH_REDIRECT_COOKIE,
        frontend_origin,
        _GITHUB_OAUTH_COOKIE_MAX_AGE,
    )

    return {
        "authorization_url": _build_github_authorization_url(
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
        )
    }


@router.get("/github/callback")
@limiter.limit("10/minute")
async def github_callback_redirect(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    frontend_origin = _resolve_frontend_origin_from_cookie(
        request.cookies.get(_GITHUB_OAUTH_REDIRECT_COOKIE)
    )

    try:
        if not code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub認証コードが取得できませんでした",
            )
        _validate_github_oauth_state(
            request.cookies.get(_GITHUB_OAUTH_STATE_COOKIE),
            state,
        )
        token_response = await _authenticate_github_user(db, code)
    except HTTPException as error:
        redirect = RedirectResponse(
            url=_build_frontend_redirect_url(frontend_origin, error.detail),
            status_code=status.HTTP_303_SEE_OTHER,
        )
        _clear_github_oauth_cookies(redirect)
        return redirect

    redirect = RedirectResponse(
        url=_build_frontend_redirect_url(frontend_origin),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    _set_auth_cookie(
        redirect,
        create_access_token(token_response.username),
    )
    _clear_github_oauth_cookies(redirect)
    return redirect


@router.post("/github/callback", response_model=TokenResponse)
@limiter.limit("5/minute")
async def github_callback(
    request: Request,
    response: Response,
    payload: GitHubCallbackRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    _validate_github_oauth_state(
        request.cookies.get(_GITHUB_OAUTH_STATE_COOKIE),
        payload.state,
    )
    token_response = await _authenticate_github_user(db, payload.code)
    _set_auth_cookie(
        response,
        create_access_token(token_response.username),
    )
    _clear_github_oauth_cookies(response)
    return token_response


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    """認証 Cookie を削除してログアウトする。"""
    _delete_cookie(response, _COOKIE_NAME)
    _clear_github_oauth_cookies(response)
