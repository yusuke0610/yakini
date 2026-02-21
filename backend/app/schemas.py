from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class Experience(BaseModel):
    class TechnologyStackItem(BaseModel):
        category: Literal["言語", "OS", "DB", "クラウドリソース", "開発支援ツール"]
        name: str = Field(min_length=1, max_length=120)

    company: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=120)
    start_date: str = Field(min_length=1, max_length=30)
    end_date: str | None = Field(default=None, max_length=30)
    is_current: bool = False
    description: str = Field(min_length=1, max_length=1500)
    achievements: str = Field(min_length=1, max_length=1500)
    employee_count: str = Field(min_length=1, max_length=60)
    capital: str = Field(min_length=1, max_length=120)
    technology_stacks: list[TechnologyStackItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_end_date(self) -> "Experience":
        if self.is_current:
            self.end_date = None
            return self
        if not self.end_date or not self.end_date.strip():
            raise ValueError("end_date is required when is_current is false")
        return self


class ResumeBase(BaseModel):
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
