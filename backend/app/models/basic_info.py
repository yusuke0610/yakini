import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.date_utils import format_iso_date
from ..db import Base
from ..services.shared.sort_utils import sort_by_date_desc


class BasicInfo(Base):
    __tablename__ = "basic_info"
    __table_args__ = (UniqueConstraint("user_id", name="uq_basic_info_user"),)

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    name_furigana: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    record_date_value: Mapped[date] = mapped_column("record_date", Date, nullable=False)
    qualification_rows: Mapped[list["BasicInfoQualification"]] = relationship(
        back_populates="basic_info",
        cascade="all, delete-orphan",
        order_by="BasicInfoQualification.sort_order",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def record_date(self) -> str:
        return format_iso_date(self.record_date_value) or ""

    @property
    def qualifications(self) -> list["BasicInfoQualification"]:
        """資格を取得日の降順でソートして返す。"""
        return sort_by_date_desc(list(self.qualification_rows))


class BasicInfoQualification(Base):
    __tablename__ = "basic_info_qualifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    basic_info_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("basic_info.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    acquired_date_value: Mapped[date] = mapped_column("acquired_date", Date, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    basic_info: Mapped["BasicInfo"] = relationship(back_populates="qualification_rows")

    @property
    def acquired_date(self) -> str:
        return format_iso_date(self.acquired_date_value) or ""
