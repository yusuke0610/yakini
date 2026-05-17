"""ドメイン横断で共用する Pydantic スキーマ。"""

from pydantic import BaseModel

_HIRAGANA_PATTERN = r"^[ぁ-ゖー\s　]+$"


class TaskStatusResponse(BaseModel):
    """非同期タスクのステータスを返す軽量レスポンス。

    blog / career_analysis / intelligence など複数の router で共通利用される。
    """

    status: str
    error_message: str | None = None
    error_code: str | None = None
