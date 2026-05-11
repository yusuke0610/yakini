"""add_task_retry_columns

Revision ID: 0027_add_task_retry_columns
Revises: 0026_drop_m_prefecture
Create Date: 2026-04-17

非同期タスクのリトライ機構のため、各分析テーブルに以下のカラムを追加する:
- retry_count: 現在までのリトライ回数（default 0）
- max_retries: 最大リトライ回数（default 3）
- next_retry_at: 次回リトライの予約時刻（nullable）

併せて、既存の ``status='failed'`` レコードを ``'dead_letter'`` に変換する
データマイグレーションを実行する。恒久的な失敗として UI に表示されるようになる。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0027_add_task_retry_columns"
down_revision: Union[str, None] = "0026_drop_m_prefecture"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ["github_analysis_cache", "blog_summary_cache", "career_analyses"]


def upgrade() -> None:
    for table in _TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "retry_count",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                ),
            )
            batch_op.add_column(
                sa.Column(
                    "max_retries",
                    sa.Integer(),
                    nullable=False,
                    server_default="3",
                ),
            )
            batch_op.add_column(
                sa.Column(
                    "next_retry_at",
                    sa.DateTime(timezone=True),
                    nullable=True,
                ),
            )

        # 既存の failed レコードを dead_letter に変換（データマイグレーション）
        op.execute(
            sa.text(
                f"UPDATE {table} SET status = 'dead_letter' WHERE status = 'failed'"
            )
        )


def downgrade() -> None:
    # dead_letter を failed に戻す（データマイグレーションの反転）
    for table in _TABLES:
        op.execute(
            sa.text(
                f"UPDATE {table} SET status = 'failed' WHERE status = 'dead_letter'"
            )
        )

    for table in _TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column("next_retry_at")
            batch_op.drop_column("max_retries")
            batch_op.drop_column("retry_count")
