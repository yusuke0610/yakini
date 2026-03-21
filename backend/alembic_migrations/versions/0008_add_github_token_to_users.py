"""add github_token to users

Revision ID: 0008_add_github_token_to_users
Revises: 0007_add_email_to_users
Create Date: 2026-03-14 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_add_github_token_to_users"
down_revision: Union[str, None] = "0007_add_email_to_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text("PRAGMA table_info(users)"))
    columns = [row[1] for row in result.fetchall()]
    if "github_token" not in columns:
        op.add_column("users", sa.Column("github_token", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("github_token")
