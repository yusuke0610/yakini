"""
ブログ連携 API エンドポイント。

GET    /api/blog/accounts          — 連携アカウント一覧
POST   /api/blog/accounts          — 連携アカウント登録
DELETE /api/blog/accounts/{id}     — 連携アカウント解除
GET    /api/blog/articles          — 記事一覧
POST   /api/blog/accounts/{id}/sync — 手動同期
POST   /api/blog/summarize         — AI サマリ生成
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..dependencies import limiter
from ..messages import get_error
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
from ..services.blog_collector import (
    BlogPlatformRequestError,
    UnsupportedBlogPlatformError,
    fetch_articles,
    verify_user_exists,
)
from ..services.blog_scorer import calculate_blog_score
from ..services.intelligence.llm_summarizer import (
    check_llm_available,
    summarize_blog_articles,
)

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
    account_repo = BlogAccountRepository(db, user.id)
    account = account_repo.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail=get_error("blog.account_link_not_found"))

    try:
        raw_articles = await fetch_articles(account.platform, account.username)
    except UnsupportedBlogPlatformError as exc:
        raise HTTPException(
            status_code=400,
            detail=get_error("blog.platform_not_supported"),
        ) from exc
    except Exception:
        logger.exception("ブログ記事の取得に失敗しました: %s/%s", account.platform, account.username)
        raise HTTPException(
            status_code=502,
            detail=get_error("blog.sync_failed"),
        )

    for art in raw_articles:
        art["account_id"] = account.id

    article_repo = BlogArticleRepository(db, user.id)
    synced = article_repo.upsert_many(raw_articles)
    total = article_repo.count_by_user()

    return BlogSyncResponse(synced_count=synced, total_count=total)


@router.get("/summary-cache", response_model=BlogSummaryResponse)
def get_summary_cache(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存済みのブログ AI 分析結果を取得する。"""
    cache = db.query(BlogSummaryCache).filter_by(user_id=user.id).first()
    if cache and cache.summary:
        return BlogSummaryResponse(summary=cache.summary, available=True)
    return BlogSummaryResponse(summary="", available=False)


@router.post("/summarize", response_model=BlogSummaryResponse)
@limiter.limit("5/minute")
async def summarize_blog(
    request: Request,
    body: BlogSummaryRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ブログ記事の AI サマリを生成する（Ollama）。結果はDBに保存する。"""
    available = await check_llm_available()
    if not available:
        return BlogSummaryResponse(summary="", available=False)

    articles_data = [art.model_dump() for art in body.articles]
    summary = await summarize_blog_articles(articles_data)
    if not summary:
        return BlogSummaryResponse(summary="", available=False)

    # DB にキャッシュ保存
    cache = db.query(BlogSummaryCache).filter_by(user_id=user.id).first()
    if not cache:
        cache = BlogSummaryCache(user_id=user.id)
        db.add(cache)
    cache.summary = summary
    db.commit()

    return BlogSummaryResponse(summary=summary, available=True)


@router.get("/score", response_model=BlogScoreResponse)
def get_blog_score(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """保存済みの記事に対してスコアリングを実行する。"""
    repo = BlogArticleRepository(db, user.id)
    articles = repo.list_by_user()

    # BlogArticle モデルを dict に変換
    articles_data = [
        {
            "id": str(art.id),
            "title": art.title,
            "url": art.url,
            "published_at": art.published_at,
            "likes_count": art.likes_count,
            "tags": art.tags,
        }
        for art in articles
    ]

    score = calculate_blog_score(articles_data)
    return BlogScoreResponse(
        frequency_rank=score.frequency_rank,
        reaction_rank=score.reaction_rank,
        count_rank=score.count_rank,
        overall_rank=score.overall_rank,
        tech_article_count=score.tech_article_count,
        total_article_count=score.total_article_count,
        avg_monthly_posts=score.avg_monthly_posts,
        avg_likes=score.avg_likes,
        articles=[
            {
                "id": a.id,
                "title": a.title,
                "url": a.url,
                "published_at": a.published_at,
                "likes_count": a.likes_count,
                "tags": a.tags,
                "is_tech": a.is_tech,
            }
            for a in score.articles
        ],
    )
