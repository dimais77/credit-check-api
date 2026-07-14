"""add idempotency keys table

Revision ID: f7839b79e3e4
Revises: 097dac109ea7
Create Date: 2026-07-11 00:38:01.653877

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7839b79e3e4"
down_revision: str | Sequence[str] | None = "097dac109ea7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("check_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["check_id"],
            ["checks.id"],
            name=op.f("fk_idempotency_keys_check_id_checks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_idempotency_keys")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("idempotency_keys")
