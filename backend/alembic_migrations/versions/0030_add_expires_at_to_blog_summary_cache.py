"""add expires_at to blog_summary_cache

Revision ID: 0030_add_expires_at_to_blog_summary_cache
Revises: 0029_add_last_synced_at_to_blog_accounts
Create Date: 2026-05-02 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0030_add_expires_at_to_blog_summary_cache"
down_revision: Union[str, None] = "0029_add_last_synced_at_to_blog_accounts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("blog_summary_cache") as batch_op:
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("blog_summary_cache") as batch_op:
        batch_op.drop_column("expires_at")
