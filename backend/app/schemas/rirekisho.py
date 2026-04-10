from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .shared import _HIRAGANA_PATTERN


class RirekishoHistory(BaseModel):
    date: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=300)

    model_config = ConfigDict(from_attributes=True)


class RirekishoBase(BaseModel):
    gender: Literal["male", "female"] = Field(min_length=1)
    birthday: str = Field(min_length=1, max_length=20)
    postal_code: str = Field(min_length=1, max_length=20)
    prefecture: str = Field(min_length=1, max_length=60)
    address: str = Field(min_length=1, max_length=400)
    address_furigana: str = Field(min_length=1, max_length=400, pattern=_HIRAGANA_PATTERN)
    email: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=50)
    motivation: str = Field(max_length=2000, default="")
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
    gender: str = ""
    birthday: str = ""
    address_furigana: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
