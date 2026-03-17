import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, default=None)
    github_id: Mapped[int | None] = mapped_column(nullable=True, unique=True, default=None)
    github_token: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BasicInfo(Base):
    __tablename__ = "basic_info"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    name_furigana: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    record_date: Mapped[str] = mapped_column(String(30), nullable=False)
    qualifications: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    career_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    self_pr: Mapped[str] = mapped_column(Text, nullable=False)
    experiences: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Rirekisho(Base):
    __tablename__ = "rirekisho"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    prefecture: Mapped[str] = mapped_column(String(60), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    address_furigana: Mapped[str] = mapped_column(String(400), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    motivation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    personal_preferences: Mapped[str] = mapped_column(Text, nullable=False, default="")
    photo: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    educations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    work_histories: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class BlogAccount(Base):
    """ブログ連携アカウント。"""

    __tablename__ = "blog_accounts"
    __table_args__ = (UniqueConstraint("user_id", "platform", name="uq_blog_accounts_user_platform"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    username: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BlogArticle(Base):
    """ブログ記事。"""

    __tablename__ = "blog_articles"
    __table_args__ = (
        UniqueConstraint("user_id", "platform", "external_id", name="uq_blog_articles_user_platform_ext"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("blog_accounts.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    published_at: Mapped[str | None] = mapped_column(String(30), nullable=True)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class MQualification(Base):
    """資格マスタ。"""

    __tablename__ = "m_qualification"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MTechnologyStack(Base):
    """技術スタックマスタ。カテゴリ別に技術名を管理する。"""

    __tablename__ = "m_technology_stack"
    __table_args__ = (UniqueConstraint("category", "name", name="uq_m_technology_stack_category_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MPrefecture(Base):
    """都道府県マスタ。"""

    __tablename__ = "m_prefecture"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
