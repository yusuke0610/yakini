"""AI キャリアパス分析のデータアクセス層。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import CareerAnalysis


class CareerAnalysisRepository:
    """CareerAnalysis の CRUD リポジトリ。"""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def get_next_version(self) -> int:
        """ユーザーの次バージョン番号を返す。"""
        max_version = self.db.scalar(
            select(func.max(CareerAnalysis.version)).where(
                CareerAnalysis.user_id == self.user_id,
            ),
        )
        return (max_version or 0) + 1

    def create(self, target_position: str, result_json_str: str) -> CareerAnalysis:
        """分析結果を新規作成する。"""
        version = self.get_next_version()
        analysis = CareerAnalysis(
            user_id=self.user_id,
            version=version,
            target_position=target_position,
            result_json=result_json_str,
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_all(self) -> list[CareerAnalysis]:
        """ユーザーの全分析結果を version 降順で返す。"""
        statement = (
            select(CareerAnalysis)
            .where(CareerAnalysis.user_id == self.user_id)
            .order_by(CareerAnalysis.version.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_id(self, analysis_id: int) -> CareerAnalysis | None:
        """指定 ID の分析結果を返す（所有者チェック込み）。"""
        statement = select(CareerAnalysis).where(
            CareerAnalysis.id == analysis_id,
            CareerAnalysis.user_id == self.user_id,
        )
        return self.db.scalar(statement)

    def delete(self, analysis_id: int) -> bool:
        """分析結果を削除する。"""
        analysis = self.get_by_id(analysis_id)
        if not analysis:
            return False
        self.db.delete(analysis)
        self.db.commit()
        return True
