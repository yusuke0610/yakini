"""drop m_prefecture master table

Revision ID: 0026_drop_m_prefecture
Revises: 0025_remove_rirekisho_basic_info
Create Date: 2026-04-11

履歴書・基本情報の削除に伴い、都道府県マスタ (m_prefecture) も
DevForge のスコープから外す。住所関連フィールドは既に削除済みで、
都道府県を参照するコードは存在しないためテーブルごと drop する。
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0026_drop_m_prefecture"
down_revision: Union[str, None] = "0025_remove_rirekisho_basic_info"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("m_prefecture")


def downgrade() -> None:
    raise NotImplementedError(
        "0026_drop_m_prefecture は不可逆的な削除のためロールバック不可"
    )
