"""drop ai_resume_snapshots and create career_analyses table

Revision ID: 0019_add_ai_resume_snapshots_table
Revises: 0018_add_position_advice_column
Create Date: 2026-03-28 21:55:12.685844

"""

from typing import Sequence, Union  # noqa: F401

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0019_add_ai_resume_snapshots_table"
down_revision: Union[str, None] = "0018_add_position_advice_column"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ai_resume_snapshots が残っていれば drop する
    conn = op.get_bind()
    tables = sa.inspect(conn).get_table_names()
    if "ai_resume_snapshots" in tables:
        op.drop_table("ai_resume_snapshots")

    # career_analyses テーブルを作成
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
        op.f("ix_career_analyses_user_id"), "career_analyses", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_career_analyses_user_id"), table_name="career_analyses")
    op.drop_table("career_analyses")
