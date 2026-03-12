from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GitHubCallbackRequest(BaseModel):
    code: str = Field(min_length=1)


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
    category: Literal["言語", "フレームワーク", "OS", "DB", "クラウドリソース", "開発支援ツール"]
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
