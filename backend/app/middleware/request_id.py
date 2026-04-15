"""リクエスト ID ミドルウェア。

受信リクエストごとに一意の X-Request-ID を付与し、ContextVar に格納する。
すべてのログは CloudLoggingFormatter が ContextVar から request_id を自動注入するため、
各モジュールで明示的に extra={"request_id": ...} を書く必要はない。

処理フロー:
  1. X-Request-ID リクエストヘッダーが存在すれば使用、なければ UUID4 を生成
  2. request_id_var に格納（ContextVar はリクエストスコープで伝播）
  3. レスポンスヘッダーに X-Request-ID を付与して返す
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..core.context import request_id_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    """X-Request-ID をリクエスト/レスポンスに付与するミドルウェア。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response
