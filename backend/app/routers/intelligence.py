"""
Career intelligence API endpoints.

POST /api/intelligence/analyze — run the full analysis pipeline.
"""

import logging

from fastapi import APIRouter, HTTPException

from ..schemas_intelligence import (
    AnalysisResponse,
    AnalyzeRequest,
    CareerPredictionResponse,
    CareerSimulationResponse,
    PredictedRoleItem,
    SimulatedPathItem,
    SkillGrowthItem,
    SkillTimelineItem,
    SummarizeRequest,
    SummarizeResponse,
    YearSnapshotItem,
)
from ..services.intelligence.github_collector import (
    GitHubUserNotFoundError,
)
from ..services.intelligence.llm_summarizer import (
    check_ollama_available,
    summarize_analysis,
)
from ..services.intelligence.pipeline import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalyzeRequest):
    """
    Run the full career intelligence pipeline for a GitHub user.

    Stages: GitHub collection → Skill extraction → Timeline →
    Growth analysis → Career prediction → Career simulation.

    All stages are deterministic (no LLM).
    """
    try:
        result = await run_pipeline(
            username=request.github_username,
            token=request.github_token,
            include_forks=request.include_forks,
        )
    except GitHubUserNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"GitHub user not found: {request.github_username}",
        )
    except Exception:
        logger.exception(
            "Intelligence pipeline failed for %s",
            request.github_username,
        )
        raise HTTPException(
            status_code=502,
            detail="Failed to analyze GitHub profile. Please try again later.",
        )

    # Convert dataclasses to Pydantic response
    return AnalysisResponse(
        username=result.username,
        repos_analyzed=result.repos_analyzed,
        unique_skills=result.unique_skills,
        timelines=[
            SkillTimelineItem(
                skill_name=t.skill_name,
                category=t.category,
                first_seen=t.first_seen,
                last_seen=t.last_seen,
                usage_frequency=t.usage_frequency,
                repositories=t.repositories,
                yearly_usage=t.yearly_usage,
            )
            for t in result.timelines
        ],
        year_snapshots=[
            YearSnapshotItem(
                year=s.year,
                skills=s.skills,
                new_skills=s.new_skills,
            )
            for s in result.year_snapshots
        ],
        growth=[
            SkillGrowthItem(
                skill_name=g.skill_name,
                category=g.category,
                trend=g.trend.value,
                velocity=g.velocity,
                yearly_usage=g.yearly_usage,
                first_seen=g.first_seen,
                last_seen=g.last_seen,
                total_repos=g.total_repos,
            )
            for g in result.growth
        ],
        prediction=CareerPredictionResponse(
            current_role=PredictedRoleItem(
                role_name=result.prediction.current_role.role_name,
                confidence=result.prediction.current_role.confidence,
                matching_skills=result.prediction.current_role.matching_skills,
                missing_skills=result.prediction.current_role.missing_skills,
                seniority=result.prediction.current_role.seniority,
            ),
            next_roles=[
                PredictedRoleItem(
                    role_name=r.role_name,
                    confidence=r.confidence,
                    matching_skills=r.matching_skills,
                    missing_skills=r.missing_skills,
                    seniority=r.seniority,
                )
                for r in result.prediction.next_roles
            ],
            long_term_roles=[
                PredictedRoleItem(
                    role_name=r.role_name,
                    confidence=r.confidence,
                    matching_skills=r.matching_skills,
                    missing_skills=r.missing_skills,
                    seniority=r.seniority,
                )
                for r in result.prediction.long_term_roles
            ],
            skill_summary=result.prediction.skill_summary,
        ),
        simulation=CareerSimulationResponse(
            current_role=result.simulation.current_role,
            paths=[
                SimulatedPathItem(
                    path=p.path,
                    confidence=p.confidence,
                    description=p.description,
                )
                for p in result.simulation.paths
            ],
            total_paths_explored=result.simulation.total_paths_explored,
        ),
        analyzed_at=result.analyzed_at,
    )


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
