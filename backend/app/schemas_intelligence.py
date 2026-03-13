"""Pydantic schemas for the career intelligence API."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ── Request ─────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    github_username: str = Field(
        ..., min_length=1, max_length=39,
        description="GitHub username to analyze",
    )
    github_token: Optional[str] = Field(
        None,
        description="Optional GitHub token for private repos / higher rate limits",
    )
    include_forks: bool = Field(
        False,
        description="Include forked repositories in analysis",
    )


# ── Skill Timeline ─────────────────────────────────────────────────────

class SkillTimelineItem(BaseModel):
    skill_name: str
    category: str
    first_seen: str
    last_seen: str
    usage_frequency: int
    repositories: List[str]
    yearly_usage: Dict[str, int]


class YearSnapshotItem(BaseModel):
    year: str
    skills: List[str]
    new_skills: List[str]


# ── Skill Growth ────────────────────────────────────────────────────────

class SkillGrowthItem(BaseModel):
    skill_name: str
    category: str
    trend: str  # "emerging", "stable", "declining", "new"
    velocity: float
    yearly_usage: Dict[str, int]
    first_seen: str
    last_seen: str
    total_repos: int


# ── Career Prediction ───────────────────────────────────────────────────

class PredictedRoleItem(BaseModel):
    role_name: str
    confidence: float
    matching_skills: List[str]
    missing_skills: List[str]
    seniority: int


class CareerPredictionResponse(BaseModel):
    current_role: PredictedRoleItem
    next_roles: List[PredictedRoleItem]
    long_term_roles: List[PredictedRoleItem]
    skill_summary: Dict[str, List[str]]


# ── Career Simulation ───────────────────────────────────────────────────

class SimulatedPathItem(BaseModel):
    path: List[str]
    confidence: float
    description: str


class CareerSimulationResponse(BaseModel):
    current_role: str
    paths: List[SimulatedPathItem]
    total_paths_explored: int


# ── Full Analysis Response ──────────────────────────────────────────────

class AnalysisResponse(BaseModel):
    username: str
    repos_analyzed: int
    unique_skills: int
    timelines: List[SkillTimelineItem]
    year_snapshots: List[YearSnapshotItem]
    growth: List[SkillGrowthItem]
    prediction: CareerPredictionResponse
    simulation: CareerSimulationResponse
    analyzed_at: str


# ── Summarize (Ollama) ────────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    analysis: AnalysisResponse


class SummarizeResponse(BaseModel):
    summary: str = Field("", description="Natural language summary from LLM")
    available: bool = Field(
        True,
        description="Whether the LLM service is available",
    )
