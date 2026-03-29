"""
AI キャリアパス分析 API エンドポイント。

POST   /api/career-analysis/generate     — キャリアパス分析を実行
GET    /api/career-analysis/             — 分析履歴一覧
GET    /api/career-analysis/{id}         — 分析結果詳細
DELETE /api/career-analysis/{id}         — 分析結果削除
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

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
)
from ..services.career_analysis.builder import build_career_analysis
from ..services.intelligence.llm import get_llm_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/career-analysis", tags=["career-analysis"])

_llm_client = get_llm_client()


def _to_response(analysis) -> CareerAnalysisResponse:
    """DB モデルを Pydantic レスポンスに変換する。"""
    result = json.loads(analysis.result_json)
    return CareerAnalysisResponse(
        id=analysis.id,
        version=analysis.version,
        target_position=analysis.target_position,
        result=CareerAnalysisResult(**result),
        created_at=analysis.created_at,
    )


@router.post("/generate", response_model=CareerAnalysisResponse)
@limiter.limit("5/minute")
async def generate(
    request: Request,
    payload: CareerAnalysisGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI キャリアパス分析を実行し、結果を保存する。"""
    # 職務経歴書データの存在チェック
    resume = db.query(Resume).filter_by(user_id=current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=422,
            detail=get_error("career_analysis.no_resume_data"),
        )

    if not await _llm_client.check_available():
        raise HTTPException(
            status_code=503,
            detail=get_error("career_analysis.llm_unavailable"),
        )

    try:
        result = await build_career_analysis(
            db=db,
            user_id=current_user.id,
            target_position=payload.target_position,
            llm_client=_llm_client,
        )
    except ValueError as exc:
        logger.exception("キャリアパス分析に失敗しました (user_id=%s)", current_user.id)
        detail = get_error("career_analysis.generate_failed")
        if str(exc) == "LLM からの応答が空です":
            detail = get_error("career_analysis.llm_unavailable")
        raise HTTPException(
            status_code=503,
            detail=detail,
        )

    repo = CareerAnalysisRepository(db, current_user.id)
    analysis = repo.create(
        target_position=payload.target_position,
        result_json_str=json.dumps(result, ensure_ascii=False),
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
        raise HTTPException(
            status_code=404,
            detail=get_error("career_analysis.not_found"),
        )
    return _to_response(analysis)


@router.delete("/{analysis_id}", status_code=204)
def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分析結果を削除する。"""
    repo = CareerAnalysisRepository(db, current_user.id)
    if not repo.delete(analysis_id):
        raise HTTPException(
            status_code=404,
            detail=get_error("career_analysis.not_found"),
        )
