"""created_at / updated_at に server_default を追加

0016 で作成されたテーブルの created_at / updated_at カラムに
server_default が設定されていなかったため、ORM 経由の INSERT 時に
NOT NULL 制約違反が発生していた問題を修正する。

SQLite は ALTER COLUMN をサポートしないため batch_alter_table で
テーブルを再作成する。

Revision ID: 0017_add_timestamp_defaults
Revises: 0016_normalize_document_storage
Create Date: 2026-03-21 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017_add_timestamp_defaults"
down_revision: Union[str, None] = "0016_normalize_document_storage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ["basic_info", "resumes", "rirekisho", "blog_articles"]


def upgrade() -> None:
    for table in _TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=False,
                server_default=sa.func.now(),
            )
            batch_op.alter_column(
                "updated_at",
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=False,
                server_default=sa.func.now(),
            )


def downgrade() -> None:
    for table in _TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=False,
                server_default=None,
            )
            batch_op.alter_column(
                "updated_at",
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=False,
                server_default=None,
            )
