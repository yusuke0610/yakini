"""リクエスト ID ミドルウェア。

受信リクエストごとに一意の X-Request-ID を付与し、ContextVar に格納する。
すべてのログは CloudLoggingFormatter が ContextVar から request_id を自動注入するため、
各モジュールで明示的に extra={"request_id": ...} を書く必要はない。

不正アクセス追跡のため、client_ip / path / method も ContextVar に格納し、
ログから攻撃元 IP・対象パスを後追いできるようにする。

処理フロー:
  1. X-Request-ID リクエストヘッダーが存在すれば使用、なければ UUID4 を生成
  2. request_id_var / client_ip_var / request_path_var / request_method_var に格納
  3. レスポンスヘッダーに X-Request-ID を付与して返す
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..core.context import (
    client_ip_var,
    request_id_var,
    request_method_var,
    request_path_var,
)


def _resolve_client_ip(request: Request) -> str:
    """Cloud Run のロードバランサ越しでも実 IP を取れるよう X-Forwarded-For を優先する。"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # カンマ区切りの先頭が原クライアント
        return forwarded.split(",", 1)[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return ""


class RequestIDMiddleware(BaseHTTPMiddleware):
    """X-Request-ID と攻撃追跡用メタデータをリクエスト/レスポンスに付与するミドルウェア。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        rid_token = request_id_var.set(request_id)
        ip_token = client_ip_var.set(_resolve_client_ip(request))
        path_token = request_path_var.set(request.url.path)
        method_token = request_method_var.set(request.method)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(rid_token)
            client_ip_var.reset(ip_token)
            request_path_var.reset(path_token)
            request_method_var.reset(method_token)
        response.headers["X-Request-ID"] = request_id
        return response
