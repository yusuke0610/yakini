"""タスクディスパッチャーの基底クラス。"""

from abc import ABC, abstractmethod
from enum import Enum


class TaskType(str, Enum):
    """バックグラウンドで実行可能なタスクの種別。"""

    GITHUB_ANALYSIS = "github_analysis"
    BLOG_SUMMARIZE = "blog_summarize"
    CAREER_ANALYSIS = "career_analysis"


class TaskDispatcher(ABC):
    """タスクをバックグラウンドにディスパッチする共通インターフェース。"""

    @abstractmethod
    async def dispatch(self, task_type: TaskType, payload: dict) -> None:
        """タスクをディスパッチする。payload には user_id と task 固有パラメータを含む。"""
