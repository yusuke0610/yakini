import secrets

from fastapi import Header, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..messages import get_error
from ..settings import get_admin_token

# 既定の IP 単位レート制限。1 IP から 1 万リクエスト級の攻撃が来た場合、
# 5 秒で 429 を返すよう 300/min を上限に設定する。個別エンドポイントは
# @limiter.limit デコレータでさらに厳しい値に上書きできる。
limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])


def verify_admin_token(
    authorization: str | None = Header(default=None),
) -> None:
    configured_token = get_admin_token()
    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=get_error("server.admin_token_not_configured"),
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error("server.bearer_token_missing"),
        )

    provided_token = authorization.removeprefix("Bearer ").strip()
    if not secrets.compare_digest(provided_token, configured_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_error("auth.forbidden"),
        )
