"""履歴書に birthday カラムを追加

Revision ID: 0015_add_birthday_to_rirekisho
Revises: 0014_add_rirekisho_and_basic_info_columns
Create Date: 2026-03-18 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015_add_birthday_to_rirekisho"
down_revision: Union[str, None] = "0014_add_rirekisho_and_basic_info_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("rirekisho") as batch_op:
        batch_op.add_column(
            sa.Column("birthday", sa.String(length=20), nullable=False, server_default="")
        )


def downgrade() -> None:
    with op.batch_alter_table("rirekisho") as batch_op:
        batch_op.drop_column("birthday")
