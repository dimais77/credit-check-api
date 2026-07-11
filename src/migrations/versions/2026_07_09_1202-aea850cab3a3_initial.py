"""initial

Revision ID: aea850cab3a3
Revises:
Create Date: 2026-07-09 12:02:29.228082

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "aea850cab3a3"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "checks",
        sa.Column("program", sa.Enum("federal", "regional", name="program"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("approved", "rejected", "check_in_progress", name="check_status"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_checks")),
    )
    op.create_table(
        "documents",
        sa.Column("check_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "detected_type",
            sa.Enum("contract", "specification", "invoice", "act", name="document_type"),
            nullable=True,
        ),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["check_id"],
            ["checks.id"],
            name=op.f("fk_documents_check_id_checks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    op.create_table(
        "issues",
        sa.Column("check_id", sa.Uuid(), nullable=False),
        sa.Column("level", sa.Enum("error", "warning", name="issue_level"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["check_id"], ["checks.id"], name=op.f("fk_issues_check_id_checks"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_issues")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("issues")
    op.drop_table("documents")
    op.drop_table("checks")
    op.execute("DROP TYPE issue_level")
    op.execute("DROP TYPE document_type")
    op.execute("DROP TYPE check_status")
    op.execute("DROP TYPE program")
