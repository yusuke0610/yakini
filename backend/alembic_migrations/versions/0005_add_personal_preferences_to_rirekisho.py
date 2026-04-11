"""add personal_preferences to rirekisho

Revision ID: 0005_add_personal_preferences_to_rirekisho
Revises: 0004_add_github_id_to_users
Create Date: 2026-03-12 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_add_personal_preferences_to_rirekisho"
down_revision: Union[str, None] = "0004_add_github_id_to_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "rirekisho", sa.Column("personal_preferences", sa.Text(), nullable=False, server_default="")
    )


def downgrade() -> None:
    op.drop_column("rirekisho", "personal_preferences")
