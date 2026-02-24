from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import BasicInfo, Resume, Rirekisho


class BasicInfoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict[str, Any]) -> BasicInfo:
        basic_info = BasicInfo(**payload)
        self.db.add(basic_info)
        self.db.commit()
        self.db.refresh(basic_info)
        return basic_info

    def get_latest(self) -> BasicInfo | None:
        statement = select(BasicInfo).order_by(BasicInfo.updated_at.desc()).limit(1)
        return self.db.scalar(statement)

    def get_by_id(self, basic_info_id: str) -> BasicInfo | None:
        return self.db.get(BasicInfo, basic_info_id)

    def update(self, basic_info: BasicInfo, payload: dict[str, Any]) -> BasicInfo:
        for field, value in payload.items():
            setattr(basic_info, field, value)

        self.db.commit()
        self.db.refresh(basic_info)
        return basic_info


class ResumeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict[str, Any]) -> Resume:
        resume = Resume(**payload)
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get_by_id(self, resume_id: str) -> Resume | None:
        return self.db.get(Resume, resume_id)

    def update(self, resume: Resume, payload: dict[str, Any]) -> Resume:
        for field, value in payload.items():
            setattr(resume, field, value)

        self.db.commit()
        self.db.refresh(resume)
        return resume


class RirekishoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict[str, Any]) -> Rirekisho:
        rirekisho = Rirekisho(**payload)
        self.db.add(rirekisho)
        self.db.commit()
        self.db.refresh(rirekisho)
        return rirekisho

    def get_by_id(self, rirekisho_id: str) -> Rirekisho | None:
        return self.db.get(Rirekisho, rirekisho_id)

    def update(self, rirekisho: Rirekisho, payload: dict[str, Any]) -> Rirekisho:
        for field, value in payload.items():
            setattr(rirekisho, field, value)

        self.db.commit()
        self.db.refresh(rirekisho)
        return rirekisho
