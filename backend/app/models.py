import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .date_utils import format_iso_date, format_year_month
from .services.sort_utils import sort_by_date_asc, sort_by_date_desc, sort_by_period_desc


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, default=None)
    github_id: Mapped[int | None] = mapped_column(nullable=True, unique=True, default=None)
    github_token: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


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


class Resume(Base):
    __tablename__ = "resumes"
    __table_args__ = (UniqueConstraint("user_id", name="uq_resumes_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    career_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    self_pr: Mapped[str] = mapped_column(Text, nullable=False)
    experience_rows: Mapped[list["ResumeExperience"]] = relationship(
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeExperience.sort_order",
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
    def experiences(self) -> list["ResumeExperience"]:
        """経歴を在籍期間の降順でソートして返す。"""
        return sort_by_period_desc(list(self.experience_rows))


class ResumeExperience(Base):
    __tablename__ = "resume_experiences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    company: Mapped[str] = mapped_column(String(120), nullable=False)
    business_description: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date_value: Mapped[date] = mapped_column("start_date", Date, nullable=False)
    end_date_value: Mapped[date | None] = mapped_column("end_date", Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    employee_count: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    capital: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    client_rows: Mapped[list["ResumeClient"]] = relationship(
        back_populates="experience",
        cascade="all, delete-orphan",
        order_by="ResumeClient.sort_order",
    )
    resume: Mapped["Resume"] = relationship(back_populates="experience_rows")

    @property
    def start_date(self) -> str:
        return format_year_month(self.start_date_value) or ""

    @property
    def end_date(self) -> str | None:
        return format_year_month(self.end_date_value)

    @property
    def clients(self) -> list["ResumeClient"]:
        return list(self.client_rows)


class ResumeClient(Base):
    __tablename__ = "resume_clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experience_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("resume_experiences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    has_client: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    project_rows: Mapped[list["ResumeProject"]] = relationship(
        back_populates="client",
        cascade="all, delete-orphan",
        order_by="ResumeProject.sort_order",
    )
    experience: Mapped["ResumeExperience"] = relationship(back_populates="client_rows")

    @property
    def projects(self) -> list["ResumeProject"]:
        """プロジェクトを期間の降順でソートして返す。"""
        return sort_by_period_desc(list(self.project_rows))


class ResumeProject(Base):
    __tablename__ = "resume_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("resume_clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    start_date_value: Mapped[date] = mapped_column("start_date", Date, nullable=False)
    end_date_value: Mapped[date | None] = mapped_column("end_date", Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    challenge: Mapped[str] = mapped_column(Text, nullable=False, default="")
    action: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result: Mapped[str] = mapped_column(Text, nullable=False, default="")
    team_total: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    team_member_rows: Mapped[list["ResumeProjectTeamMember"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ResumeProjectTeamMember.sort_order",
    )
    technology_stack_rows: Mapped[list["ResumeProjectTechnologyStack"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ResumeProjectTechnologyStack.sort_order",
    )
    phase_rows: Mapped[list["ResumeProjectPhase"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ResumeProjectPhase.sort_order",
    )
    client: Mapped["ResumeClient"] = relationship(back_populates="project_rows")

    @property
    def start_date(self) -> str:
        return format_year_month(self.start_date_value) or ""

    @property
    def end_date(self) -> str | None:
        return format_year_month(self.end_date_value)

    @property
    def team(self) -> dict:
        return {
            "total": self.team_total,
            "members": list(self.team_member_rows),
        }

    @property
    def technology_stacks(self) -> list["ResumeProjectTechnologyStack"]:
        return list(self.technology_stack_rows)

    @property
    def phases(self) -> list[str]:
        return [phase.name for phase in self.phase_rows]


class ResumeProjectTeamMember(Base):
    __tablename__ = "resume_project_team_members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("resume_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    role: Mapped[str] = mapped_column(String(60), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    project: Mapped["ResumeProject"] = relationship(back_populates="team_member_rows")


class ResumeProjectTechnologyStack(Base):
    __tablename__ = "resume_project_technology_stacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("resume_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    project: Mapped["ResumeProject"] = relationship(back_populates="technology_stack_rows")


class ResumeProjectPhase(Base):
    __tablename__ = "resume_project_phases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("resume_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    project: Mapped["ResumeProject"] = relationship(back_populates="phase_rows")


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


class GitHubAnalysisCache(Base):
    """GitHub 分析結果のキャッシュ。ユーザーごとに最新の分析結果を1件保持する。"""

    __tablename__ = "github_analysis_cache"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, nullable=False
    )
    analysis_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_activity_month: Mapped[list | None] = mapped_column(JSON, nullable=True)
    skill_activity_year: Mapped[list | None] = mapped_column(JSON, nullable=True)
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


class BlogSummaryCache(Base):
    """ブログ AI 分析結果のキャッシュ。ユーザーごとに最新の要約を1件保持する。"""

    __tablename__ = "blog_summary_cache"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, nullable=False
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
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


class MQualification(Base):
    """資格マスタ。"""

    __tablename__ = "m_qualification"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MTechnologyStack(Base):
    """技術スタックマスタ。カテゴリ別に技術名を管理する。"""

    __tablename__ = "m_technology_stack"
    __table_args__ = (
        UniqueConstraint("category", "name", name="uq_m_technology_stack_category_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MPrefecture(Base):
    """都道府県マスタ。"""

    __tablename__ = "m_prefecture"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
