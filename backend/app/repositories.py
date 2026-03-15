import logging
from typing import Any, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .encryption import decrypt_field, encrypt_field
from .models import BasicInfo, MPrefecture, MQualification, MTechnologyStack, Resume, Rirekisho, User

_ENCRYPTED_RIREKISHO_FIELDS = {"email", "phone", "postal_code", "address"}

T = TypeVar("T")


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
        return self.db.scalar(select(User).where(User.username == username))

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_github_id(self, github_id: int) -> User | None:
        return self.db.scalar(select(User).where(User.github_id == github_id))

    def create_github_user(self, username: str, github_id: int) -> User:
        user = User(username=username, hashed_password="", github_id=github_id)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(User)) or 0


class BaseUserDocRepository:
    """ユーザーに紐づくドキュメント（基本情報・職務経歴書・履歴書）の共通リポジトリ。"""

    _model: type  # サブクラスで設定

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def create(self, payload: dict[str, Any]) -> Any:
        entity = self._model(**payload, user_id=self.user_id)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_latest(self) -> Any:
        statement = (
            select(self._model)
            .where(self._model.user_id == self.user_id)
            .order_by(self._model.updated_at.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def get_by_id(self, entity_id: str) -> Any:
        statement = (
            select(self._model)
            .where(self._model.id == entity_id)
            .where(self._model.user_id == self.user_id)
        )
        return self.db.scalar(statement)

    def update(self, entity: Any, payload: dict[str, Any]) -> Any:
        for field, value in payload.items():
            setattr(entity, field, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity


class BasicInfoRepository(BaseUserDocRepository):
    _model = BasicInfo


class ResumeRepository(BaseUserDocRepository):
    _model = Resume


class RirekishoRepository(BaseUserDocRepository):
    """履歴書リポジトリ。個人情報フィールドの暗号化・復号を行う。"""

    _model = Rirekisho

    def _encrypt_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
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
        rirekisho = super().create(self._encrypt_payload(payload))
        self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def get_latest(self) -> Rirekisho | None:
        rirekisho = super().get_latest()
        if rirekisho:
            self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def get_by_id(self, entity_id: str) -> Rirekisho | None:
        rirekisho = super().get_by_id(entity_id)
        if rirekisho:
            self._decrypt_rirekisho(rirekisho)
        return rirekisho

    def update(self, entity: Any, payload: dict[str, Any]) -> Rirekisho:
        rirekisho = super().update(entity, self._encrypt_payload(payload))
        self._decrypt_rirekisho(rirekisho)
        return rirekisho


class BaseMasterRepository:
    """マスタデータ（資格・都道府県）の共通リポジトリ。"""

    _model: type  # サブクラスで設定

    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list:
        """マスタ一覧を取得する。"""
        statement = select(self._model).order_by(self._model.sort_order, self._model.name)
        return list(self.db.scalars(statement).all())

    def create(self, name: str, sort_order: int = 0) -> Any:
        """マスタを作成する。"""
        item = self._model(name=name, sort_order=sort_order)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item_id: str, name: str, sort_order: int = 0) -> Any:
        """マスタを更新する。"""
        item = self.db.scalar(select(self._model).where(self._model.id == item_id))
        if not item:
            return None
        item.name = name
        item.sort_order = sort_order
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: str) -> bool:
        """マスタを削除する。"""
        item = self.db.scalar(select(self._model).where(self._model.id == item_id))
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    def seed_if_empty(self, items: list[dict]) -> None:
        """テーブルが空の場合のみ一括投入する。"""
        count = self.db.scalar(select(func.count()).select_from(self._model))
        if count:
            return
        for item in items:
            self.db.add(self._model(**item))
        self.db.commit()


class MQualificationRepository(BaseMasterRepository):
    """資格マスタリポジトリ。"""
    _model = MQualification


class MPrefectureRepository(BaseMasterRepository):
    """都道府県マスタリポジトリ。"""
    _model = MPrefecture


class MTechnologyStackRepository(BaseMasterRepository):
    """技術スタックマスタリポジトリ。category フィールドを追加で管理する。"""
    _model = MTechnologyStack

    def list_by_category(self, category: str) -> list[MTechnologyStack]:
        """カテゴリ別に技術スタックマスタを取得する。"""
        statement = (
            select(MTechnologyStack)
            .where(MTechnologyStack.category == category)
            .order_by(MTechnologyStack.sort_order, MTechnologyStack.name)
        )
        return list(self.db.scalars(statement).all())

    def create(self, category: str, name: str, sort_order: int = 0) -> MTechnologyStack:
        """技術スタックマスタを作成する。"""
        item = MTechnologyStack(category=category, name=name, sort_order=sort_order)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(
        self, item_id: str, name: str, sort_order: int = 0, category: str | None = None
    ) -> MTechnologyStack | None:
        """技術スタックマスタを更新する。"""
        item = self.db.scalar(select(MTechnologyStack).where(MTechnologyStack.id == item_id))
        if not item:
            return None
        item.name = name
        item.sort_order = sort_order
        if category is not None:
            item.category = category
        self.db.commit()
        self.db.refresh(item)
        return item
