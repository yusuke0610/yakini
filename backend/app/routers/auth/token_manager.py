"""
Cookie設定・削除・JWT生成・トークン検証を担うモジュール。
"""

import json
import secrets

from fastapi import Request, Response
from sqlalchemy.orm import Session

from ...core.security.auth import (
    _COOKIE_MAX_AGE,
    _COOKIE_NAME,
    _REFRESH_COOKIE_MAX_AGE,
    _REFRESH_COOKIE_NAME,
    create_access_token,
    create_refresh_token,
)
from ...core.security.csrf import CSRF_COOKIE_NAME, set_csrf_cookie
from ...core.settings import get_cookie_samesite, get_cookie_secure
from ...repositories import UserRepository

# GitHub OAuth 用 Cookie 名
GITHUB_OAUTH_STATE_COOKIE = "github_oauth_state"
GITHUB_OAUTH_REDIRECT_COOKIE = "github_oauth_redirect"
# Firebase Hosting は __session という名前の Cookie のみ Cloud Run に転送するため、
# state と redirect_url を JSON で1つの Cookie にまとめて格納する
GITHUB_OAUTH_SESSION_COOKIE = "__session"
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
    """GitHub OAuth 用の state と redirect_url を __session cookie に格納する。

    Firebase Hosting は __session という名前の Cookie のみ Cloud Run に転送するため、
    state と redirect_url を JSON で1つの Cookie にまとめる。
    """
    payload = json.dumps({"state": state, "redirect": redirect_url})
    set_cookie(response, GITHUB_OAUTH_SESSION_COOKIE, payload, GITHUB_OAUTH_COOKIE_MAX_AGE)


def get_github_oauth_session(request: Request) -> tuple[str | None, str | None]:
    """__session cookie から (state, redirect_url) を取り出す。

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
    """__session cookie を削除する。"""
    delete_cookie(response, GITHUB_OAUTH_SESSION_COOKIE)


def set_auth_cookies(response: Response, username: str, db: Session) -> None:
    """アクセストークン・リフレッシュトークン・CSRF トークンを Cookie にセットし、refresh_jti を DB に保存する。"""
    access_token = create_access_token(username)
    refresh_token, jti = create_refresh_token(username)
    csrf_token = secrets.token_urlsafe(32)

    # アクセストークン（15分, path="/"）
    set_cookie(response, _COOKIE_NAME, access_token, _COOKIE_MAX_AGE)

    # リフレッシュトークン（7日, path="/auth/" に限定: /auth/refresh と /auth/logout の両方で読み取れるようにする）
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=get_cookie_secure(),
        samesite=get_cookie_samesite(),
        max_age=_REFRESH_COOKIE_MAX_AGE,
        path="/auth/",
    )

    # CSRF トークン（httpOnly=False: JS から読み取れる）
    set_csrf_cookie(response, csrf_token)

    # refresh_jti を DB に保存
    user = UserRepository(db).get_by_username(username)
    if user:
        UserRepository(db).update_refresh_jti(user, jti)


def clear_auth_cookies(response: Response) -> None:
    """認証関連の Cookie をすべて削除する。"""
    delete_cookie(response, _COOKIE_NAME, path="/")
    # path="/auth/" と旧 path="/auth/refresh" の両方を削除して移行期の互換を保つ
    delete_cookie(response, _REFRESH_COOKIE_NAME, path="/auth/")
    delete_cookie(response, _REFRESH_COOKIE_NAME, path="/auth/refresh")
    delete_cookie(response, CSRF_COOKIE_NAME, path="/")
