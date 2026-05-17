"""ブログ AI サマリ生成・リトライ・キャッシュ取得・ステータスポーリング。"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ...core.errors import resolve_async_error_code
from ...core.messages import get_error
from ...core.security.auth import get_current_user
from ...core.security.dependencies import limiter
from ...db import get_db
from ...models import User
from ...repositories import BlogSummaryCacheRepository
from ...schemas import BlogSummaryResponse
from ...schemas.shared import TaskStatusResponse
from ...services.intelligence.llm_summarizer import check_llm_available
from ...services.tasks import AsyncTaskCacheService, TaskType

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary-cache", response_model=BlogSummaryResponse)
def get_summary_cache(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存済みのブログ AI 分析結果を取得する。期限切れキャッシュは無効扱いにする。"""
    cache = BlogSummaryCacheRepository(db, user.id).get()
    if cache and cache.summary:
        return BlogSummaryResponse(
            summary=cache.summary,
            available=True,
            status=cache.status,
            error_message=cache.error_message,
            error_code=resolve_async_error_code(cache.error_message),
        )
    if cache:
        return BlogSummaryResponse(
            summary="",
            available=False,
            status=cache.status,
            error_message=cache.error_message,
            error_code=resolve_async_error_code(cache.error_message),
        )
    return BlogSummaryResponse(summary="", available=False)


@router.get("/summary-cache/status", response_model=TaskStatusResponse)
def get_summary_cache_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """サマリ生成ステータスを返す（軽量ポーリング用）。"""
    cache = BlogSummaryCacheRepository(db, user.id).get()
    if not cache:
        return TaskStatusResponse(status="completed")
    return TaskStatusResponse(
        status=cache.status,
        error_message=cache.error_message,
        error_code=resolve_async_error_code(cache.error_message),
    )


@router.post("/summarize", response_model=BlogSummaryResponse, status_code=202)
@limiter.limit("5/minute")
async def summarize_blog(
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ブログ記事の AI サマリをバックグラウンドで生成する。

    記事は worker 側で ``BlogArticleRepository`` から取得するため、リクエストボディは不要。
    """
    cache = BlogSummaryCacheRepository(db, user.id).get_or_create()
    service = AsyncTaskCacheService(db, cache)

    available = await check_llm_available()
    if not available:
        return BlogSummaryResponse(summary="", available=False)

    # DB 最新状態を取得しつつ pending へアトミック遷移。進行中なら早期リターン
    if not service.try_reset_to_pending():
        return BlogSummaryResponse(
            summary=cache.summary or "",
            available=False,
            status=cache.status,
        )

    try:
        await service.dispatch(
            background_tasks,
            TaskType.BLOG_SUMMARIZE,
            {"user_id": user.id},
            failure_message="タスクの開始に失敗しました",
            logger=logger,
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=get_error("task.dispatch_failed"),
        )

    return BlogSummaryResponse(
        summary="",
        available=False,
        status="pending",
    )


@router.post("/summarize/retry", response_model=BlogSummaryResponse, status_code=202)
@limiter.limit("5/minute")
async def retry_summarize_blog(
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """失敗したブログサマリタスクを手動で再実行する。

    ``dead_letter`` 状態のキャッシュのみ再実行可能。記事は worker 側で
    ``BlogArticleRepository`` から取得するため、リクエストボディは不要。
    """
    cache = BlogSummaryCacheRepository(db, user.id).get()
    if not cache:
        raise HTTPException(
            status_code=404,
            detail="サマリキャッシュが見つかりません",
        )
    service = AsyncTaskCacheService(db, cache)
    if not service.is_retryable_terminal():
        raise HTTPException(
            status_code=409,
            detail=f"このタスクはリトライできない状態です（現在: {cache.status}）",
        )

    available = await check_llm_available()
    if not available:
        return BlogSummaryResponse(summary="", available=False)

    # DB 最新状態を取得しつつアトミック遷移。並列リトライ競合を防ぐ
    if not service.try_reset_to_pending(reset_retry_count=True):
        raise HTTPException(
            status_code=409,
            detail=f"このタスクはリトライできない状態です（現在: {cache.status}）",
        )

    try:
        await service.dispatch(
            background_tasks,
            TaskType.BLOG_SUMMARIZE,
            {"user_id": user.id},
            failure_message="タスクの再実行に失敗しました",
            logger=logger,
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=get_error("task.dispatch_failed"),
        )

    return BlogSummaryResponse(
        summary="",
        available=False,
        status="pending",
    )
