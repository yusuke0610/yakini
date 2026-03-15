from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)

    @model_validator(mode="after")
    def _validate_password_complexity(self) -> "RegisterRequest":
        """パスワードに英大文字・英小文字・数字をそれぞれ1文字以上含むことを検証する。"""
        p = self.password
        if not any(c.isupper() for c in p):
            raise ValueError("パスワードには英大文字を1文字以上含めてください")
        if not any(c.islower() for c in p):
            raise ValueError("パスワードには英小文字を1文字以上含めてください")
        if not any(c.isdigit() for c in p):
            raise ValueError("パスワードには数字を1文字以上含めてください")
        return self


class TokenResponse(BaseModel):
    username: str
    is_github_user: bool = False


class UserResponse(BaseModel):
    username: str
    email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GitHubCallbackRequest(BaseModel):
    code: str = Field(min_length=1)
    state: str = Field(min_length=1)


class BasicQualification(BaseModel):
    acquired_date: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)


class BasicInfoBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    record_date: str = Field(min_length=1, max_length=30)
    qualifications: list[BasicQualification] = Field(default_factory=list)


class BasicInfoCreate(BasicInfoBase):
    pass


class BasicInfoUpdate(BasicInfoBase):
    pass


class BasicInfoResponse(BasicInfoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TechnologyStackItem(BaseModel):
    category: Literal["language", "framework", "os", "db", "cloud_resource", "dev_tool"]
    name: str = Field(min_length=1, max_length=120)


class Project(BaseModel):
    name: str = Field(max_length=200, default="")
    role: str = Field(max_length=200, default="")
    description: str = Field(max_length=1500, default="")
    achievements: str = Field(max_length=1500, default="")
    scale: str = Field(max_length=60, default="")
    technology_stacks: list[TechnologyStackItem] = Field(default_factory=list)


class Experience(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    business_description: str = Field(min_length=1, max_length=200)
    start_date: str = Field(min_length=1, max_length=30)
    end_date: str | None = Field(default=None, max_length=30)
    is_current: bool = False
    employee_count: str = Field(max_length=60, default="")
    capital: str = Field(max_length=120, default="")
    projects: list[Project] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_end_date(self) -> "Experience":
        if self.is_current:
            self.end_date = None
            return self
        if not self.end_date or not self.end_date.strip():
            raise ValueError("end_date is required when is_current is false")
        return self


class ResumeBase(BaseModel):
    career_summary: str = Field(min_length=1, max_length=2000)
    self_pr: str = Field(min_length=1, max_length=2000)
    experiences: list[Experience] = Field(default_factory=list)


class ResumeCreate(ResumeBase):
    pass


class ResumeUpdate(ResumeBase):
    pass


class ResumeResponse(ResumeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RirekishoHistory(BaseModel):
    date: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=300)


class RirekishoBase(BaseModel):
    postal_code: str = Field(min_length=1, max_length=20)
    prefecture: str = Field(min_length=1, max_length=60)
    address: str = Field(min_length=1, max_length=400)
    email: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=50)
    motivation: str = Field(min_length=1, max_length=2000)
    personal_preferences: str = Field(max_length=2000, default="")
    photo: str | None = Field(default=None)
    educations: list[RirekishoHistory] = Field(default_factory=list)
    work_histories: list[RirekishoHistory] = Field(default_factory=list)


class RirekishoCreate(RirekishoBase):
    pass


class RirekishoUpdate(RirekishoBase):
    pass


class RirekishoResponse(RirekishoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlogAccountCreate(BaseModel):
    """ブログ連携アカウントの作成リクエスト。"""
    platform: Literal["zenn", "note"]
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


class BlogSummaryRequest(BaseModel):
    """ブログ記事 AI 分析リクエスト。"""
    articles: list[BlogArticleResponse]


class BlogSummaryResponse(BaseModel):
    """ブログ記事 AI 分析レスポンス。"""
    summary: str
    available: bool


class MasterItem(BaseModel):
    """マスタデータ共通レスポンス（資格・都道府県）。"""
    id: UUID
    name: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class MasterItemCreate(BaseModel):
    """マスタデータ共通の作成リクエスト（資格・都道府県）。"""
    name: str = Field(min_length=1, max_length=200)
    sort_order: int = Field(default=0)


class MasterItemUpdate(BaseModel):
    """マスタデータ共通の更新リクエスト（資格・都道府県）。"""
    name: str = Field(min_length=1, max_length=200)
    sort_order: int = Field(default=0)


class TechStackMasterItem(BaseModel):
    """技術スタックマスタのレスポンス。"""
    id: UUID
    category: str
    name: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class TechStackMasterCreate(BaseModel):
    """技術スタックマスタの作成リクエスト。"""
    category: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=200)
    sort_order: int = Field(default=0)


class TechStackMasterUpdate(BaseModel):
    """技術スタックマスタの更新リクエスト。"""
    category: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=200)
    sort_order: int = Field(default=0)
