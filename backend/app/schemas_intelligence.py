"""キャリアインテリジェンス API 用の Pydantic スキーマ。"""

from typing import Dict, List

from pydantic import BaseModel, Field


# ── リクエスト ─────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    include_forks: bool = Field(
        False,
        description="分析にフォークしたリポジトリを含めるかどうか",
    )


# ── 全分析レスポンス ──────────────────────────────────────────────

class AnalysisResponse(BaseModel):
    username: str
    repos_analyzed: int
    unique_skills: int
    analyzed_at: str
    languages: Dict[str, int] = Field(
        default_factory=dict,
        description="言語ごとのバイト数（GitHub linguist ベース）",
    )


# ── 要約 (Ollama) ────────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    analysis: AnalysisResponse


class SummarizeResponse(BaseModel):
    summary: str = Field("", description="LLM による自然言語の要約")
    available: bool = Field(
        True,
        description="LLM サービスが利用可能かどうか",
    )


# ── スキルアクティビティ ─────────────────────────────────────────────────────

class SkillTimelinePoint(BaseModel):
    period: str
    activity: float


class SkillActivityItem(BaseModel):
    skill: str
    timeline: List[SkillTimelinePoint]


class SkillActivityResponse(BaseModel):
    skills: List[SkillActivityItem]
