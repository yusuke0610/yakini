"""キャリアインテリジェンス API 用の Pydantic スキーマ。"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    include_forks: bool = Field(
        False,
        description="分析にフォークしたリポジトリを含めるかどうか",
    )


class PositionScoresResponse(BaseModel):
    """5軸のエンジニアポジションスコア。"""

    backend: int = Field(0, description="バックエンド適性スコア (0-100)")
    frontend: int = Field(0, description="フロントエンド適性スコア (0-100)")
    fullstack: int = Field(0, description="フルスタック適性スコア (0-100)")
    sre: int = Field(0, description="SRE適性スコア (0-100)")
    cloud: int = Field(0, description="クラウド適性スコア (0-100)")
    missing_skills: List[str] = Field(
        default_factory=list,
        description="フルスタックエンジニアに不足しているスキル",
    )


class AnalysisResponse(BaseModel):
    username: str
    repos_analyzed: int
    unique_skills: int
    analyzed_at: str
    languages: Dict[str, int] = Field(
        default_factory=dict,
        description="言語ごとのバイト数（GitHub linguist ベース）",
    )
    position_scores: Optional[PositionScoresResponse] = Field(
        None,
        description="エンジニアポジションスコア（5軸）",
    )


class PositionAdviceResponse(BaseModel):
    """現状分析+学習アドバイス。"""

    advice: str = Field("", description="LLM による現状分析と学習アドバイス")
    available: bool = Field(True, description="LLM サービスが利用可能かどうか")


class CachedAnalysisResponse(BaseModel):
    """DB に保存された分析結果・学習アドバイスを返す。"""

    analysis_result: Optional[Dict[str, Any]] = None
    position_advice: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
