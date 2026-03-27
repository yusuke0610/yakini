from sqlalchemy import select

from ..models import MPrefecture, MQualification, MTechnologyStack
from .base import BaseMasterRepository


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
        statement = (
            select(MTechnologyStack)
            .where(MTechnologyStack.category == category)
            .order_by(MTechnologyStack.sort_order, MTechnologyStack.name)
        )
        return list(self.db.scalars(statement).all())

    def create(self, category: str, name: str, sort_order: int = 0) -> MTechnologyStack:
        item = MTechnologyStack(category=category, name=name, sort_order=sort_order)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(
        self, item_id: str, category: str, name: str, sort_order: int = 0
    ) -> MTechnologyStack | None:
        item = self.db.scalar(select(MTechnologyStack).where(MTechnologyStack.id == item_id))
        if not item:
            return None
        item.category = category
        item.name = name
        item.sort_order = sort_order
        self.db.commit()
        self.db.refresh(item)
        return item
