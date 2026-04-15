"""リクエストスコープのコンテキスト変数。

asyncio タスクをまたいでリクエスト ID を伝播させるための ContextVar を定義する。
ContextVar は asyncio.create_task() で生成した子タスクには引き継がれないため、
子タスク内で参照する場合は copy_context().run(...) パターンを使用すること。
Cloud Tasks 経由のワーカーは HTTP リクエストとして受け取るため
RequestIDMiddleware が正常に機能する。
"""

from contextvars import ContextVar

# ミドルウェアがリクエストごとにセットするリクエスト ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
