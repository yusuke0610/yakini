"""github_analysis_cache に position_advice カラムを追加

ポジションスコアに基づく学習アドバイスをキャッシュするためのカラム。

Revision ID: 0018_add_position_advice_column
Revises: 0017_add_timestamp_defaults
Create Date: 2026-03-27 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018_add_position_advice_column"
down_revision: Union[str, None] = "0017_add_timestamp_defaults"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("github_analysis_cache") as batch_op:
        batch_op.add_column(
            sa.Column("position_advice", sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("github_analysis_cache") as batch_op:
        batch_op.drop_column("position_advice")
