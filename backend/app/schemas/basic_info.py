from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .shared import _HIRAGANA_PATTERN


class BasicQualification(BaseModel):
    acquired_date: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)

    model_config = ConfigDict(from_attributes=True)


class BasicInfoBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    name_furigana: str = Field(min_length=1, max_length=200, pattern=_HIRAGANA_PATTERN)
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
