from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BlogAccountCreate(BaseModel):
    """ブログ連携アカウントの作成リクエスト。"""

    platform: Literal["zenn", "note", "qiita"]
    username: str = Field(min_length=1, max_length=120)


class BlogAccountResponse(BaseModel):
    """ブログ連携アカウントのレスポンス。"""

    id: UUID
    platform: str
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlogArticleResponse(BaseModel):
    """ブログ記事のレスポンス。"""

    id: UUID
    platform: str
    title: str
    url: str
    published_at: str | None = None
    likes_count: int = 0
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BlogSyncResponse(BaseModel):
    """ブログ同期結果のレスポンス。"""

    synced_count: int
    total_count: int


class BlogSummaryArticle(BaseModel):
    """ブログ AI 分析に渡す記事情報。"""

    platform: Literal["zenn", "note", "qiita"]
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=1000)
    published_at: str | None = Field(default=None, max_length=30)
    likes_count: int = Field(default=0, ge=0, le=1_000_000)
    summary: str | None = Field(default=None, max_length=1000)
    tags: list[str] = Field(default_factory=list, max_length=20)


class BlogSummaryRequest(BaseModel):
    """ブログ記事 AI 分析リクエスト。"""

    articles: list[BlogSummaryArticle] = Field(min_length=1, max_length=50)


class BlogSummaryResponse(BaseModel):
    """ブログ記事 AI 分析レスポンス。"""

    summary: str
    available: bool
    status: str | None = None
    error_message: str | None = None
    error_code: str | None = None


class BlogScoreArticleResponse(BaseModel):
    """技術記事判定結果付きの記事情報。"""

    id: str
    title: str
    url: str
    published_at: str | None = None
    likes_count: int = 0
    tags: list[str] = Field(default_factory=list)
    is_tech: bool = False


class BlogScoreResponse(BaseModel):
    """ブログ統計サマリのレスポンス。"""

    tech_article_count: int = 0
    total_article_count: int = 0
    avg_monthly_posts: float = 0.0
    avg_likes: float = 0.0
    articles: list[BlogScoreArticleResponse] = Field(default_factory=list)
