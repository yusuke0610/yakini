"""タスクハンドラの抽象基底クラス。

各タスク種別は ``TaskHandler`` を継承し、以下を実装する:
  - ``get_record(db, payload)``: payload から対応するキャッシュレコードを取得
  - ``run(db, payload)``: タスク本体の実行

レコード状態遷移（``processing`` / ``completed`` / ``dead_letter`` / ``retrying``）は
worker 側で本基底クラスが提供する共通ロジックを通じて行う。
"""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session


class TaskHandler(ABC):
    """非同期タスクの実行とレコード取得を担う抽象基底クラス。"""

    @abstractmethod
    def get_record(self, db: Session, payload: dict) -> Any | None:
        """payload からキャッシュレコードを取得する（status / error_message 等の更新対象）。"""

    @abstractmethod
    async def run(self, db: Session, payload: dict) -> None:
        """タスク本体を実行する。状態遷移は呼び出し側 (worker) が担う。"""
