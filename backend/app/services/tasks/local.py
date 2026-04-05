"""ローカル環境用ディスパッチャー（FastAPI BackgroundTasks）。"""

from fastapi import BackgroundTasks

from .base import TaskDispatcher, TaskType
from .worker import execute_task


class LocalDispatcher(TaskDispatcher):
    """FastAPI の BackgroundTasks を利用してレスポンス返却後に同一プロセスで実行する。"""

    def __init__(self, background_tasks: BackgroundTasks):
        self._bg = background_tasks

    async def dispatch(self, task_type: TaskType, payload: dict) -> None:
        self._bg.add_task(execute_task, task_type, payload)
