"""create blog_accounts and blog_articles tables

Revision ID: 0011_create_blog_tables
Revises: 0010_split_master_data_tables
Create Date: 2026-03-15 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_create_blog_tables"
down_revision: Union[str, None] = "0010_split_master_data_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # blog_accounts テーブル作成
    op.create_table(
        "blog_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", "platform", name="uq_blog_accounts_user_platform"),
    )

    # blog_articles テーブル作成
    op.create_table(
        "blog_articles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("published_at", sa.String(length=30), nullable=True),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["account_id"], ["blog_accounts.id"]),
        sa.UniqueConstraint(
            "user_id", "platform", "external_id", name="uq_blog_articles_user_platform_ext"
        ),
    )


def downgrade() -> None:
    op.drop_table("blog_articles")
    op.drop_table("blog_accounts")
