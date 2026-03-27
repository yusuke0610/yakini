import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.date_utils import format_iso_date
from ..db import Base


class BlogAccount(Base):
    """ブログ連携アカウント。"""

    __tablename__ = "blog_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "platform", name="uq_blog_accounts_user_platform"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    username: Mapped[str] = mapped_column(String(120), nullable=False)
    article_rows: Mapped[list["BlogArticle"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        order_by=lambda: BlogArticle.published_at_value.desc(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BlogArticle(Base):
    """ブログ記事。"""

    __tablename__ = "blog_articles"
    __table_args__ = (
        UniqueConstraint("account_id", "external_id", name="uq_blog_articles_account_external_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("blog_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(String(1000), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    published_at_value: Mapped[date | None] = mapped_column("published_at", Date, nullable=True)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tag_rows: Mapped[list["BlogArticleTag"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="BlogArticleTag.sort_order",
    )
    account: Mapped["BlogAccount"] = relationship(back_populates="article_rows")
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
    def platform(self) -> str:
        return self.account.platform if self.account else ""

    @property
    def published_at(self) -> str | None:
        return format_iso_date(self.published_at_value)

    @property
    def tags(self) -> list[str]:
        return [tag.name for tag in self.tag_rows]


class BlogArticleTag(Base):
    __tablename__ = "blog_article_tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    article_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("blog_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    article: Mapped["BlogArticle"] = relationship(back_populates="tag_rows")
