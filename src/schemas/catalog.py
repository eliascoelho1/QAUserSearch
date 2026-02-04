"""Pydantic schemas for the catalog API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.enums import EnrichmentStatus, InferredType


# Response schemas
class SourceSummary(BaseModel):
    """Summary of an external source for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Source ID in format db_name.table_name")
    db_name: str
    table_name: str
    column_count: int = Field(default=0)
    enumerable_count: int = Field(default=0)
    cataloged_at: datetime
    updated_at: datetime


class SourceListResponse(BaseModel):
    """Paginated list of sources."""

    items: list[SourceSummary]
    total: int
    skip: int
    limit: int


class ColumnDetail(BaseModel):
    """Detailed information about a column."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Column ID in format source_id.column_path")
    column_name: str
    column_path: str
    inferred_type: InferredType
    is_required: bool
    is_nullable: bool
    is_enumerable: bool
    unique_values: list[Any] | None = None
    sample_values: list[Any] | None = None
    presence_ratio: float = Field(ge=0.0, le=1.0)
    description: str | None = None
    enrichment_status: EnrichmentStatus


class ColumnListResponse(BaseModel):
    """Paginated list of columns."""

    items: list[ColumnDetail]
    total: int
    skip: int
    limit: int


class SourceStats(BaseModel):
    """Statistics for a source."""

    total_columns: int
    required_columns: int
    enumerable_columns: int
    types_distribution: dict[str, int]


class SourceDetailResponse(BaseModel):
    """Detailed information about a source including columns."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Source ID in format db_name.table_name")
    db_name: str
    table_name: str
    document_count: int
    cataloged_at: datetime
    updated_at: datetime
    columns: list[ColumnDetail]
    stats: SourceStats


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: str
    timestamp: datetime
