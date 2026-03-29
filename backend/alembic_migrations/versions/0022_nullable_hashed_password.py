"""nullable_hashed_password

Revision ID: 0022_nullable_hashed_password
Revises: 0021_reconcile_career_analyses_table
Create Date: 2026-03-29 16:14:13.282598

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0022_nullable_hashed_password"
down_revision: Union[str, None] = "0021_reconcile_career_analyses_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """hashed_password を NULL 許容に変更する。GitHub OAuth 一本化対応。"""
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "hashed_password",
            existing_type=sa.VARCHAR(length=255),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "hashed_password",
            existing_type=sa.VARCHAR(length=255),
            nullable=False,
        )
