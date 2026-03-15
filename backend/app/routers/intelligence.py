"""
キャリアインテリジェンス API エンドポイント。

POST /api/intelligence/analyze — 全分析パイプラインを実行。
POST /api/intelligence/skill-activity — スキルアクティビティを集計。
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..encryption import decrypt_field
from ..models import User
from ..schemas_intelligence import (
    AnalysisResponse,
    AnalyzeRequest,
    SkillActivityResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from ..services.intelligence.github_collector import (
    GitHubUserNotFoundError,
)
from ..services.intelligence.llm_summarizer import (
    check_ollama_available,
    summarize_analysis,
)
from ..services.intelligence.pipeline import run_pipeline
from ..services.intelligence.response_mapper import map_pipeline_result
from ..services.intelligence.skill_activity_analyzer import get_skill_activity
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    request: AnalyzeRequest,
    user: User = Depends(get_current_user),
):
    """
    ログイン中の GitHub ユーザーに対して全キャリアインテリジェンスパイプラインを実行します。

    ステージ: GitHub データ収集 → スキル抽出 → タイムライン生成 →
    成長分析 → キャリア予測 → キャリアシミュレーション。

    すべてのステージは決定的です（LLM 不使用）。
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
                token=decrypt_field(user.github_token) if user.github_token else None,
                include_forks=request.include_forks,
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
            detail="GitHubプロフィールの分析に失敗しました。しばらくしてから再度お試しください。",
        )

    return map_pipeline_result(result)


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    user: User = Depends(get_current_user),
):
    """
    Ollama を使用して分析結果の自然言語要約を生成します。

    Ollama サーバーに接続できない場合は available: false を返します。
    これによりフロントエンドで要約セクションを適切に非表示にできます。
    """
    available = await check_ollama_available()
    if not available:
        return SummarizeResponse(summary="", available=False)

    analysis_dict = request.analysis.model_dump()
    summary = await summarize_analysis(analysis_dict)
    return SummarizeResponse(summary=summary, available=True)


@router.post("/skill-activity", response_model=SkillActivityResponse)
async def skill_activity(
    interval: str = "month",
    user: User = Depends(get_current_user),
):
    """
    スキルアクティビティ（コミット数）を取得し、時系列で集計します。
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
        return SkillActivityResponse(skills=results)
    except Exception:
        logger.exception("%s のスキルアクティビティ分析に失敗しました", github_username)
        raise HTTPException(
            status_code=502,
            detail="GitHubアクティビティの分析に失敗しました。",
        )
