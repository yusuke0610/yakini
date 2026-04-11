"""normalize document storage and blog articles

Revision ID: 0016_normalize_document_storage
Revises: 0015_add_birthday_to_rirekisho
Create Date: 2026-03-19 00:00:00.000000
"""

import json
from datetime import date
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016_normalize_document_storage"
down_revision: Union[str, None] = "0015_add_birthday_to_rirekisho"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _load_json(value):
    if value in (None, "", b""):
        return []
    if isinstance(value, (list, dict)):
        return value
    return json.loads(value)


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    trimmed = str(value).strip()
    if not trimmed:
        return None
    try:
        return date.fromisoformat(trimmed[:10])
    except ValueError:
        return None


def _parse_year_month(value: str | None) -> date | None:
    if not value:
        return None
    trimmed = str(value).strip()
    if not trimmed:
        return None
    parts = trimmed.split("-")
    if len(parts) < 2:
        return None
    try:
        return date(int(parts[0]), int(parts[1]), 1)
    except ValueError:
        return None


def _fallback_date(*candidates) -> date:
    for candidate in candidates:
        parsed = _parse_iso_date(candidate)
        if parsed:
            return parsed
    return date(1970, 1, 1)


def _fallback_year_month(*candidates) -> date:
    for candidate in candidates:
        parsed = _parse_year_month(candidate)
        if parsed:
            return parsed
    return date(1970, 1, 1)


def _latest_rows(conn, table_name: str) -> list[dict]:
    rows = conn.execute(
        sa.text(f"SELECT * FROM {table_name} ORDER BY updated_at DESC, created_at DESC")
    ).mappings()
    latest_by_user: dict[str, dict] = {}
    for row in rows:
        user_id = row["user_id"]
        if user_id not in latest_by_user:
            latest_by_user[user_id] = dict(row)
    return list(latest_by_user.values())


def _create_normalized_tables() -> None:
    op.create_table(
        "basic_info",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column(
            "name_furigana", sa.String(length=200), nullable=False, server_default=""
        ),
        sa.Column("record_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_basic_info_user"),
    )
    op.create_index("ix_basic_info_user_id", "basic_info", ["user_id"])

    op.create_table(
        "basic_info_qualifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("basic_info_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acquired_date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(
            ["basic_info_id"], ["basic_info.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_basic_info_qualifications_basic_info_id",
        "basic_info_qualifications",
        ["basic_info_id"],
    )

    op.create_table(
        "resumes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("career_summary", sa.Text(), nullable=False),
        sa.Column("self_pr", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_resumes_user"),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])

    op.create_table(
        "resume_experiences",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("resume_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("company", sa.String(length=120), nullable=False),
        sa.Column("business_description", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "is_current", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "employee_count", sa.String(length=60), nullable=False, server_default=""
        ),
        sa.Column("capital", sa.String(length=120), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resume_experiences_resume_id", "resume_experiences", ["resume_id"]
    )

    op.create_table(
        "resume_clients",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("experience_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("has_client", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ["experience_id"], ["resume_experiences.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resume_clients_experience_id", "resume_clients", ["experience_id"]
    )

    op.create_table(
        "resume_projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("client_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "is_current", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("role", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("challenge", sa.Text(), nullable=False, server_default=""),
        sa.Column("action", sa.Text(), nullable=False, server_default=""),
        sa.Column("result", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "team_total", sa.String(length=60), nullable=False, server_default=""
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], ["resume_clients.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_projects_client_id", "resume_projects", ["client_id"])

    op.create_table(
        "resume_project_team_members",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("role", sa.String(length=60), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["project_id"], ["resume_projects.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resume_project_team_members_project_id",
        "resume_project_team_members",
        ["project_id"],
    )

    op.create_table(
        "resume_project_technology_stacks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["resume_projects.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resume_project_technology_stacks_project_id",
        "resume_project_technology_stacks",
        ["project_id"],
    )

    op.create_table(
        "resume_project_phases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["resume_projects.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resume_project_phases_project_id",
        "resume_project_phases",
        ["project_id"],
    )

    op.create_table(
        "rirekisho",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("gender", sa.String(length=10), nullable=False, server_default=""),
        sa.Column("birthday", sa.Date(), nullable=False),
        sa.Column("prefecture", sa.String(length=60), nullable=False),
        sa.Column(
            "postal_code", sa.String(length=255), nullable=False, server_default=""
        ),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column(
            "address_furigana", sa.String(length=400), nullable=False, server_default=""
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=255), nullable=False),
        sa.Column("motivation", sa.Text(), nullable=False, server_default=""),
        sa.Column("personal_preferences", sa.Text(), nullable=False, server_default=""),
        sa.Column("photo", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_rirekisho_user"),
    )
    op.create_index("ix_rirekisho_user_id", "rirekisho", ["user_id"])

    op.create_table(
        "rirekisho_educations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("rirekisho_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.ForeignKeyConstraint(["rirekisho_id"], ["rirekisho.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rirekisho_educations_rirekisho_id", "rirekisho_educations", ["rirekisho_id"]
    )

    op.create_table(
        "rirekisho_work_histories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("rirekisho_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.ForeignKeyConstraint(["rirekisho_id"], ["rirekisho.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rirekisho_work_histories_rirekisho_id",
        "rirekisho_work_histories",
        ["rirekisho_id"],
    )

    op.create_table(
        "blog_articles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("external_id", sa.String(length=1000), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("published_at", sa.Date(), nullable=True),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["blog_accounts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_id", "external_id", name="uq_blog_articles_account_external_id"
        ),
    )
    op.create_index("ix_blog_articles_account_id", "blog_articles", ["account_id"])

    op.create_table(
        "blog_article_tags",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("article_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(
            ["article_id"], ["blog_articles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_blog_article_tags_article_id", "blog_article_tags", ["article_id"]
    )


def upgrade() -> None:
    conn = op.get_bind()

    op.rename_table("basic_info", "basic_info_legacy")
    op.rename_table("resumes", "resumes_legacy")
    op.rename_table("rirekisho", "rirekisho_legacy")
    op.rename_table("blog_articles", "blog_articles_legacy")

    _create_normalized_tables()

    basic_info_rows = _latest_rows(conn, "basic_info_legacy")
    for row in basic_info_rows:
        qualifications = _load_json(row.get("qualifications"))
        conn.execute(
            sa.text(
                """
            INSERT INTO basic_info (
                id, user_id, full_name, name_furigana, record_date, created_at, updated_at
            ) VALUES (
                :id, :user_id, :full_name, :name_furigana, :record_date, :created_at, :updated_at
            )
            """
            ),
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "full_name": row["full_name"],
                "name_furigana": row.get("name_furigana", "") or "",
                "record_date": _fallback_date(
                    row.get("record_date"),
                    row["updated_at"],
                    row["created_at"],
                ),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            },
        )
        for index, qualification in enumerate(qualifications):
            conn.execute(
                sa.text(
                    """
                INSERT INTO basic_info_qualifications (
                    id, basic_info_id, sort_order, acquired_date, name
                ) VALUES (
                    :id, :basic_info_id, :sort_order, :acquired_date, :name
                )
                """
                ),
                {
                    "id": f"{row['id']}-qualification-{index}",
                    "basic_info_id": row["id"],
                    "sort_order": index,
                    "acquired_date": _fallback_date(qualification.get("acquired_date")),
                    "name": qualification.get("name", ""),
                },
            )

    resume_rows = _latest_rows(conn, "resumes_legacy")
    for row in resume_rows:
        experiences = _load_json(row.get("experiences"))
        conn.execute(
            sa.text(
                """
            INSERT INTO resumes (
                id, user_id, career_summary, self_pr, created_at, updated_at
            ) VALUES (
                :id, :user_id, :career_summary, :self_pr, :created_at, :updated_at
            )
            """
            ),
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "career_summary": row["career_summary"],
                "self_pr": row["self_pr"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            },
        )
        for exp_index, experience in enumerate(experiences):
            experience_id = f"{row['id']}-experience-{exp_index}"
            conn.execute(
                sa.text(
                    """
                INSERT INTO resume_experiences (
                    id, resume_id, sort_order, company, business_description, start_date,
                    end_date, is_current, employee_count, capital
                ) VALUES (
                    :id, :resume_id, :sort_order, :company, :business_description, :start_date,
                    :end_date, :is_current, :employee_count, :capital
                )
                """
                ),
                {
                    "id": experience_id,
                    "resume_id": row["id"],
                    "sort_order": exp_index,
                    "company": experience.get("company", ""),
                    "business_description": experience.get("business_description", ""),
                    "start_date": _fallback_year_month(experience.get("start_date")),
                    "end_date": _parse_year_month(experience.get("end_date")),
                    "is_current": bool(experience.get("is_current", False)),
                    "employee_count": experience.get("employee_count", "") or "",
                    "capital": experience.get("capital", "") or "",
                },
            )
            clients = experience.get("clients") or []
            if not clients and experience.get("projects"):
                clients = [{"name": "", "has_client": True, "projects": experience["projects"]}]
            for client_index, client in enumerate(clients):
                client_id = f"{experience_id}-client-{client_index}"
                conn.execute(
                    sa.text(
                        """
                    INSERT INTO resume_clients (
                        id, experience_id, sort_order, name, has_client
                    ) VALUES (
                        :id, :experience_id, :sort_order, :name, :has_client
                    )
                    """
                    ),
                    {
                        "id": client_id,
                        "experience_id": experience_id,
                        "sort_order": client_index,
                        "name": client.get("name", "") or "",
                        "has_client": bool(client.get("has_client", True)),
                    },
                )
                for project_index, project in enumerate(client.get("projects", [])):
                    project_id = f"{client_id}-project-{project_index}"
                    team = project.get("team") or {}
                    if not team and project.get("scale"):
                        team = {"total": str(project["scale"]), "members": []}
                    conn.execute(
                        sa.text(
                            """
                        INSERT INTO resume_projects (
                            id, client_id, sort_order, name, start_date, end_date, is_current,
                            role, description, challenge, action, result, team_total
                        ) VALUES (
                            :id, :client_id, :sort_order, :name,
                            :start_date, :end_date, :is_current,
                            :role, :description, :challenge,
                            :action, :result, :team_total
                        )
                        """
                        ),
                        {
                            "id": project_id,
                            "client_id": client_id,
                            "sort_order": project_index,
                            "name": project.get("name", "") or "",
                            "start_date": _fallback_year_month(project.get("start_date")),
                            "end_date": _parse_year_month(project.get("end_date")),
                            "is_current": bool(project.get("is_current", False)),
                            "role": project.get("role", "") or "",
                            "description": project.get("description", "") or "",
                            "challenge": project.get("challenge", "") or "",
                            "action": project.get("action", "") or "",
                            "result": project.get("result", "") or "",
                            "team_total": team.get("total", "") or "",
                        },
                    )
                    for member_index, member in enumerate(team.get("members", [])):
                        conn.execute(
                            sa.text(
                                """
                            INSERT INTO resume_project_team_members (
                                id, project_id, sort_order, role, count
                            ) VALUES (
                                :id, :project_id, :sort_order, :role, :count
                            )
                            """
                            ),
                            {
                                "id": f"{project_id}-member-{member_index}",
                                "project_id": project_id,
                                "sort_order": member_index,
                                "role": member.get("role", ""),
                                "count": int(member.get("count", 0) or 0),
                            },
                        )
                    for stack_index, stack in enumerate(project.get("technology_stacks", [])):
                        conn.execute(
                            sa.text(
                                """
                            INSERT INTO resume_project_technology_stacks (
                                id, project_id, sort_order, category, name
                            ) VALUES (
                                :id, :project_id, :sort_order, :category, :name
                            )
                            """
                            ),
                            {
                                "id": f"{project_id}-stack-{stack_index}",
                                "project_id": project_id,
                                "sort_order": stack_index,
                                "category": stack.get("category", ""),
                                "name": stack.get("name", ""),
                            },
                        )
                    for phase_index, phase in enumerate(project.get("phases", [])):
                        conn.execute(
                            sa.text(
                                """
                            INSERT INTO resume_project_phases (
                                id, project_id, sort_order, name
                            ) VALUES (
                                :id, :project_id, :sort_order, :name
                            )
                            """
                            ),
                            {
                                "id": f"{project_id}-phase-{phase_index}",
                                "project_id": project_id,
                                "sort_order": phase_index,
                                "name": phase,
                            },
                        )

    rirekisho_rows = _latest_rows(conn, "rirekisho_legacy")
    for row in rirekisho_rows:
        educations = _load_json(row.get("educations"))
        work_histories = _load_json(row.get("work_histories"))
        conn.execute(
            sa.text(
                """
            INSERT INTO rirekisho (
                id, user_id, gender, birthday, prefecture, postal_code, address,
                address_furigana, email, phone, motivation, personal_preferences,
                photo, created_at, updated_at
            ) VALUES (
                :id, :user_id, :gender, :birthday, :prefecture, :postal_code, :address,
                :address_furigana, :email, :phone, :motivation, :personal_preferences,
                :photo, :created_at, :updated_at
            )
            """
            ),
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "gender": row.get("gender", "") or "",
                "birthday": _fallback_date(
                    row.get("birthday"),
                    row["updated_at"],
                    row["created_at"],
                ),
                "prefecture": row["prefecture"],
                "postal_code": row.get("postal_code", "") or "",
                "address": row["address"],
                "address_furigana": row.get("address_furigana", "") or "",
                "email": row["email"],
                "phone": row["phone"],
                "motivation": row.get("motivation", "") or "",
                "personal_preferences": row.get("personal_preferences", "") or "",
                "photo": row.get("photo"),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            },
        )
        for index, education in enumerate(educations):
            conn.execute(
                sa.text(
                    """
                INSERT INTO rirekisho_educations (
                    id, rirekisho_id, sort_order, date, name
                ) VALUES (
                    :id, :rirekisho_id, :sort_order, :date, :name
                )
                """
                ),
                {
                    "id": f"{row['id']}-education-{index}",
                    "rirekisho_id": row["id"],
                    "sort_order": index,
                    "date": _fallback_year_month(education.get("date")),
                    "name": education.get("name", ""),
                },
            )
        for index, work_history in enumerate(work_histories):
            conn.execute(
                sa.text(
                    """
                INSERT INTO rirekisho_work_histories (
                    id, rirekisho_id, sort_order, date, name
                ) VALUES (
                    :id, :rirekisho_id, :sort_order, :date, :name
                )
                """
                ),
                {
                    "id": f"{row['id']}-work-history-{index}",
                    "rirekisho_id": row["id"],
                    "sort_order": index,
                    "date": _fallback_year_month(work_history.get("date")),
                    "name": work_history.get("name", ""),
                },
            )

    article_rows = conn.execute(
        sa.text(
            """
        SELECT * FROM blog_articles_legacy
        ORDER BY updated_at DESC, created_at DESC
        """
        )
    ).mappings()
    seen_articles: set[tuple[str, str]] = set()
    for row in article_rows:
        external_id = row["external_id"] or row["url"]
        dedupe_key = (row["account_id"], external_id)
        if dedupe_key in seen_articles:
            continue
        seen_articles.add(dedupe_key)
        conn.execute(
            sa.text(
                """
            INSERT INTO blog_articles (
                id, account_id, external_id, title, url, published_at,
                likes_count, summary, created_at, updated_at
            ) VALUES (
                :id, :account_id, :external_id, :title, :url, :published_at,
                :likes_count, :summary, :created_at, :updated_at
            )
            """
            ),
            {
                "id": row["id"],
                "account_id": row["account_id"],
                "external_id": external_id,
                "title": row["title"],
                "url": row["url"],
                "published_at": _parse_iso_date(row.get("published_at")),
                "likes_count": row.get("likes_count", 0),
                "summary": row.get("summary"),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            },
        )
        for index, tag in enumerate(_load_json(row.get("tags"))):
            conn.execute(
                sa.text(
                    """
                INSERT INTO blog_article_tags (
                    id, article_id, sort_order, name
                ) VALUES (
                    :id, :article_id, :sort_order, :name
                )
                """
                ),
                {
                    "id": f"{row['id']}-tag-{index}",
                    "article_id": row["id"],
                    "sort_order": index,
                    "name": str(tag),
                },
            )

    op.drop_table("blog_articles_legacy")
    op.drop_table("rirekisho_legacy")
    op.drop_table("resumes_legacy")
    op.drop_table("basic_info_legacy")


def downgrade() -> None:
    raise NotImplementedError("0016_normalize_document_storage is irreversible")
