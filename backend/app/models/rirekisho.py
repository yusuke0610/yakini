import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.date_utils import format_iso_date, format_year_month
from ..db import Base
from ..services.shared.sort_utils import sort_by_date_asc


class Rirekisho(Base):
    __tablename__ = "rirekisho"
    __table_args__ = (UniqueConstraint("user_id", name="uq_rirekisho_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    gender: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    birthday_value: Mapped[date] = mapped_column("birthday", Date, nullable=False)
    prefecture: Mapped[str] = mapped_column(String(60), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    address: Mapped[str] = mapped_column(Text, nullable=False)
    address_furigana: Mapped[str] = mapped_column(String(400), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(255), nullable=False)
    motivation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    personal_preferences: Mapped[str] = mapped_column(Text, nullable=False, default="")
    photo: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    education_rows: Mapped[list["RirekishoEducation"]] = relationship(
        back_populates="rirekisho",
        cascade="all, delete-orphan",
        order_by="RirekishoEducation.sort_order",
    )
    work_history_rows: Mapped[list["RirekishoWorkHistory"]] = relationship(
        back_populates="rirekisho",
        cascade="all, delete-orphan",
        order_by="RirekishoWorkHistory.sort_order",
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
    def birthday(self) -> str:
        return format_iso_date(self.birthday_value) or ""

    @property
    def educations(self) -> list["RirekishoEducation"]:
        """学歴を日付の昇順でソートして返す。"""
        return sort_by_date_asc(list(self.education_rows))

    @property
    def work_histories(self) -> list["RirekishoWorkHistory"]:
        """職歴を日付の昇順でソートして返す。"""
        return sort_by_date_asc(list(self.work_history_rows))


class RirekishoEducation(Base):
    __tablename__ = "rirekisho_educations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rirekisho_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("rirekisho.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    occurred_on_value: Mapped[date] = mapped_column("date", Date, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    rirekisho: Mapped["Rirekisho"] = relationship(back_populates="education_rows")

    @property
    def date(self) -> str:
        return format_year_month(self.occurred_on_value) or ""


class RirekishoWorkHistory(Base):
    __tablename__ = "rirekisho_work_histories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rirekisho_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("rirekisho.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    occurred_on_value: Mapped[date] = mapped_column("date", Date, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    rirekisho: Mapped["Rirekisho"] = relationship(back_populates="work_history_rows")

    @property
    def date(self) -> str:
        return format_year_month(self.occurred_on_value) or ""
