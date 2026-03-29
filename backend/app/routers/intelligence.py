"""
キャリアインテリジェンス API エンドポイント。

POST /api/intelligence/analyze — 全分析パイプラインを実行（結果をDBに保存）。
POST /api/intelligence/position-advice — 現状分析+学習アドバイスを生成。
GET  /api/intelligence/cache — 保存済みの分析結果を取得。
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.encryption import decrypt_field
from ..core.messages import get_error
from ..core.security.auth import get_current_user
from ..core.security.dependencies import limiter
from ..db import get_db
from ..models import GitHubAnalysisCache, User
from ..schemas.intelligence import (
    AnalysisResponse,
    AnalyzeRequest,
    CachedAnalysisResponse,
    PositionAdviceResponse,
)
from ..services.intelligence.github_collector import (
    GitHubUserNotFoundError,
)
from ..services.intelligence.llm_summarizer import (
    check_llm_available,
    generate_learning_advice,
)
from ..services.intelligence.pipeline import run_pipeline
from ..services.intelligence.response_mapper import map_pipeline_result

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
    )


@router.post("/analyze", response_model=AnalysisResponse)
@limiter.limit("5/minute")
async def analyze(
    request: Request,
    payload: AnalyzeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ログイン中の GitHub ユーザーに対して全キャリアインテリジェンスパイプラインを実行します。

    結果はDBに保存され、次回以降はキャッシュから取得可能です。
    GitHub OAuth ログインが必要です（ユーザー名形式: "github:{login}"）。
    """
    if not user.username.startswith("github:"):
        raise HTTPException(
            status_code=403,
            detail=get_error("intelligence.github_login_required"),
        )

    github_username = user.username.removeprefix("github:")

    try:
        result = await asyncio.wait_for(
            run_pipeline(
                username=github_username,
                token=(decrypt_field(user.github_token) if user.github_token else None),
                include_forks=payload.include_forks,
            ),
            timeout=120.0,
        )
    except GitHubUserNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=get_error("intelligence.github_user_not_found", username=github_username),
        )
    except asyncio.TimeoutError:
        logger.warning(
            "%s のインテリジェンスパイプラインがタイムアウトしました",
            github_username,
        )
        raise HTTPException(
            status_code=504,
            detail=get_error("intelligence.analysis_timeout"),
        )
    except Exception:
        logger.exception(
            "%s のインテリジェンスパイプラインが失敗しました",
            github_username,
        )
        raise HTTPException(
            status_code=502,
            detail=get_error("intelligence.profile_analysis_failed"),
        )

    response = map_pipeline_result(result)

    # 分析結果をDBに保存（学習アドバイスはクリアして再生成を促す）
    cache = _get_or_create_cache(db, user.id)
    cache.analysis_result = response.model_dump()
    cache.position_advice = None
    db.commit()

    return response


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
