"""
キャリアインテリジェンス API エンドポイント。

POST /api/intelligence/analyze — 全分析パイプラインを実行（結果をDBに保存）。
POST /api/intelligence/summarize — AI要約を生成（結果をDBに保存）。
POST /api/intelligence/skill-activity — スキルアクティビティを集計（結果をDBに保存）。
GET  /api/intelligence/cache — 保存済みの分析結果を取得。
"""

import asyncio
import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..dependencies import limiter
from ..encryption import decrypt_field
from ..models import GitHubAnalysisCache, User
from ..schemas_intelligence import (
    AnalysisResponse,
    AnalyzeRequest,
    CachedAnalysisResponse,
    SkillActivityResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from ..services.intelligence.github_collector import (
    GitHubUserNotFoundError,
)
from ..services.intelligence.llm_summarizer import (
    check_llm_available,
    summarize_analysis,
)
from ..services.intelligence.pipeline import run_pipeline
from ..services.intelligence.response_mapper import map_pipeline_result
from ..services.intelligence.skill_activity_analyzer import get_skill_activity

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
    """保存済みの分析結果・AI要約を取得する。"""
    cache = db.query(GitHubAnalysisCache).filter_by(user_id=user.id).first()
    if not cache:
        return CachedAnalysisResponse()
    return CachedAnalysisResponse(
        analysis_result=cache.analysis_result,
        ai_summary=cache.ai_summary,
        skill_activity_month=cache.skill_activity_month,
        skill_activity_year=cache.skill_activity_year,
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
            detail="GitHub分析にはGitHubアカウントでのログインが必要です",
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
            detail=f"GitHubユーザーが見つかりません: {github_username}",
        )
    except asyncio.TimeoutError:
        logger.warning(
            "%s のインテリジェンスパイプラインがタイムアウトしました",
            github_username,
        )
        raise HTTPException(
            status_code=504,
            detail="分析がタイムアウトしました。しばらくしてから再度お試しください。",
        )
    except Exception:
        logger.exception(
            "%s のインテリジェンスパイプラインが失敗しました",
            github_username,
        )
        raise HTTPException(
            status_code=502,
            detail=("GitHubプロフィールの分析に失敗しました。" "しばらくしてから再度お試しください。"),
        )

    response = map_pipeline_result(result)

    # 分析結果をDBに保存（AI要約はクリアして再生成を促す）
    cache = _get_or_create_cache(db, user.id)
    cache.analysis_result = response.model_dump()
    cache.ai_summary = None
    cache.skill_activity_month = None
    cache.skill_activity_year = None
    db.commit()

    return response


@router.post("/summarize", response_model=SummarizeResponse)
@limiter.limit("10/minute")
async def summarize(
    request: Request,
    payload: SummarizeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ollama を使用して分析結果の自然言語要約を生成します。
    結果はDBに保存され、次回以降はキャッシュから取得可能です。

    Ollama サーバーに接続できない場合は available: false を返します。
    """
    available = await check_llm_available()
    if not available:
        return SummarizeResponse(summary="", available=False)

    analysis_dict = payload.analysis.model_dump()
    summary = await summarize_analysis(analysis_dict)
    if not summary:
        return SummarizeResponse(summary="", available=False)

    # AI要約をDBに保存
    cache = _get_or_create_cache(db, user.id)
    cache.ai_summary = summary
    db.commit()

    return SummarizeResponse(summary=summary, available=True)


@router.post("/skill-activity", response_model=SkillActivityResponse)
@limiter.limit("10/minute")
async def skill_activity(
    request: Request,
    interval: Literal["month", "year"] = "month",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    スキルアクティビティ（コミット数）を取得し、時系列で集計します。
    結果はDBに保存され、次回以降はキャッシュから取得可能です。
    GitHub OAuth ログインが必要です。
    """
    if not user.username.startswith("github:"):
        raise HTTPException(
            status_code=403,
            detail="GitHub分析にはGitHubアカウントでのログインが必要です",
        )

    github_username = user.username.removeprefix("github:")
    token = decrypt_field(user.github_token) if user.github_token else None

    try:
        results = await get_skill_activity(
            username=github_username,
            token=token,
            interval=interval,  # type: ignore
        )
    except Exception:
        logger.exception("%s のスキルアクティビティ分析に失敗しました", github_username)
        raise HTTPException(
            status_code=502,
            detail="GitHubアクティビティの分析に失敗しました。",
        )

    # スキルアクティビティをDBに保存
    cache = _get_or_create_cache(db, user.id)
    activity_data = [item.model_dump() if hasattr(item, "model_dump") else item for item in results]
    if interval == "year":
        cache.skill_activity_year = activity_data
    else:
        cache.skill_activity_month = activity_data
    db.commit()

    return SkillActivityResponse(skills=results)
