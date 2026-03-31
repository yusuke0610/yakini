"""
内部タスクエンドポイント（Cloud Tasks コールバック用）。

POST /internal/tasks/{task_type} — Cloud Tasks からのタスク実行リクエストを受け付ける
"""

import logging
import os

from fastapi import APIRouter, HTTPException, Request

from ..core.messages import get_error
from ..services.tasks.base import TaskType
from ..services.tasks.worker import execute_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/tasks", tags=["internal"])


def _verify_request(request: Request) -> bool:
    """Cloud Tasks からのリクエストか検証する。

    ローカルでは TASK_RUNNER=local なのでこのエンドポイントは通常使われないが、
    テスト用に常に許可する。Cloud 環境では X-CloudTasks-QueueName ヘッダーで検証する。
    """
    if os.environ.get("TASK_RUNNER", "local") == "local":
        return True
    queue_name = request.headers.get("X-CloudTasks-QueueName")
    return bool(queue_name)


@router.post("/{task_type}")
async def handle_task(task_type: str, request: Request):
    """Cloud Tasks コールバックまたはローカルテスト用エンドポイント。"""
    if not _verify_request(request):
        raise HTTPException(
            status_code=403,
            detail=get_error("task.internal_unauthorized"),
        )

    try:
        task_type_enum = TaskType(task_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不明なタスク種別: {task_type}")

    payload = await request.json()
    await execute_task(task_type_enum, payload)
    return {"status": "ok"}
