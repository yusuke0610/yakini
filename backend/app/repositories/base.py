from typing import Any, TypeVar

from sqlalchemy import func, select

T = TypeVar("T")


class SingleUserDocumentRepository:
    """1ユーザー1件のドキュメント用共通リポジトリ。"""

    _model: type
    _loader_options: tuple[Any, ...] = ()

    def __init__(self, db, user_id: str):
        self.db = db
        self.user_id = user_id

    def _statement(self):
        statement = select(self._model).where(self._model.user_id == self.user_id)
        for option in self._loader_options:
            statement = statement.options(option)
        return statement

    def get_current(self) -> Any:
        return self.db.scalar(self._statement())

    def get_latest(self) -> Any:
        return self.get_current()

    def get_by_id(self, entity_id: str) -> Any:
        statement = self._statement().where(self._model.id == entity_id)
        return self.db.scalar(statement)

    def create(self, payload: dict[str, Any]) -> Any:
        if self.get_current():
            raise ValueError("document.already_exists")
        entity = self._model(user_id=self.user_id)
        self._apply_payload(entity, payload)
        self.db.add(entity)
        self.db.commit()
        return self.get_by_id(entity.id)

    def update(self, entity: Any, payload: dict[str, Any]) -> Any:
        self._apply_payload(entity, payload)
        self.db.commit()
        return self.get_by_id(entity.id)

    def delete(self) -> bool:
        """ドキュメントを削除する。CASCADE により子テーブルも削除される。"""
        entity = self.get_current()
        if not entity:
            return False
        self.db.delete(entity)
        self.db.commit()
        return True

    def _apply_payload(self, entity: Any, payload: dict[str, Any]) -> None:
        raise NotImplementedError


class BaseMasterRepository:
    """マスタデータ（資格・都道府県）の共通リポジトリ。"""

    _model: type

    def __init__(self, db):
        self.db = db

    def list_all(self) -> list:
        """マスタ一覧を取得する。"""
        statement = select(self._model).order_by(self._model.sort_order, self._model.name)
        return list(self.db.scalars(statement).all())

    def create(self, name: str, sort_order: int = 0):
        """マスタを作成する。"""
        item = self._model(name=name, sort_order=sort_order)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item_id: str, name: str, sort_order: int = 0):
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
