"""add last_synced_at to blog_accounts

Revision ID: 0029_add_last_synced_at_to_blog_accounts
Revises: 0028_add_refresh_jti_to_users
Create Date: 2026-05-02 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0029_add_last_synced_at_to_blog_accounts"
down_revision: Union[str, None] = "0028_add_refresh_jti_to_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("blog_accounts") as batch_op:
        batch_op.add_column(sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("blog_accounts") as batch_op:
        batch_op.drop_column("last_synced_at")
