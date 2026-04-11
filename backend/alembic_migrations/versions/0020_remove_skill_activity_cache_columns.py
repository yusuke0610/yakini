"""github_analysis_cache から skill_activity カラムを削除

スキル成熟度グラフ廃止に伴い、未使用になったキャッシュ列を削除する。

Revision ID: 0020_remove_skill_activity_cache_columns
Revises: 0019_add_ai_resume_snapshots_table
Create Date: 2026-03-29 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020_remove_skill_activity_cache_columns"
down_revision: Union[str, None] = "0019_add_ai_resume_snapshots_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("github_analysis_cache") as batch_op:
        batch_op.drop_column("skill_activity_month")
        batch_op.drop_column("skill_activity_year")


def downgrade() -> None:
    with op.batch_alter_table("github_analysis_cache") as batch_op:
        batch_op.add_column(sa.Column("skill_activity_month", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("skill_activity_year", sa.JSON(), nullable=True))
