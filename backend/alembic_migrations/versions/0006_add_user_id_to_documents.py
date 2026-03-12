"""add user_id to basic_info, resumes, rirekisho

Revision ID: 0006_add_user_id_to_documents
Revises: 0005_add_personal_preferences_to_rirekisho
Create Date: 2026-03-12 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_add_user_id_to_documents"
down_revision: Union[str, None] = "0005_add_personal_preferences_to_rirekisho"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("basic_info", "resumes", "rirekisho")


def upgrade() -> None:
    conn = op.get_bind()

    # 既存ユーザーの ID を取得（既存データの埋め込み用）
    result = conn.execute(sa.text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1"))
    row = result.fetchone()
    default_user_id = row[0] if row else ""

    for table in _TABLES:
        # まず nullable=True で追加
        op.add_column(table, sa.Column("user_id", sa.String(36), nullable=True))

        # 既存行を埋める
        op.execute(
            sa.text(f"UPDATE {table} SET user_id = :uid").bindparams(uid=default_user_id)
        )

        # nullable=False に変更
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column("user_id", nullable=False)
            batch_op.create_foreign_key(
                f"fk_{table}_user_id",
                "users",
                ["user_id"],
                ["id"],
            )


def downgrade() -> None:
    for table in _TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_constraint(f"fk_{table}_user_id", type_="foreignkey")
            batch_op.drop_column("user_id")
