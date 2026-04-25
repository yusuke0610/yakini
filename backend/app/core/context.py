"""リクエストスコープのコンテキスト変数。

asyncio タスクをまたいでリクエスト ID を伝播させるための ContextVar を定義する。
ContextVar は asyncio.create_task() で生成した子タスクには引き継がれないため、
子タスク内で参照する場合は copy_context().run(...) パターンを使用すること。
Cloud Tasks 経由のワーカーは HTTP リクエストとして受け取るため
RequestIDMiddleware が正常に機能する。

不正アクセス追跡のため client_ip / path / method もリクエストスコープで保持する。
これにより全ログエントリに自動的に攻撃元情報が付与される。
"""

from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
client_ip_var: ContextVar[str] = ContextVar("client_ip", default="")
request_path_var: ContextVar[str] = ContextVar("request_path", default="")
request_method_var: ContextVar[str] = ContextVar("request_method", default="")
