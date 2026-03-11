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
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("github_id", sa.Integer(), nullable=True))
        batch_op.create_unique_constraint("uq_users_github_id", ["github_id"])


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_github_id", type_="unique")
        batch_op.drop_column("github_id")
