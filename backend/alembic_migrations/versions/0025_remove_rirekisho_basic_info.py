"""remove rirekisho/basic_info, move full_name and qualifications into resumes

Revision ID: 0025_remove_rirekisho_basic_info
Revises: 0024_add_notifications_table
Create Date: 2026-04-11

履歴書 (rirekisho) と基本情報 (basic_info) を DevForge のスコープから外す。
氏名 (full_name) と資格 (qualifications) は職務経歴書 (resumes) に移植する。

- resumes に full_name 列を追加
- resume_qualifications 子テーブルを作成
- basic_info_qualifications, basic_info, rirekisho_educations,
  rirekisho_work_histories, rirekisho を drop
- データ移行は行わない（単一ユーザー前提のため）
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0025_remove_rirekisho_basic_info"
down_revision: Union[str, None] = "0024_add_notifications_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # resumes に full_name 列を追加
    with op.batch_alter_table("resumes") as batch_op:
        batch_op.add_column(
            sa.Column(
                "full_name",
                sa.String(length=120),
                nullable=False,
                server_default="",
            )
        )

    # resume_qualifications 子テーブルを作成
    op.create_table(
        "resume_qualifications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("resume_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("acquired_date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_resume_qualifications_resume_id",
        "resume_qualifications",
        ["resume_id"],
    )

    # 履歴書・基本情報のテーブルを drop
    op.drop_index("ix_rirekisho_work_histories_rirekisho_id", table_name="rirekisho_work_histories")
    op.drop_table("rirekisho_work_histories")

    op.drop_index("ix_rirekisho_educations_rirekisho_id", table_name="rirekisho_educations")
    op.drop_table("rirekisho_educations")

    op.drop_index("ix_rirekisho_user_id", table_name="rirekisho")
    op.drop_table("rirekisho")

    op.drop_index(
        "ix_basic_info_qualifications_basic_info_id",
        table_name="basic_info_qualifications",
    )
    op.drop_table("basic_info_qualifications")

    op.drop_index("ix_basic_info_user_id", table_name="basic_info")
    op.drop_table("basic_info")


def downgrade() -> None:
    raise NotImplementedError(
        "0025_remove_rirekisho_basic_info は不可逆的な削除のためロールバック不可"
    )
