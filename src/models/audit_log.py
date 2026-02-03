"""SQLAlchemy model for audit log of blocked queries.

Per FR-008: Logs blocked queries WITHOUT user identification.
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.core.database import Base


class AuditLog(Base):
    """Log of blocked queries for audit purposes.

    Note: Per FR-008, this model intentionally does NOT include
    any user identification fields to protect privacy.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index(
            "idx_audit_log_timestamp", "timestamp", postgresql_ops={"timestamp": "DESC"}
        ),
        Index("idx_audit_log_blocked_command", "blocked_command"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    blocked_query: Mapped[str] = mapped_column(Text, nullable=False)
    original_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    blocked_command: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(500), nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, blocked_command={self.blocked_command}, timestamp={self.timestamp})>"
