"""
ブログ連携 API エンドポイント。

GET    /api/blog/accounts              — 連携アカウント一覧
POST   /api/blog/accounts              — 連携アカウント登録
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
from ..models import BlogSummaryCache, User
from ..repositories import BlogAccountRepository, BlogArticleRepository
from ..schemas import (
    BlogAccountCreate,
    BlogAccountResponse,
    BlogArticleResponse,
    BlogScoreResponse,
    BlogSummaryRequest,
    BlogSummaryResponse,
    BlogSyncResponse,
)
from ..schemas.career_analysis import TaskStatusResponse
from ..services.blog.collector import (
    BlogPlatformRequestError,
    UnsupportedBlogPlatformError,
    verify_user_exists,
)
from ..services.blog.scorer import blog_articles_to_score_dicts, calculate_blog_score
from ..services.blog.sync_service import BlogSyncService
from ..services.intelligence.llm_summarizer import check_llm_available
from ..services.tasks import TaskType, get_task_dispatcher

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

    # 外部プラットフォーム上にユーザーが存在するか検証
    try:
        user_exists = await verify_user_exists(body.platform, body.username)
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

    account = repo.upsert(body.platform, body.username)
    return account


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
    """保存済みのブログ AI 分析結果を取得する。"""
    cache = db.query(BlogSummaryCache).filter_by(user_id=user.id).first()
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
    cache = db.query(BlogSummaryCache).filter_by(user_id=user.id).first()
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
    body: BlogSummaryRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ブログ記事の AI サマリをバックグラウンドで生成する。"""
    # 進行中のタスクがあればそのステータスを返す
    cache = db.query(BlogSummaryCache).filter_by(user_id=user.id).first()
    if cache and cache.status in ("pending", "processing"):
        return BlogSummaryResponse(
            summary=cache.summary or "",
            available=False,
            status=cache.status,
        )

    available = await check_llm_available()
    if not available:
        return BlogSummaryResponse(summary="", available=False)

    # キャッシュレコードを準備して pending にセット
    if not cache:
        cache = BlogSummaryCache(user_id=user.id)
        db.add(cache)
    cache.status = "pending"
    cache.error_message = None
    db.commit()

    articles_data = [art.model_dump() for art in body.articles]

    try:
        dispatcher = get_task_dispatcher(background_tasks)
        await dispatcher.dispatch(
            TaskType.BLOG_SUMMARIZE,
            {
                "user_id": user.id,
                "articles": articles_data,
            },
        )
    except Exception:
        logger.exception("ブログサマリタスクのディスパッチに失敗しました")
        cache.status = "failed"
        cache.error_message = "タスクの開始に失敗しました"
        db.commit()
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
