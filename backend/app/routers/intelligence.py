"""
キャリアインテリジェンス API エンドポイント。

POST /api/intelligence/analyze         — 全分析パイプラインをバックグラウンド実行（202）
POST /api/intelligence/position-advice — 現状分析+学習アドバイスを生成
GET  /api/intelligence/cache           — 保存済みの分析結果を取得
GET  /api/intelligence/cache/status    — 分析ステータスポーリング用
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from ..core.errors import ErrorCode, raise_app_error, resolve_async_error_code
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
    ProgressResponse,
)
from ..services.intelligence.llm_advice_service import LLMPositionAdviceService
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
        error_code=resolve_async_error_code(cache.error_message),
    )


@router.get("/progress", response_model=ProgressResponse)
async def get_analysis_progress(
    user: User = Depends(get_current_user),
):
    """GitHub 分析タスクの進捗を取得する（ポーリング用）。

    Redis にデータがない場合（タスク未開始・Redis 障害）は step_index=0 のデフォルトを返す。
    """
    from ..services.progress_service import get_progress

    data = await get_progress(user.id)
    return ProgressResponse(**data)


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
        error_code=resolve_async_error_code(cache.error_message),
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
        raise_app_error(
            status_code=403,
            code=ErrorCode.AUTH_REQUIRED,
            message=get_error("intelligence.github_login_required"),
            action="GitHub アカウントでログインし直してください",
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
        cache.status = "dead_letter"
        cache.error_message = "タスクの開始に失敗しました"
        db.commit()
        raise_app_error(
            status_code=500,
            code=ErrorCode.INTERNAL_ERROR,
            message=get_error("task.dispatch_failed"),
            action="しばらく待ってから再試行してください",
        )

    return {"status": "pending"}


# リトライ可能な終端ステータス（リトライ枯渇 or リトライ不可エラー）
_RETRYABLE_TERMINAL_STATUSES = {"dead_letter"}


@router.post("/analyze/retry", status_code=202)
@limiter.limit("5/minute")
async def retry_analyze(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: AnalyzeRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """失敗した GitHub 分析タスクを手動で再実行する。

    ``dead_letter`` 状態のキャッシュのみ再実行可能。
    ``retry_count`` を 0 にリセットし、ステータスを ``pending`` に戻して再ディスパッチする。
    """
    if not user.username.startswith("github:"):
        raise_app_error(
            status_code=403,
            code=ErrorCode.AUTH_REQUIRED,
            message=get_error("intelligence.github_login_required"),
            action="GitHub アカウントでログインし直してください",
        )

    cache = db.query(GitHubAnalysisCache).filter_by(user_id=user.id).first()
    if not cache:
        raise_app_error(
            status_code=404,
            code=ErrorCode.VALIDATION_ERROR,
            message=get_error("intelligence.no_analysis_cache"),
            action="先に GitHub 分析を実行してください",
        )
    if cache.status not in _RETRYABLE_TERMINAL_STATUSES:
        raise_app_error(
            status_code=409,
            code=ErrorCode.VALIDATION_ERROR,
            message=f"このタスクはリトライできない状態です（現在: {cache.status}）",
            action="タスクの完了または失敗を待ってから再試行してください",
        )

    github_username = user.username.removeprefix("github:")
    include_forks = payload.include_forks if payload else False

    cache.status = "pending"
    cache.error_message = None
    cache.retry_count = 0
    cache.started_at = None
    cache.completed_at = None
    db.commit()

    try:
        dispatcher = get_task_dispatcher(background_tasks)
        await dispatcher.dispatch(
            TaskType.GITHUB_ANALYSIS,
            {
                "user_id": user.id,
                "github_username": github_username,
                "github_token": user.github_token,
                "include_forks": include_forks,
            },
        )
    except Exception:
        logger.exception("GitHub 分析タスクの再実行に失敗しました")
        cache.status = "dead_letter"
        cache.error_message = "タスクの再実行に失敗しました"
        db.commit()
        raise_app_error(
            status_code=500,
            code=ErrorCode.INTERNAL_ERROR,
            message=get_error("task.dispatch_failed"),
            action="しばらく待ってから再試行してください",
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
    service = LLMPositionAdviceService(db, user.id)

    if not service.has_analysis():
        raise_app_error(
            status_code=404,
            code=ErrorCode.VALIDATION_ERROR,
            message=get_error("intelligence.no_analysis_cache"),
            action="先に GitHub 分析を実行してください",
        )

    if not service.has_position_scores():
        raise_app_error(
            status_code=404,
            code=ErrorCode.VALIDATION_ERROR,
            message=get_error("intelligence.no_position_scores"),
            action="GitHub 分析を再実行してください",
        )

    advice = await service.generate_and_save()
    if not advice:
        return PositionAdviceResponse(advice="", available=False)

    return PositionAdviceResponse(advice=advice, available=True)
