"""add email to users

Revision ID: 0007_add_email_to_users
Revises: 0006_add_user_id_to_documents
Create Date: 2026-03-12 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_add_email_to_users"
down_revision: Union[str, None] = "0006_add_user_id_to_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text("PRAGMA table_info(users)"))
    columns = [row[1] for row in result.fetchall()]
    if "email" not in columns:
        op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    with op.batch_alter_table("users") as batch_op:
        batch_op.create_unique_constraint("uq_users_email", ["email"])


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_email", type_="unique")
        batch_op.drop_column("email")
