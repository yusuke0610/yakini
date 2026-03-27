from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import User
from ..messages import get_error
from ..settings import get_jwt_private_key, get_jwt_public_key

# アクセストークン Cookie 名（後方互換性のため公開）
_COOKIE_NAME = "access_token"
_REFRESH_COOKIE_NAME = "refresh_token"

# アクセストークン: 15分
_ACCESS_TOKEN_EXPIRE_MINUTES = 15
_COOKIE_MAX_AGE = _ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 900秒

# リフレッシュトークン: 7日
_REFRESH_TOKEN_EXPIRE_DAYS = 7
_REFRESH_COOKIE_MAX_AGE = _REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 604800秒

_ALGORITHM = "RS256"

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(username: str) -> str:
    """短命のアクセストークン（15分）を生成する。"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "type": "access", "exp": expire}
    return jwt.encode(payload, get_jwt_private_key(), algorithm=_ALGORITHM)


def create_refresh_token(username: str) -> str:
    """長命のリフレッシュトークン（7日）を生成する。"""
    expire = datetime.now(timezone.utc) + timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": username, "type": "refresh", "exp": expire}
    return jwt.encode(payload, get_jwt_private_key(), algorithm=_ALGORITHM)


def _decode_token(token: str) -> dict:
    """JWT をデコードしてペイロードを返す。失敗時は 401 を送出する。"""
    try:
        return jwt.decode(token, get_jwt_public_key(), algorithms=[_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error("auth.invalid_token"),
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_refresh_token(token: str) -> str:
    """リフレッシュトークンを検証し、username を返す。type 不一致時は 401 を送出する。"""
    payload = _decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error("auth.invalid_token"),
        )
    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error("auth.invalid_token"),
        )
    return username


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get(_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error("auth.login_required"),
        )
    payload = _decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error("auth.invalid_token"),
        )
    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error("auth.invalid_token"),
        )

    from ...repositories import UserRepository

    user = UserRepository(db).get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error("auth.user_not_found"),
        )
    return user
