from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Experience(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=120)
    start_date: str = Field(min_length=1, max_length=30)
    end_date: str = Field(min_length=1, max_length=30)
    description: str = Field(min_length=1, max_length=1500)


class Education(BaseModel):
    school: str = Field(min_length=1, max_length=120)
    degree: str = Field(min_length=1, max_length=120)
    start_date: str = Field(min_length=1, max_length=30)
    end_date: str = Field(min_length=1, max_length=30)


class ResumeBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=1, max_length=50)
    summary: str = Field(min_length=1, max_length=2000)
    experiences: list[Experience] = Field(default_factory=list)
    educations: list[Education] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class ResumeCreate(ResumeBase):
    pass


class ResumeUpdate(ResumeBase):
    pass


class ResumeResponse(ResumeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
