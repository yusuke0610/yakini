"""
キャリアインテリジェンス API エンドポイント。

POST /api/intelligence/analyze         — 全分析パイプラインをバックグラウンド実行（202）
POST /api/intelligence/position-advice — 現状分析+学習アドバイスを生成
GET  /api/intelligence/cache           — 保存済みの分析結果を取得
GET  /api/intelligence/cache/status    — 分析ステータスポーリング用
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.messages import get_error
from ..core.security.auth import get_current_user
from ..core.security.dependencies import limiter
from ..db import get_db
from ..models import GitHubAnalysisCache, User
from ..schemas.career_analysis import TaskStatusResponse
from ..schemas.intelligence import (
    AnalyzeRequest,
    CachedAnalysisResponse,
    PositionAdviceResponse,
)
from ..services.intelligence.llm_summarizer import (
    check_llm_available,
    generate_learning_advice,
)
from ..services.tasks import TaskType, get_task_dispatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


def _get_or_create_cache(db: Session, user_id: str) -> GitHubAnalysisCache:
    """ユーザーのキャッシュレコードを取得、なければ作成する。"""
    cache = db.query(GitHubAnalysisCache).filter_by(user_id=user_id).first()
    if not cache:
        cache = GitHubAnalysisCache(user_id=user_id)
        db.add(cache)
        db.flush()
    return cache


@router.get("/cache", response_model=CachedAnalysisResponse)
def get_cache(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存済みの分析結果・学習アドバイスを取得する。"""
    cache = db.query(GitHubAnalysisCache).filter_by(user_id=user.id).first()
    if not cache:
        return CachedAnalysisResponse()
    return CachedAnalysisResponse(
        analysis_result=cache.analysis_result,
        position_advice=cache.position_advice,
        status=cache.status,
        error_message=cache.error_message,
    )


@router.get("/cache/status", response_model=TaskStatusResponse)
def get_cache_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """分析ステータスを返す（軽量ポーリング用）。"""
    cache = db.query(GitHubAnalysisCache).filter_by(user_id=user.id).first()
    if not cache:
        return TaskStatusResponse(status="completed")
    return TaskStatusResponse(
        status=cache.status,
        error_message=cache.error_message,
    )


@router.post("/analyze", status_code=202)
@limiter.limit("5/minute")
async def analyze(
    request: Request,
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GitHub 分析パイプラインをバックグラウンドで開始する。"""
    if not user.username.startswith("github:"):
        raise HTTPException(
            status_code=403,
            detail=get_error("intelligence.github_login_required"),
        )

    github_username = user.username.removeprefix("github:")

    # 進行中のタスクがあればそのステータスを返す
    cache = _get_or_create_cache(db, user.id)
    if cache.status in ("pending", "processing"):
        return {"status": cache.status}

    # pending にセットして即座に返却
    cache.status = "pending"
    cache.error_message = None
    db.commit()

    try:
        dispatcher = get_task_dispatcher(background_tasks)
        await dispatcher.dispatch(
            TaskType.GITHUB_ANALYSIS,
            {
                "user_id": user.id,
                "github_username": github_username,
                "github_token": user.github_token,
                "include_forks": payload.include_forks,
            },
        )
    except Exception:
        logger.exception("GitHub 分析タスクのディスパッチに失敗しました")
        cache.status = "failed"
        cache.error_message = "タスクの開始に失敗しました"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=get_error("task.dispatch_failed"),
        )

    return {"status": "pending"}


@router.post("/position-advice", response_model=PositionAdviceResponse)
@limiter.limit("10/minute")
async def position_advice(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    分析結果とポジションスコアに基づく現状分析+学習アドバイスを LLM で生成します。
    キャッシュ済みの分析結果からデータを取得し、統合プロンプトで生成します。
    """
    cache = db.query(GitHubAnalysisCache).filter_by(user_id=user.id).first()
    if not cache or not cache.analysis_result:
        raise HTTPException(
            status_code=404,
            detail=get_error("intelligence.no_analysis_cache"),
        )

    analysis = cache.analysis_result
    scores = analysis.get("position_scores")
    if not scores:
        raise HTTPException(
            status_code=404,
            detail=get_error("intelligence.no_position_scores"),
        )

    available = await check_llm_available()
    if not available:
        return PositionAdviceResponse(advice="", available=False)

    advice = await generate_learning_advice(analysis, scores)
    if not advice:
        return PositionAdviceResponse(advice="", available=False)

    # 学習アドバイスをDBに保存
    cache.position_advice = advice
    db.commit()

    return PositionAdviceResponse(advice=advice, available=True)
