"""タスクディスパッチャーのファクトリ。"""

import os

from fastapi import BackgroundTasks

from .base import TaskDispatcher


def get_task_dispatcher(
    background_tasks: BackgroundTasks | None = None,
) -> TaskDispatcher:
    """環境変数 TASK_RUNNER に応じたディスパッチャーを返す。

    - ``"local"`` (デフォルト): LocalDispatcher（FastAPI BackgroundTasks）
    - ``"cloud_tasks"``: CloudTasksDispatcher（Google Cloud Tasks）
    """
    runner = os.environ.get("TASK_RUNNER", "local")

    if runner == "cloud_tasks":
        from .cloud_tasks import CloudTasksDispatcher

        return CloudTasksDispatcher()

    if background_tasks is None:
        raise ValueError("LocalDispatcher には BackgroundTasks インスタンスが必要です")

    from .local import LocalDispatcher

    return LocalDispatcher(background_tasks)
