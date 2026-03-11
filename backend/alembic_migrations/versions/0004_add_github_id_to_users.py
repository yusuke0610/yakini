"""add github_id to users

Revision ID: 0004_add_github_id_to_users
Revises: 0003_add_photo_to_rirekisho
Create Date: 2026-03-11 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_add_github_id_to_users"
down_revision: Union[str, None] = "0003_add_photo_to_rirekisho"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("github_id", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_users_github_id", "users", ["github_id"])


def downgrade() -> None:
    op.drop_constraint("uq_users_github_id", "users", type_="unique")
    op.drop_column("users", "github_id")
