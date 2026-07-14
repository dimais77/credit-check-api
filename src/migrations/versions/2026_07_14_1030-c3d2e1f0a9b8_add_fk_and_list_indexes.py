"""add fk and list indexes

Revision ID: c3d2e1f0a9b8
Revises: b2c1d0e9f8a7
Create Date: 2026-07-14 10:30:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3d2e1f0a9b8"
down_revision: str | Sequence[str] | None = "b2c1d0e9f8a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index("ix_documents_check_id", "documents", ["check_id"])
    op.create_index("ix_issues_check_id", "issues", ["check_id"])
    op.create_index("ix_checks_checked_at_id", "checks", ["checked_at", "id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_checks_checked_at_id", table_name="checks")
    op.drop_index("ix_issues_check_id", table_name="issues")
    op.drop_index("ix_documents_check_id", table_name="documents")