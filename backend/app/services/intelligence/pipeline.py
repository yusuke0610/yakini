"""
Career intelligence pipeline orchestrator.

Runs the full analysis pipeline:
  GitHub → Repos → Skills → Timeline → Growth → Prediction → Simulation

Each stage is deterministic except optional LLM summarization.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .career_predictor import CareerPrediction, predict_career
from .career_simulator import CareerSimulation, simulate_careers
from .github_collector import collect_repos, RepoData
from .skill_extractor import ExtractionResult, extract_skills
from .skill_growth_analyzer import SkillGrowth, analyze_growth
from .skill_timeline_builder import (
    SkillTimeline,
    YearSnapshot,
    build_timeline,
    build_year_snapshots,
)

logger = logging.getLogger(__name__)


@dataclass
class IntelligenceResult:
    username: str
    repos_analyzed: int
    unique_skills: int
    timelines: List[SkillTimeline]
    year_snapshots: List[YearSnapshot]
    growth: List[SkillGrowth]
    prediction: CareerPrediction
    simulation: CareerSimulation
    analyzed_at: str


async def run_pipeline(
    username: str,
    token: Optional[str] = None,
    include_forks: bool = False,
) -> IntelligenceResult:
    """
    Run the full career intelligence pipeline for a GitHub user.

    Pipeline stages:
      1. Collect repos from GitHub API
      2. Extract skills (deterministic)
      3. Build skill timeline
      4. Analyze growth velocity
      5. Predict career path
      6. Simulate career branches
    """
    logger.info("Starting intelligence pipeline for %s", username)

    # Stage 1: Collect GitHub data
    repos: List[RepoData] = await collect_repos(
        username, token=token, include_forks=include_forks,
    )

    # Stage 2: Extract skills
    extraction: ExtractionResult = extract_skills(repos)

    # Stage 3: Build timeline
    timelines: List[SkillTimeline] = build_timeline(extraction)
    snapshots: List[YearSnapshot] = build_year_snapshots(timelines)

    # Stage 4: Analyze growth
    current_year = str(datetime.now().year)
    growth: List[SkillGrowth] = analyze_growth(
        timelines, current_year=current_year,
    )

    # Stage 5: Predict career
    prediction: CareerPrediction = predict_career(timelines, growth)

    # Stage 6: Simulate paths
    simulation: CareerSimulation = simulate_careers(
        prediction, timelines, growth,
    )

    logger.info(
        "Pipeline complete for %s: %d skills, current=%s, %d paths",
        username,
        len(extraction.unique_skills),
        prediction.current_role.role_name,
        len(simulation.paths),
    )

    return IntelligenceResult(
        username=username,
        repos_analyzed=extraction.repos_analyzed,
        unique_skills=len(extraction.unique_skills),
        timelines=timelines,
        year_snapshots=snapshots,
        growth=growth,
        prediction=prediction,
        simulation=simulation,
        analyzed_at=datetime.now().isoformat(),
    )
