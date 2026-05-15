"""add warning_message to github_analysis_cache

Revision ID: 0031_add_warning_message_to_github_analysis_cache
Revises: 0030_add_expires_at_to_blog_summary_cache
Create Date: 2026-05-15 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0031_add_warning_message_to_github_analysis_cache"
down_revision: Union[str, None] = "0030_add_expires_at_to_blog_summary_cache"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("github_analysis_cache") as batch_op:
        batch_op.add_column(sa.Column("warning_message", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("github_analysis_cache") as batch_op:
        batch_op.drop_column("warning_message")
