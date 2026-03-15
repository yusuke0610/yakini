"""split master_data into m_qualification, m_technology_stack, m_prefecture

Revision ID: 0010_split_master_data_tables
Revises: 0009_create_master_data_table
Create Date: 2026-03-15 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_split_master_data_tables"
down_revision: Union[str, None] = "0009_create_master_data_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # m_qualification テーブル作成
    op.create_table(
        "m_qualification",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_m_qualification_name"),
    )

    # m_technology_stack テーブル作成
    op.create_table(
        "m_technology_stack",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category", "name", name="uq_m_technology_stack_category_name"),
    )
    op.create_index("ix_m_technology_stack_category", "m_technology_stack", ["category"])

    # m_prefecture テーブル作成
    op.create_table(
        "m_prefecture",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_m_prefecture_name"),
    )

    # 旧テーブル master_data からデータ移行
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='master_data'"))
    if result.fetchone() is not None:
        conn.execute(sa.text(
            "INSERT INTO m_qualification (id, name, sort_order, created_at) "
            "SELECT id, name, sort_order, created_at FROM master_data WHERE category = 'qualification'"
        ))
        conn.execute(sa.text(
            "INSERT INTO m_prefecture (id, name, sort_order, created_at) "
            "SELECT id, name, sort_order, created_at FROM master_data WHERE category = 'prefecture'"
        ))
        # technology_stack はカテゴリなしだったので移行しない（シードで再投入される）
        op.drop_index("ix_master_data_category", table_name="master_data")
        op.drop_table("master_data")


def downgrade() -> None:
    op.create_table(
        "master_data",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category", "name", name="uq_master_data_category_name"),
    )
    op.create_index("ix_master_data_category", "master_data", ["category"])
    op.drop_index("ix_m_technology_stack_category", table_name="m_technology_stack")
    op.drop_table("m_qualification")
    op.drop_table("m_technology_stack")
    op.drop_table("m_prefecture")
