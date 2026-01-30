"""SQLAlchemy model for external data sources."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.catalog.column_metadata import ColumnMetadata


class ExternalSource(Base):
    """Represents an external data source (database + table combination)."""

    __tablename__ = "external_sources"
    __table_args__ = (
        UniqueConstraint("db_name", "table_name", name="uq_source_identity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    db_name: Mapped[str] = mapped_column(String(100), index=True)
    table_name: Mapped[str] = mapped_column(String(100), index=True)
    cataloged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    document_count: Mapped[int] = mapped_column(Integer, default=0)

    columns: Mapped[list["ColumnMetadata"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
