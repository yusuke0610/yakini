"""
AI キャリアパス分析 API エンドポイント。

POST   /api/career-analysis/generate          — キャリアパス分析を開始（202 非同期）
GET    /api/career-analysis/                   — 分析履歴一覧
GET    /api/career-analysis/{id}               — 分析結果詳細
GET    /api/career-analysis/{id}/status        — ステータスポーリング用
DELETE /api/career-analysis/{id}               — 分析結果削除
"""

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from ..core.errors import ErrorCode, raise_app_error, resolve_async_error_code
from ..core.messages import get_error
from ..core.security.auth import get_current_user
from ..core.security.dependencies import limiter
from ..db import get_db
from ..models import Resume, User
from ..repositories import CareerAnalysisRepository
from ..schemas.career_analysis import (
    CareerAnalysisGenerateRequest,
    CareerAnalysisResponse,
    CareerAnalysisResult,
    TaskStatusResponse,
)
from ..services.intelligence.llm import get_llm_client
from ..services.tasks import TaskType, get_task_dispatcher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/career-analysis", tags=["career-analysis"])

_llm_client = get_llm_client()


def _to_response(analysis) -> CareerAnalysisResponse:
    """DB モデルを Pydantic レスポンスに変換する。"""
    result = None
    if analysis.result_json:
        parsed = json.loads(analysis.result_json)
        result = CareerAnalysisResult(**parsed)
    return CareerAnalysisResponse(
        id=analysis.id,
        version=analysis.version,
        target_position=analysis.target_position,
        result=result,
        status=analysis.status,
        error_message=analysis.error_message,
        created_at=analysis.created_at,
    )


@router.post("/generate", response_model=CareerAnalysisResponse, status_code=202)
@limiter.limit("5/minute")
async def generate(
    request: Request,
    payload: CareerAnalysisGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI キャリアパス分析をバックグラウンドで開始する。"""
    repo = CareerAnalysisRepository(db, current_user.id)

    # 進行中のタスクがあればそのレコードを返す
    pending = repo.get_pending()
    if pending:
        return _to_response(pending)

    # 職務経歴書データの存在チェック
    resume = db.query(Resume).filter_by(user_id=current_user.id).first()
    if not resume:
        raise_app_error(
            status_code=422,
            code=ErrorCode.VALIDATION_ERROR,
            message=get_error("career_analysis.no_resume_data"),
            action="職務経歴書を入力してから再試行してください",
        )

    if not await _llm_client.check_available():
        raise_app_error(
            status_code=503,
            code=ErrorCode.LLM_UNAVAILABLE,
            message=get_error("career_analysis.llm_unavailable"),
            action="しばらく待ってから再試行してください",
        )

    # pending レコード作成
    analysis = repo.create_pending(target_position=payload.target_position)

    # バックグラウンドタスクをディスパッチ
    try:
        dispatcher = get_task_dispatcher(background_tasks)
        await dispatcher.dispatch(
            TaskType.CAREER_ANALYSIS,
            {
                "user_id": current_user.id,
                "record_id": analysis.id,
                "target_position": payload.target_position,
            },
        )
    except Exception:
        logger.exception("キャリア分析タスクのディスパッチに失敗しました")
        raise_app_error(
            status_code=500,
            code=ErrorCode.INTERNAL_ERROR,
            message=get_error("task.dispatch_failed"),
            action="しばらく待ってから再試行してください",
        )

    return _to_response(analysis)


# リトライ可能な終端ステータス（リトライ枯渇 or リトライ不可エラー）
_RETRYABLE_TERMINAL_STATUSES = {"dead_letter"}


@router.post("/{analysis_id}/retry", response_model=CareerAnalysisResponse, status_code=202)
@limiter.limit("5/minute")
async def retry_analysis(
    analysis_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """失敗したキャリア分析タスクを手動で再実行する。

    ``dead_letter`` 状態のレコードのみ再実行可能。
    ``retry_count`` を 0 にリセットし、``target_position`` は既存レコードの値を再利用する。
    """
    repo = CareerAnalysisRepository(db, current_user.id)
    analysis = repo.get_by_id(analysis_id)
    if not analysis:
        raise_app_error(
            status_code=404,
            code=ErrorCode.VALIDATION_ERROR,
            message=get_error("career_analysis.not_found"),
            action="一覧に戻って対象を選び直してください",
        )
    if analysis.status not in _RETRYABLE_TERMINAL_STATUSES:
        raise_app_error(
            status_code=409,
            code=ErrorCode.VALIDATION_ERROR,
            message=f"このタスクはリトライできない状態です（現在: {analysis.status}）",
            action="タスクの完了または失敗を待ってから再試行してください",
        )

    analysis.status = "pending"
    analysis.error_message = None
    analysis.retry_count = 0
    analysis.started_at = None
    analysis.completed_at = None
    db.commit()

    try:
        dispatcher = get_task_dispatcher(background_tasks)
        await dispatcher.dispatch(
            TaskType.CAREER_ANALYSIS,
            {
                "user_id": current_user.id,
                "record_id": analysis.id,
                "target_position": analysis.target_position,
            },
        )
    except Exception:
        logger.exception("キャリア分析タスクの再実行に失敗しました")
        analysis.status = "dead_letter"
        analysis.error_message = "タスクの再実行に失敗しました"
        db.commit()
        raise_app_error(
            status_code=500,
            code=ErrorCode.INTERNAL_ERROR,
            message=get_error("task.dispatch_failed"),
            action="しばらく待ってから再試行してください",
        )

    return _to_response(analysis)


@router.get("/", response_model=list[CareerAnalysisResponse])
def list_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """ログインユーザーの全分析結果を返す。"""
    repo = CareerAnalysisRepository(db, current_user.id)
    return [_to_response(a) for a in repo.get_all()]


@router.get("/{analysis_id}", response_model=CareerAnalysisResponse)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """指定 ID の分析結果を返す。"""
    repo = CareerAnalysisRepository(db, current_user.id)
    analysis = repo.get_by_id(analysis_id)
    if not analysis:
        raise_app_error(
            status_code=404,
            code=ErrorCode.VALIDATION_ERROR,
            message=get_error("career_analysis.not_found"),
            action="一覧に戻って対象を選び直してください",
        )
    return _to_response(analysis)


@router.get("/{analysis_id}/status", response_model=TaskStatusResponse)
def get_analysis_status(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """タスクステータスを返す（軽量ポーリング用）。"""
    repo = CareerAnalysisRepository(db, current_user.id)
    analysis = repo.get_by_id(analysis_id)
    if not analysis:
        raise_app_error(
            status_code=404,
            code=ErrorCode.VALIDATION_ERROR,
            message=get_error("career_analysis.not_found"),
            action="一覧に戻って対象を選び直してください",
        )
    return TaskStatusResponse(
        status=analysis.status,
        error_message=analysis.error_message,
        error_code=resolve_async_error_code(analysis.error_message),
    )


@router.delete("/{analysis_id}", status_code=204)
def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分析結果を削除する。"""
    repo = CareerAnalysisRepository(db, current_user.id)
    if not repo.delete(analysis_id):
        raise_app_error(
            status_code=404,
            code=ErrorCode.VALIDATION_ERROR,
            message=get_error("career_analysis.not_found"),
            action="一覧に戻って対象を選び直してください",
        )
