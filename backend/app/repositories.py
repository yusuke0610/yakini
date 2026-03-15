import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .encryption import decrypt_field, encrypt_field
from .models import BasicInfo, MasterData, Resume, Rirekisho, User

_ENCRYPTED_RIREKISHO_FIELDS = {"email", "phone", "postal_code", "address"}


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, username: str, hashed_password: str, email: str | None = None) -> User:
        user = User(username=username, hashed_password=hashed_password, email=email)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return self.db.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.scalar(statement)

    def get_by_github_id(self, github_id: int) -> User | None:
        statement = select(User).where(User.github_id == github_id)
        return self.db.scalar(statement)

    def create_github_user(self, username: str, github_id: int) -> User:
        user = User(username=username, hashed_password="", github_id=github_id)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def count(self) -> int:
        statement = select(func.count()).select_from(User)
        return self.db.scalar(statement) or 0


class BasicInfoRepository:
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def create(self, payload: dict[str, Any]) -> BasicInfo:
        basic_info = BasicInfo(**payload, user_id=self.user_id)
        self.db.add(basic_info)
        self.db.commit()
        self.db.refresh(basic_info)
        return basic_info

    def get_latest(self) -> BasicInfo | None:
        statement = (
            select(BasicInfo)
            .where(BasicInfo.user_id == self.user_id)
            .order_by(BasicInfo.updated_at.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def get_by_id(self, basic_info_id: str) -> BasicInfo | None:
        statement = (
            select(BasicInfo)
            .where(BasicInfo.id == basic_info_id)
            .where(BasicInfo.user_id == self.user_id)
        )
        return self.db.scalar(statement)

    def update(
        self, basic_info: BasicInfo, payload: dict[str, Any]
    ) -> BasicInfo:
        for field, value in payload.items():
            setattr(basic_info, field, value)

        self.db.commit()
        self.db.refresh(basic_info)
        return basic_info


class ResumeRepository:
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def create(self, payload: dict[str, Any]) -> Resume:
        resume = Resume(**payload, user_id=self.user_id)
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get_latest(self) -> Resume | None:
        statement = (
            select(Resume)
            .where(Resume.user_id == self.user_id)
            .order_by(Resume.updated_at.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def get_by_id(self, resume_id: str) -> Resume | None:
        statement = (
            select(Resume)
            .where(Resume.id == resume_id)
            .where(Resume.user_id == self.user_id)
        )
        return self.db.scalar(statement)

    def update(self, resume: Resume, payload: dict[str, Any]) -> Resume:
        for field, value in payload.items():
            setattr(resume, field, value)

        self.db.commit()
        self.db.refresh(resume)
        return resume


class RirekishoRepository:
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def _encrypt_payload(
        self, payload: dict[str, Any]
    ) -> dict[str, Any]:
        result = dict(payload)
        for field in _ENCRYPTED_RIREKISHO_FIELDS:
            if field in result and isinstance(result[field], str):
                result[field] = encrypt_field(result[field])
        return result

    def _decrypt_rirekisho(self, rirekisho: Rirekisho) -> None:
        for field in _ENCRYPTED_RIREKISHO_FIELDS:
            value = getattr(rirekisho, field, None)
            if isinstance(value, str):
                try:
                    setattr(rirekisho, field, decrypt_field(value))
                except Exception:
                    logging.warning("Failed to decrypt field %s, returning raw value", field, exc_info=True)

    def create(self, payload: dict[str, Any]) -> Rirekisho:
        rirekisho = Rirekisho(**self._encrypt_payload(payload), user_id=self.user_id)
        self.db.add(rirekisho)
        self.db.commit()
        self.db.refresh(rirekisho)
        self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def get_latest(self) -> Rirekisho | None:
        statement = (
            select(Rirekisho)
            .where(Rirekisho.user_id == self.user_id)
            .order_by(Rirekisho.updated_at.desc())
            .limit(1)
        )
        rirekisho = self.db.scalar(statement)
        if rirekisho:
            self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def get_by_id(self, rirekisho_id: str) -> Rirekisho | None:
        statement = (
            select(Rirekisho)
            .where(Rirekisho.id == rirekisho_id)
            .where(Rirekisho.user_id == self.user_id)
        )
        rirekisho = self.db.scalar(statement)
        if rirekisho:
            self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def update(
        self, rirekisho: Rirekisho, payload: dict[str, Any]
    ) -> Rirekisho:
        for field, value in self._encrypt_payload(payload).items():
            setattr(rirekisho, field, value)

        self.db.commit()
        self.db.refresh(rirekisho)
        self._decrypt_rirekisho(rirekisho)
        return rirekisho


class MasterDataRepository:
    """マスタデータの永続化操作を管理するリポジトリ。"""

    def __init__(self, db: Session):
        self.db = db

    def list_by_category(self, category: str) -> list[MasterData]:
        """カテゴリ別にマスタデータを取得する。"""
        statement = (
            select(MasterData)
            .where(MasterData.category == category)
            .order_by(MasterData.sort_order, MasterData.name)
        )
        return list(self.db.scalars(statement).all())

    def create(self, category: str, name: str, sort_order: int = 0) -> MasterData:
        """マスタデータを作成する。"""
        item = MasterData(category=category, name=name, sort_order=sort_order)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item_id: str, name: str, sort_order: int = 0) -> MasterData | None:
        """マスタデータを更新する。"""
        statement = select(MasterData).where(MasterData.id == item_id)
        item = self.db.scalar(statement)
        if not item:
            return None
        item.name = name
        item.sort_order = sort_order
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: str) -> bool:
        """マスタデータを削除する。"""
        statement = select(MasterData).where(MasterData.id == item_id)
        item = self.db.scalar(statement)
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    def seed_if_empty(self, category: str, items: list[dict]) -> None:
        """カテゴリが空の場合のみ一括投入する。"""
        existing = self.db.scalar(
            select(func.count()).select_from(MasterData).where(MasterData.category == category)
        )
        if existing:
            return
        for item in items:
            self.db.add(MasterData(category=category, **item))
        self.db.commit()
