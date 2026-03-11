"""add photo to rirekisho

Revision ID: 0003_add_photo_to_rirekisho
Revises: 0002_add_users_table
Create Date: 2026-03-11 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_add_photo_to_rirekisho"
down_revision: Union[str, None] = "0002_add_users_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("rirekisho", sa.Column("photo", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("rirekisho", "photo")
