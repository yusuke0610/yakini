import logging

from fastapi import (
    APIRouter, Depends, HTTPException, Request, Response, status
)
from sqlalchemy.orm import Session

from ..auth import (
    create_access_token, verify_password, hash_password,
    _COOKIE_NAME, _COOKIE_MAX_AGE
)
from ..database import get_db
from ..dependencies import limiter
from ..logging_utils import log_event
from ..repositories import UserRepository
from ..schemas import (
    GitHubCallbackRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from ..encryption import encrypt_field
from ..settings import (
    get_cors_origins, get_github_client_id, get_github_client_secret
)


def _set_auth_cookie(response: Response, token: str) -> None:
    """認証トークンを HttpOnly Cookie にセットする。"""
    origins = get_cors_origins()
    is_https = (
        all(o.startswith("https://") for o in origins)
        if origins else False
    )
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_https,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        path="/",
    )


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")
def register(
    request: Request,
    response: Response,
    payload: RegisterRequest,
    db: Session = Depends(get_db)
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
        payload.username, hash_password(payload.password), email=payload.email
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
    db: Session = Depends(get_db)
) -> TokenResponse:
    user = UserRepository(db).get_by_email(payload.email)
    if not user or not verify_password(
        payload.password, user.hashed_password
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


@router.post("/github/callback", response_model=TokenResponse)
@limiter.limit("5/minute")
async def github_callback(
    request: Request, response: Response, payload: GitHubCallbackRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
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
                "code": payload.code,
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
            username=f"github:{github_login}", github_id=github_id
        )
        log_event(logging.INFO, "github_user_created", username=user.username)

    user.github_token = encrypt_field(access_token)
    db.commit()

    token = create_access_token(user.username)
    _set_auth_cookie(response, token)
    return TokenResponse(username=user.username, is_github_user=True)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    """認証 Cookie を削除してログアウトする。"""
    response.delete_cookie(key=_COOKIE_NAME, path="/")
