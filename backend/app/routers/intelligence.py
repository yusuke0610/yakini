"""
Career intelligence API endpoints.

POST /api/intelligence/analyze — run the full analysis pipeline.
POST /api/intelligence/download/pdf — generate PDF from analysis data.
POST /api/intelligence/download/markdown — generate Markdown from analysis data.
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
    DownloadRequest,
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
from ..services.markdown.generators.intelligence_generator import (
    build_intelligence_markdown,
)
from ..services.pdf.generators.intelligence_generator import build_intelligence_pdf
from .download_utils import stream_markdown, stream_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    request: AnalyzeRequest,
    user: User = Depends(get_current_user),
):
    """
    Run the full career intelligence pipeline for the logged-in GitHub user.

    Stages: GitHub collection → Skill extraction → Timeline →
    Growth analysis → Career prediction → Career simulation.

    All stages are deterministic (no LLM).
    Requires GitHub OAuth login (username format: "github:{login}").
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
            "Intelligence pipeline timed out for %s",
            github_username,
        )
        raise HTTPException(
            status_code=504,
            detail="分析がタイムアウトしました。しばらくしてから再度お試しください。",
        )
    except Exception:
        logger.exception(
            "Intelligence pipeline failed for %s",
            github_username,
        )
        raise HTTPException(
            status_code=502,
            detail="GitHubプロフィールの分析に失敗しました。しばらくしてから再度お試しください。",
        )

    return map_pipeline_result(result)


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """
    Generate a natural language summary of analysis results using Ollama.

    Returns ``available: false`` when the Ollama server is not reachable,
    allowing the frontend to gracefully hide the summary section.
    """
    available = await check_ollama_available()
    if not available:
        return SummarizeResponse(summary="", available=False)

    analysis_dict = request.analysis.model_dump()
    summary = await summarize_analysis(analysis_dict)
    return SummarizeResponse(summary=summary, available=True)


@router.post("/download/pdf")
async def download_pdf(
    request: DownloadRequest,
    user: User = Depends(get_current_user),
):
    """Generate a PDF report from the analysis data."""
    payload = request.analysis.model_dump()
    if request.summary:
        payload["summary"] = request.summary

    pdf_bytes = build_intelligence_pdf(payload)
    username = payload.get("username", "analysis")
    return stream_pdf(pdf_bytes, f"github-analysis-{username}.pdf")


@router.post("/download/markdown")
async def download_markdown(
    request: DownloadRequest,
    user: User = Depends(get_current_user),
):
    """Generate a Markdown report from the analysis data."""
    payload = request.analysis.model_dump()
    if request.summary:
        payload["summary"] = request.summary

    md_text = build_intelligence_markdown(payload)
    username = payload.get("username", "analysis")
    return stream_markdown(md_text, f"github-analysis-{username}.md")
