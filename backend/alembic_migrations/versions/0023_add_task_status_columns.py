"""add_task_status_columns

Revision ID: 0023_add_task_status_columns
Revises: 0022_nullable_hashed_password
Create Date: 2026-03-30

各分析テーブルにバックグラウンドタスク管理用のカラムを追加する。
既存レコードは status="completed" として扱う。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023_add_task_status_columns"
down_revision: Union[str, None] = "0022_nullable_hashed_password"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ["github_analysis_cache", "blog_summary_cache", "career_analyses"]


def upgrade() -> None:
    for table in _TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(
                sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
            )
            batch_op.add_column(
                sa.Column("error_message", sa.Text(), nullable=True),
            )
            batch_op.add_column(
                sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            )
            batch_op.add_column(
                sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            )

    # career_analyses.result_json を nullable に変更（pending 時は NULL）
    with op.batch_alter_table("career_analyses") as batch_op:
        batch_op.alter_column("result_json", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    # career_analyses.result_json を NOT NULL に戻す
    with op.batch_alter_table("career_analyses") as batch_op:
        batch_op.alter_column("result_json", existing_type=sa.Text(), nullable=False)

    for table in _TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column("completed_at")
            batch_op.drop_column("started_at")
            batch_op.drop_column("error_message")
            batch_op.drop_column("status")
