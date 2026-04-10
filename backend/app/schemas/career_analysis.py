"""AI キャリアパス分析のリクエスト/レスポンススキーマ。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TechStackItem(BaseModel):
    """技術スタック1件。"""

    name: str
    priority: int  # 1〜3
    source: str  # "案件実績" | "個人開発" | "資格"
    note: str | None = None


class TechStackSection(BaseModel):
    """技術スタック評価セクション。"""

    top: list[TechStackItem]
    summary: str


class StrengthItem(BaseModel):
    """強み1件（根拠付き）。"""

    title: str
    detail: str
    evidence_source: str  # "resume" | "github" | "blog" | "basic_info"


class CareerPathItem(BaseModel):
    """キャリアパス提案1件。"""

    horizon: str  # "short" | "mid" | "long"
    label: str
    title: str
    description: str
    required_skills: list[str]
    gap_skills: list[str]
    fit_score: int  # 0〜100


class ActionItem(BaseModel):
    """アクションアイテム1件。"""

    priority: int
    action: str
    reason: str


class CareerAnalysisResult(BaseModel):
    """キャリアパス分析の全セクション。"""

    growth_summary: str
    tech_stack: TechStackSection
    strengths: list[StrengthItem]
    career_paths: list[CareerPathItem]  # short/mid/long の 3件
    action_items: list[ActionItem]


class CareerAnalysisGenerateRequest(BaseModel):
    """キャリアパス分析の生成リクエスト。"""

    target_position: str = Field(max_length=200)


class CareerAnalysisResponse(BaseModel):
    """キャリアパス分析のレスポンス。"""

    id: int
    version: int
    target_position: str
    result: CareerAnalysisResult | None = None
    status: str = "completed"
    error_message: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskStatusResponse(BaseModel):
    """タスクステータスの軽量レスポンス。"""

    status: str
    error_message: str | None = None
    error_code: str | None = None
