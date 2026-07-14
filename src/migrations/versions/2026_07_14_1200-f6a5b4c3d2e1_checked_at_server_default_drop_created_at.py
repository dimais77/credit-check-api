"""checked_at server default, drop created_at

Revision ID: f6a5b4c3d2e1
Revises: e5f4a3b2c1d0
Create Date: 2026-07-14 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6a5b4c3d2e1"
down_revision: str | Sequence[str] | None = "e5f4a3b2c1d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("checks", "checked_at", server_default=sa.text("now()"))
    op.drop_column("checks", "created_at")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "checks",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.alter_column("checks", "checked_at", server_default=None)