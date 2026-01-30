"""SQLAlchemy model for column metadata."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.catalog.external_source import ExternalSource


class ColumnMetadata(Base):
    """Represents metadata for a column within an external source."""

    __tablename__ = "column_metadata"
    __table_args__ = (
        UniqueConstraint("source_id", "column_path", name="uq_column_identity"),
        CheckConstraint(
            "presence_ratio >= 0.0 AND presence_ratio <= 1.0",
            name="ck_presence_ratio",
        ),
        CheckConstraint(
            "enrichment_status IN ('not_enriched', 'pending_enrichment', 'enriched')",
            name="ck_enrichment_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("external_sources.id", ondelete="CASCADE"), index=True
    )
    column_name: Mapped[str] = mapped_column(String(255))
    column_path: Mapped[str] = mapped_column(String(500))
    inferred_type: Mapped[str] = mapped_column(String(50), index=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_enumerable: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    unique_values: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    sample_values: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    presence_ratio: Mapped[float] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    enrichment_status: Mapped[str] = mapped_column(
        String(20), default="not_enriched", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    source: Mapped["ExternalSource"] = relationship(back_populates="columns")
