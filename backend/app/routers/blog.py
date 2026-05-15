"""
ブログ連携 API エンドポイント。

GET    /api/blog/accounts              — 連携アカウント一覧
POST   /api/blog/accounts              — 連携アカウント登録
PATCH  /api/blog/accounts/{platform}   — 連携アカウント更新
DELETE /api/blog/accounts/{id}         — 連携アカウント解除
GET    /api/blog/articles              — 記事一覧
POST   /api/blog/accounts/{id}/sync   — 手動同期
POST   /api/blog/summarize            — AI サマリ生成（202 非同期）
GET    /api/blog/summary-cache         — 保存済みサマリ取得
GET    /api/blog/summary-cache/status  — サマリ生成ステータスポーリング用
GET    /api/blog/score                 — ブログスコアリング
"""

import logging
from dataclasses import asdict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..core.errors import resolve_async_error_code
from ..core.messages import get_error
from ..core.security.auth import get_current_user
from ..core.security.dependencies import limiter
from ..db import get_db
from ..models import User
from ..repositories import BlogAccountRepository, BlogArticleRepository, BlogSummaryCacheRepository
from ..schemas import (
    BlogAccountCreate,
    BlogAccountResponse,
    BlogAccountUpdate,
    BlogArticleResponse,
    BlogScoreResponse,
    BlogSummaryResponse,
    BlogSyncResponse,
)
from ..schemas.career_analysis import TaskStatusResponse
from ..services.blog.account_service import BlogAccountService
from ..services.blog.collector import (
    BlogAccountNotFoundError,
    BlogPlatformRequestError,
    UnsupportedBlogPlatformError,
    normalize_username,
    verify_user_exists,
)
from ..services.blog.scorer import blog_articles_to_score_dicts, calculate_blog_score
from ..services.blog.sync_service import BlogSyncService
from ..services.intelligence.llm_summarizer import check_llm_available
from ..services.tasks import AsyncTaskCacheService, TaskType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/blog", tags=["blog"])


@router.get("/accounts", response_model=list[BlogAccountResponse])
def list_accounts(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """連携アカウント一覧を取得する。"""
    repo = BlogAccountRepository(db, user.id)
    return repo.list_by_user()


@router.post("/accounts", response_model=BlogAccountResponse, status_code=201)
@limiter.limit("10/minute")
async def add_account(
    request: Request,
    body: BlogAccountCreate,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """連携アカウントを登録する。
    同じプラットフォームは1つまで。ユーザー存在チェックあり。
    """
    repo = BlogAccountRepository(db, user.id)
    existing = repo.get_by_platform(body.platform)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=get_error("blog.account_already_registered"),
        )

    try:
        normalized_username = normalize_username(body.platform, body.username)
    except UnsupportedBlogPlatformError as exc:
        raise HTTPException(
            status_code=400,
            detail=get_error("blog.platform_not_supported"),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=get_error("blog.account_not_found"),
        ) from exc

    # 外部プラットフォーム上にユーザーが存在するか検証
    try:
        user_exists = await verify_user_exists(body.platform, normalized_username)
    except UnsupportedBlogPlatformError as exc:
        raise HTTPException(
            status_code=400,
            detail=get_error("blog.platform_not_supported"),
        ) from exc
    except BlogPlatformRequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=get_error("blog.account_check_failed"),
        ) from exc

    if not user_exists:
        raise HTTPException(
            status_code=404,
            detail=get_error("blog.account_not_found"),
        )

    account = repo.upsert(body.platform, normalized_username)
    return account


@router.patch("/accounts/{platform}", response_model=BlogAccountResponse)
@limiter.limit("10/minute")
async def update_account(
    request: Request,
    platform: str,
    body: BlogAccountUpdate,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """連携アカウントの username を更新し、同期状態を未同期に戻す。"""
    service = BlogAccountService(db, user.id)
    if not service.get_by_platform(platform):
        raise HTTPException(status_code=404, detail=get_error("blog.account_link_not_found"))

    try:
        return await service.update_username(platform, body.username)
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
    except BlogPlatformRequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=get_error("blog.account_check_failed"),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=get_error("blog.account_not_found"),
        ) from exc


@router.delete("/accounts/{account_id}", status_code=204)
def delete_account(
    account_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """連携アカウントを解除する。紐づく記事も削除される。"""
    account_repo = BlogAccountRepository(db, user.id)
    if not account_repo.delete(account_id):
        raise HTTPException(status_code=404, detail=get_error("blog.account_link_not_found"))


@router.get("/articles", response_model=list[BlogArticleResponse])
def list_articles(
    platform: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """DB に保存済みの記事一覧を取得する。"""
    repo = BlogArticleRepository(db, user.id)
    return repo.list_by_user(platform=platform)


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


@router.get("/score", response_model=BlogScoreResponse)
def get_blog_score(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """保存済みの記事に対してスコアリングを実行する。"""
    repo = BlogArticleRepository(db, user.id)
    articles = repo.list_by_user()

    score = calculate_blog_score(blog_articles_to_score_dicts(articles))
    return BlogScoreResponse.model_validate(asdict(score))
