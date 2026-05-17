"""ブログアカウント手動同期エンドポイント。"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from ...core.messages import get_error
from ...core.security.auth import get_current_user
from ...core.security.dependencies import limiter
from ...db import get_db
from ...models import User
from ...schemas import BlogSyncResponse
from ...services.blog.collector import (
    BlogAccountNotFoundError,
    UnsupportedBlogPlatformError,
)
from ...services.blog.sync_service import BlogSyncService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/accounts/{account_id}/sync", response_model=BlogSyncResponse)
@limiter.limit("10/minute")
async def sync_account(
    request: Request,
    account_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """外部 API からデータを取得して DB に保存する。"""
    service = BlogSyncService(db, user.id)
    if not service.get_account_or_none(account_id):
        raise HTTPException(status_code=404, detail=get_error("blog.account_link_not_found"))

    try:
        return await service.sync(account_id)
    except BlogAccountNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=get_error("blog.account_not_found"),
        ) from exc
    except UnsupportedBlogPlatformError as exc:
        raise HTTPException(
            status_code=400,
            detail=get_error("blog.platform_not_supported"),
        ) from exc
    except Exception as exc:
        # UnsupportedBlogPlatformError は上の except で先に捕捉される
        raise HTTPException(
            status_code=502,
            detail=get_error("blog.sync_failed"),
        ) from exc
