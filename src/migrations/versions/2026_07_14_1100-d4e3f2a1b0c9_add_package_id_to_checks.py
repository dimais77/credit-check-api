"""add package_id to checks

Revision ID: d4e3f2a1b0c9
Revises: c3d2e1f0a9b8
Create Date: 2026-07-14 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e3f2a1b0c9"
down_revision: str | Sequence[str] | None = "c3d2e1f0a9b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "checks",
        sa.Column(
            "package_id",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.alter_column("checks", "package_id", server_default=None)
    op.create_index("ix_checks_package_id", "checks", ["package_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_checks_package_id", table_name="checks")
    op.drop_column("checks", "package_id")