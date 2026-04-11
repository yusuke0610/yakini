"""履歴書に gender/address_furigana を追加、基本情報に name_furigana を追加

Revision ID: 0014_add_rirekisho_and_basic_info_columns
Revises: 0013_create_blog_summary_cache
Create Date: 2026-03-17 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014_add_rirekisho_and_basic_info_columns"
down_revision: Union[str, None] = "0013_create_blog_summary_cache"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # basic_info に name_furigana を追加
    with op.batch_alter_table("basic_info") as batch_op:
        batch_op.add_column(
            sa.Column("name_furigana", sa.String(length=200), nullable=False, server_default="")
        )

    # rirekisho に gender, address_furigana を追加
    with op.batch_alter_table("rirekisho") as batch_op:
        batch_op.add_column(
            sa.Column("gender", sa.String(length=10), nullable=False, server_default="")
        )
        batch_op.add_column(
            sa.Column("address_furigana", sa.String(length=400), nullable=False, server_default="")
        )


def downgrade() -> None:
    with op.batch_alter_table("rirekisho") as batch_op:
        batch_op.drop_column("address_furigana")
        batch_op.drop_column("gender")

    with op.batch_alter_table("basic_info") as batch_op:
        batch_op.drop_column("name_furigana")
