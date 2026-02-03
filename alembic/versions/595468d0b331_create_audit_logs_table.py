"""create_audit_logs_table

Revision ID: 595468d0b331
Revises: 32df100854bb
Create Date: 2026-01-30 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "595468d0b331"
down_revision: str | Sequence[str] | None = "32df100854bb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create audit_logs table for blocked query tracking.

    Per FR-008: This table intentionally does NOT include
    any user identification fields to protect privacy.
    """
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("blocked_query", sa.Text(), nullable=False),
        sa.Column("original_prompt", sa.Text(), nullable=False),
        sa.Column("blocked_command", sa.String(length=50), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # Index for timestamp-based queries (DESC for recent-first)
    op.create_index(
        "idx_audit_log_timestamp",
        "audit_logs",
        ["timestamp"],
        postgresql_ops={"timestamp": "DESC"},
    )
    # Index for filtering by blocked command
    op.create_index("idx_audit_log_blocked_command", "audit_logs", ["blocked_command"])


def downgrade() -> None:
    """Drop audit_logs table."""
    op.drop_index("idx_audit_log_blocked_command", table_name="audit_logs")
    op.drop_index("idx_audit_log_timestamp", table_name="audit_logs")
    op.drop_table("audit_logs")
