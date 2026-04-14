"""
通知 API エンドポイント。

GET    /api/notifications              — 通知一覧（最新30件）
GET    /api/notifications/unread-count — 未読件数
PATCH  /api/notifications/{id}/read   — 既読にする
POST   /api/notifications/read-all    — 全件既読にする
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.date_utils import to_jst
from ..core.security.auth import get_current_user
from ..db import get_db
from ..models import User
from ..repositories.notification import NotificationRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    """通知レスポンス。"""

    id: str
    task_type: str
    status: str
    title: str
    message: str | None
    is_read: bool
    created_at: str

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    """未読件数レスポンス。"""

    count: int


class MarkAllReadResponse(BaseModel):
    """全件既読レスポンス。"""

    updated: int


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """最新30件の通知を取得する。"""
    repo = NotificationRepository(db, user.id)
    notifications = repo.list_recent()
    return [
        NotificationResponse(
            id=n.id,
            task_type=n.task_type,
            status=n.status,
            title=n.title,
            message=n.message,
            is_read=n.is_read,
            created_at=to_jst(n.created_at).isoformat(),
        )
        for n in notifications
    ]


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """未読通知件数を返す。"""
    repo = NotificationRepository(db, user.id)
    return UnreadCountResponse(count=repo.unread_count())


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """指定された通知を既読にする。"""
    from fastapi import HTTPException, status

    repo = NotificationRepository(db, user.id)
    updated = repo.mark_read(notification_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知が見つかりません")

    notifications = repo.list_recent()
    n = next((n for n in notifications if n.id == notification_id), None)
    if not n:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知が見つかりません")
    return NotificationResponse(
        id=n.id,
        task_type=n.task_type,
        status=n.status,
        title=n.title,
        message=n.message,
        is_read=n.is_read,
        created_at=n.created_at.isoformat(),
    )


@router.post("/read-all", response_model=MarkAllReadResponse)
def mark_all_as_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """全通知を既読にする。"""
    repo = NotificationRepository(db, user.id)
    updated = repo.mark_all_read()
    return MarkAllReadResponse(updated=updated)
