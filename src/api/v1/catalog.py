"""Catalog API endpoints for schema management."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.database import get_db_manager
from src.schemas.catalog import (
    ColumnDetail,
    ColumnListResponse,
    SourceDetailResponse,
    SourceListResponse,
    SourceStats,
    SourceSummary,
)
from src.schemas.enums import EnrichmentStatus, InferredType
from src.services.catalog_service import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    db_manager = get_db_manager()
    async with db_manager.session() as session:
        yield session


async def get_catalog_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CatalogService:
    """Get catalog service instance."""
    settings = get_settings()
    return CatalogService(
        session=session,
        sample_size=settings.schema_sample_size,
        cardinality_limit=settings.enumerable_cardinality_limit,
    )


@router.get("/sources", response_model=SourceListResponse)
async def list_sources(
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    db_name: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> SourceListResponse:
    """List all cataloged external sources."""
    sources = await service._repository.list_sources(
        db_name=db_name, skip=skip, limit=limit
    )
    total = await service._repository.count_sources(db_name=db_name)

    items = []
    for source in sources:
        # Count columns and enumerables for each source
        column_count = await service._repository.count_columns(source.id)
        enumerable_count = await service._repository.count_columns(
            source.id, is_enumerable=True
        )

        items.append(
            SourceSummary(
                id=source.id,
                db_name=source.db_name,
                table_name=source.table_name,
                column_count=column_count,
                enumerable_count=enumerable_count,
                cataloged_at=source.cataloged_at,
                updated_at=source.updated_at,
            )
        )

    return SourceListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/sources/{source_id}", response_model=SourceDetailResponse)
async def get_source(
    source_id: int,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> SourceDetailResponse:
    """Get detailed information about a specific source."""
    detail = await service.get_source_detail(source_id)

    if detail is None:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    # Convert columns to ColumnDetail
    columns = [
        ColumnDetail(
            id=col.id,
            column_name=col.column_name,
            column_path=col.column_path,
            inferred_type=InferredType(col.inferred_type),
            is_required=col.is_required,
            is_nullable=col.is_nullable,
            is_enumerable=col.is_enumerable,
            unique_values=col.unique_values,
            sample_values=col.sample_values,
            presence_ratio=col.presence_ratio,
            description=col.description,
            enrichment_status=EnrichmentStatus(col.enrichment_status),
        )
        for col in detail["columns"]
    ]

    return SourceDetailResponse(
        id=detail["id"],
        db_name=detail["db_name"],
        table_name=detail["table_name"],
        document_count=detail["document_count"],
        cataloged_at=detail["cataloged_at"],
        updated_at=detail["updated_at"],
        columns=columns,
        stats=SourceStats(**detail["stats"]),
    )


@router.delete("/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: int,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> None:
    """Delete a source and all its columns."""
    deleted = await service.delete_source(source_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")


@router.get("/sources/{source_id}/columns", response_model=ColumnListResponse)
async def list_columns(
    source_id: int,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    type: str | None = Query(default=None, alias="type"),
    is_required: bool | None = None,
    is_enumerable: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> ColumnListResponse:
    """List columns for a source with optional filters."""
    # Verify source exists
    source = await service._repository.get_source_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    columns = await service._repository.get_columns(
        source_id=source_id,
        inferred_type=type,
        is_required=is_required,
        is_enumerable=is_enumerable,
        skip=skip,
        limit=limit,
    )

    total = await service._repository.count_columns(
        source_id=source_id,
        inferred_type=type,
        is_required=is_required,
        is_enumerable=is_enumerable,
    )

    items = [
        ColumnDetail(
            id=col.id,
            column_name=col.column_name,
            column_path=col.column_path,
            inferred_type=InferredType(col.inferred_type),
            is_required=col.is_required,
            is_nullable=col.is_nullable,
            is_enumerable=col.is_enumerable,
            unique_values=col.unique_values,
            sample_values=col.sample_values,
            presence_ratio=col.presence_ratio,
            description=col.description,
            enrichment_status=EnrichmentStatus(col.enrichment_status),
        )
        for col in columns
    ]

    return ColumnListResponse(items=items, total=total, skip=skip, limit=limit)
