"""career_analyses テーブルの実スキーマを補正

過去の 0019 リビジョンが差し替えられた影響で、
alembic_version は進んでいるのに career_analyses が存在しない
SQLite ファイルが残っているため、そのズレを補正する。

Revision ID: 0021_reconcile_career_analyses_table
Revises: 0020_remove_skill_activity_cache_columns
Create Date: 2026-03-29 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021_reconcile_career_analyses_table"
down_revision: Union[str, None] = "0020_remove_skill_activity_cache_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if "career_analyses" not in tables:
        op.create_table(
            "career_analyses",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("target_position", sa.String(length=200), nullable=False),
            sa.Column("result_json", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "version", name="uq_career_analysis_user_version"),
        )
        op.create_index(
            op.f("ix_career_analyses_user_id"),
            "career_analyses",
            ["user_id"],
            unique=False,
        )
    else:
        indexes = {index["name"] for index in inspector.get_indexes("career_analyses")}
        index_name = op.f("ix_career_analyses_user_id")
        if index_name not in indexes:
            op.create_index(index_name, "career_analyses", ["user_id"], unique=False)

    if "ai_resume_snapshots" in tables:
        op.drop_table("ai_resume_snapshots")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if "career_analyses" in tables:
        indexes = {index["name"] for index in inspector.get_indexes("career_analyses")}
        index_name = op.f("ix_career_analyses_user_id")
        if index_name in indexes:
            op.drop_index(index_name, table_name="career_analyses")
        op.drop_table("career_analyses")
