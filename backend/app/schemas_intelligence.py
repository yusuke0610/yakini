"""キャリアインテリジェンス API 用の Pydantic スキーマ。"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ── リクエスト ─────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    include_forks: bool = Field(
        False,
        description="分析にフォークしたリポジトリを含めるかどうか",
    )


# ── スキルタイムライン ─────────────────────────────────────────────────────

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


# ── スキル成長 ────────────────────────────────────────────────────────

class SkillGrowthItem(BaseModel):
    skill_name: str
    category: str
    trend: str  # "emerging", "stable", "declining", "new"
    velocity: float
    yearly_usage: Dict[str, int]
    first_seen: str
    last_seen: str
    total_repos: int


# ── キャリア予測 ───────────────────────────────────────────────────

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


# ── キャリアシミュレーション ───────────────────────────────────────────────────

class SimulatedPathItem(BaseModel):
    path: List[str]
    confidence: float
    description: str


class CareerSimulationResponse(BaseModel):
    current_role: str
    paths: List[SimulatedPathItem]
    total_paths_explored: int


# ── 全分析レスポンス ──────────────────────────────────────────────

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


# ── 要約 (Ollama) ────────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    analysis: AnalysisResponse


class SummarizeResponse(BaseModel):
    summary: str = Field("", description="LLM による自然言語の要約")
    available: bool = Field(
        True,
        description="LLM サービスが利用可能かどうか",
    )


class DownloadRequest(BaseModel):
    analysis: AnalysisResponse
    summary: Optional[str] = Field(
        None,
        description="レポートに含める AI 要約テキスト",
    )


# ── スキルアクティビティ ─────────────────────────────────────────────────────

class SkillTimelinePoint(BaseModel):
    period: str
    activity: int


class SkillActivityItem(BaseModel):
    skill: str
    timeline: List[SkillTimelinePoint]


class SkillActivityResponse(BaseModel):
    skills: List[SkillActivityItem]
