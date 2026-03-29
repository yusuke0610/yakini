"""AI キャリアパス分析のスナップショット。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class CareerAnalysis(Base):
    """AI が生成したキャリアパス分析のバージョン管理用スナップショット。"""

    __tablename__ = "career_analyses"
    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_career_analysis_user_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    target_position: Mapped[str] = mapped_column(String(200), nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )
