"""create master_data table

Revision ID: 0009_create_master_data_table
Revises: 0008_add_github_token_to_users
Create Date: 2026-03-15 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009_create_master_data_table"
down_revision: Union[str, None] = "0008_add_github_token_to_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='master_data'")
    )
    if result.fetchone() is None:
        op.create_table(
            "master_data",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("category", sa.String(length=60), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("category", "name", name="uq_master_data_category_name"),
        )
        op.create_index("ix_master_data_category", "master_data", ["category"])


def downgrade() -> None:
    op.drop_index("ix_master_data_category", table_name="master_data")
    op.drop_table("master_data")
