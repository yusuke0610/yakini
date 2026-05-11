"""
Cookie設定・削除・JWT生成・トークン検証を担うモジュール。
"""

import json
import secrets

from fastapi import Request, Response
from sqlalchemy.orm import Session

from ...core.security.auth import (
    _REFRESH_COOKIE_MAX_AGE,
    create_access_token,
    create_refresh_token,
)
from ...core.security.csrf import CSRF_COOKIE_NAME, set_csrf_cookie
from ...core.settings import get_cookie_samesite, get_cookie_secure
from ...repositories import UserRepository

# GitHub OAuth 用 Cookie 名
GITHUB_OAUTH_STATE_COOKIE = "github_oauth_state"
GITHUB_OAUTH_REDIRECT_COOKIE = "github_oauth_redirect"
# state と redirect_url を JSON で1つの Cookie にまとめて格納する
GITHUB_OAUTH_SESSION_COOKIE = "session"
GITHUB_OAUTH_COOKIE_MAX_AGE = 10 * 60


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


def clear_github_oauth_cookies(response: Response) -> None:
    """GitHub OAuth フロー用 Cookie をすべて削除する。"""
    delete_cookie(response, GITHUB_OAUTH_STATE_COOKIE)
    delete_cookie(response, GITHUB_OAUTH_REDIRECT_COOKIE)


def set_github_oauth_session(
    response: Response, state: str, redirect_url: str
) -> None:
    """GitHub OAuth 用の state と redirect_url を session cookie に格納する。

    state と redirect_url を JSON で1つの Cookie にまとめる。
    """
    payload = json.dumps({"state": state, "redirect": redirect_url})
    set_cookie(response, GITHUB_OAUTH_SESSION_COOKIE, payload, GITHUB_OAUTH_COOKIE_MAX_AGE)


def get_github_oauth_session(request: Request) -> tuple[str | None, str | None]:
    """session cookie から (state, redirect_url) を取り出す。

    取得できない場合は (None, None) を返す。
    """
    raw = request.cookies.get(GITHUB_OAUTH_SESSION_COOKIE)
    if not raw:
        return None, None
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None, None
    if not isinstance(data, dict):
        return None, None
    return data.get("state"), data.get("redirect")


def clear_github_oauth_session(response: Response) -> None:
    """session cookie を削除する。"""
    delete_cookie(response, GITHUB_OAUTH_SESSION_COOKIE)


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
