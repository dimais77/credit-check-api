"""add position to documents and issues

Revision ID: 097dac109ea7
Revises: aea850cab3a3
Create Date: 2026-07-10 19:01:54.862876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '097dac109ea7'
down_revision: Union[str, Sequence[str], None] = 'aea850cab3a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    for table in ("documents", "issues"):
        op.add_column(
            table, sa.Column("position", sa.Integer(), nullable=False, server_default="0")
        )
        op.alter_column(table, "position", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("issues", "position")
    op.drop_column("documents", "position")
