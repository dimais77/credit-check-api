"""add created_by to checks

Revision ID: e5f4a3b2c1d0
Revises: d4e3f2a1b0c9
Create Date: 2026-07-14 11:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f4a3b2c1d0"
down_revision: str | Sequence[str] | None = "d4e3f2a1b0c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("checks", sa.Column("created_by", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("checks", "created_by")