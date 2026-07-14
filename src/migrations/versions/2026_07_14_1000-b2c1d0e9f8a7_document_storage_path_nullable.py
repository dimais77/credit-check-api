"""document storage_path nullable

Revision ID: b2c1d0e9f8a7
Revises: f7839b79e3e4
Create Date: 2026-07-14 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c1d0e9f8a7"
down_revision: str | Sequence[str] | None = "f7839b79e3e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("documents", "storage_path", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("documents", "storage_path", existing_type=sa.Text(), nullable=False)