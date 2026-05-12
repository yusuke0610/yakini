"""
Cookie設定・削除・JWT生成・トークン検証を担うモジュール。
"""

import json
import secrets

from fastapi import Response
from sqlalchemy.orm import Session

from ...core.security.auth import (
    _REFRESH_COOKIE_MAX_AGE,
    create_access_token,
    create_refresh_token,
)
from ...core.security.csrf import CSRF_COOKIE_NAME, set_csrf_cookie
from ...core.settings import get_cookie_samesite, get_cookie_secure
from ...repositories import UserRepository

# 認証セッション Cookie 名（state と redirect_url はフロントの sessionStorage で管理する）
GITHUB_OAUTH_SESSION_COOKIE = "session"


def set_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    """指定したキーと値で HttpOnly Cookie を設定する。"""
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=get_cookie_secure(),
        samesite=get_cookie_samesite(),
        max_age=max_age,
        path="/",
    )


def delete_cookie(response: Response, key: str, path: str = "/") -> None:
    """指定したキーの Cookie を削除する。"""
    response.delete_cookie(key=key, path=path)



def set_auth_cookies(response: Response, username: str, db: Session) -> None:
    """アクセストークン・リフレッシュトークン・CSRF トークンを Cookie にセットし、refresh_jti を DB に保存する。"""
    access_token = create_access_token(username)
    refresh_token, jti = create_refresh_token(username)
    csrf_token = secrets.token_urlsafe(32)

    # 旧 Cookie の残留削除（移行期の互換）
    delete_cookie(response, "access_token")
    delete_cookie(response, "refresh_token")

    # アクセストークン・リフレッシュトークンを JSON で1つの session Cookie にまとめる（7日）
    session_payload = json.dumps({"access_token": access_token, "refresh_token": refresh_token})
    set_cookie(response, GITHUB_OAUTH_SESSION_COOKIE, session_payload, _REFRESH_COOKIE_MAX_AGE)

    # CSRF トークン（httpOnly=False: JS から読み取れる）
    set_csrf_cookie(response, csrf_token)

    # refresh_jti を DB に保存
    user = UserRepository(db).get_by_username(username)
    if user:
        UserRepository(db).update_refresh_jti(user, jti)


def clear_auth_cookies(response: Response) -> None:
    """認証関連の Cookie をすべて削除する。"""
    delete_cookie(response, GITHUB_OAUTH_SESSION_COOKIE, path="/")
    # 旧 Cookie の削除（移行期の互換）
    delete_cookie(response, "access_token", path="/")
    delete_cookie(response, "refresh_token", path="/auth/")
    delete_cookie(response, "refresh_token", path="/auth/refresh")
    delete_cookie(response, CSRF_COOKIE_NAME, path="/")
