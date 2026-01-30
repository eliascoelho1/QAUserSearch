"""Pydantic schemas for the catalog API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.enums import EnrichmentStatus, InferredType


# Request schemas
class ExtractionRequest(BaseModel):
    """Request to extract schema from an external source."""

    model_config = ConfigDict(strict=True)

    db_name: str = Field(
        ..., min_length=1, max_length=100, description="External database name"
    )
    table_name: str = Field(
        ..., min_length=1, max_length=100, description="Table/collection name"
    )
    sample_size: int = Field(
        default=500, ge=1, le=10000, description="Number of documents to sample"
    )


# Response schemas
class SourceSummary(BaseModel):
    """Summary of an external source for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: int
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

    id: int
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

    id: int
    db_name: str
    table_name: str
    document_count: int
    cataloged_at: datetime
    updated_at: datetime
    columns: list[ColumnDetail]
    stats: SourceStats


class ExtractionTaskResponse(BaseModel):
    """Response for extraction task creation."""

    task_id: str
    status: str = "pending"
    message: str = "Extração iniciada com sucesso"
    created_at: datetime


class ExtractionProgress(BaseModel):
    """Progress information for extraction."""

    current: int
    total: int


class ExtractionResult(BaseModel):
    """Result of a completed extraction."""

    source_id: int
    columns_extracted: int
    enumerable_columns: int


class ExtractionStatusResponse(BaseModel):
    """Status of an extraction task."""

    task_id: str
    status: str
    progress: ExtractionProgress | None = None
    result: ExtractionResult | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class BatchExtractionTask(BaseModel):
    """Individual task in a batch extraction."""

    task_id: str
    db_name: str
    table_name: str


class BatchExtractionResponse(BaseModel):
    """Response for batch extraction."""

    batch_id: str
    tasks: list[BatchExtractionTask]
    total_tasks: int


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: str
    timestamp: datetime
