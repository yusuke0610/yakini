"""add_refresh_jti_to_users

Revision ID: 0028_add_refresh_jti_to_users
Revises: 0027_add_task_retry_columns
Create Date: 2026-04-24

リフレッシュトークン失効のため users テーブルに refresh_jti カラムを追加する。
ログアウト時や不正利用検知時に NULL クリアすることでトークンを即時無効化できる。
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0028_add_refresh_jti_to_users"
down_revision: Union[str, None] = "0027_add_task_retry_columns"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("refresh_jti", sa.String(36), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("refresh_jti")
