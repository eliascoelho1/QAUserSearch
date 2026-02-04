"""Catalog API endpoints for schema management using YAML files."""

from typing import Annotated

import structlog
import yaml
from fastapi import APIRouter, Depends, HTTPException, Query

from src.dependencies.catalog import get_catalog_repository
from src.repositories.catalog.file_repository import CatalogFileRepository
from src.schemas.catalog import (
    ColumnDetail,
    ColumnListResponse,
    ErrorResponse,
    SourceDetailResponse,
    SourceListResponse,
    SourceStats,
    SourceSummary,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])
logger = structlog.get_logger(__name__)


@router.get("/sources", response_model=SourceListResponse)
async def list_sources(
    repository: Annotated[CatalogFileRepository, Depends(get_catalog_repository)],
    db_name: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> SourceListResponse:
    """List all cataloged external sources."""
    log = logger.bind(db_name=db_name, skip=skip, limit=limit)
    log.info("Listing catalog sources")

    try:
        sources = await repository.list_sources(db_name=db_name, skip=skip, limit=limit)
        total = await repository.count_sources(db_name=db_name)

        items: list[SourceSummary] = []
        for source in sources:
            # Count columns and enumerables for each source
            column_count = len(source.columns)
            enumerable_count = sum(1 for c in source.columns if c.enumerable)

            items.append(
                SourceSummary(
                    id=source.source_id,
                    db_name=source.db_name,
                    table_name=source.table_name,
                    column_count=column_count,
                    enumerable_count=enumerable_count,
                    cataloged_at=source.extracted_at,
                    updated_at=source.updated_at or source.extracted_at,
                )
            )

        log.info("Listed sources successfully", total=total, returned=len(items))
        return SourceListResponse(items=items, total=total, skip=skip, limit=limit)

    except yaml.YAMLError as e:
        log.error("YAML parsing error while listing sources", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to parse catalog files. Please check YAML syntax.",
        ) from e


@router.get(
    "/sources/{source_id}",
    response_model=SourceDetailResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_source(
    source_id: str,
    repository: Annotated[CatalogFileRepository, Depends(get_catalog_repository)],
) -> SourceDetailResponse:
    """Get detailed information about a specific source.

    Args:
        source_id: Source ID in format db_name.table_name (e.g., credit.invoice)
        repository: Catalog repository dependency.

    Returns:
        Detailed source information including columns and stats.

    Raises:
        HTTPException: 404 if source not found, 500 if YAML parsing fails.
    """
    log = logger.bind(source_id=source_id)
    log.info("Getting source detail")

    try:
        detail = await repository.get_source_detail(source_id)

        if detail is None:
            log.warning("Source not found")
            raise HTTPException(
                status_code=404, detail=f"Source '{source_id}' not found"
            )

        # Convert columns to ColumnDetail
        columns = [
            ColumnDetail(
                id=f"{source_id}.{col.path}",
                column_name=col.name,
                column_path=col.path,
                inferred_type=col.type,
                is_required=col.required,
                is_nullable=col.nullable,
                is_enumerable=col.enumerable,
                unique_values=col.unique_values,
                sample_values=col.sample_values,
                presence_ratio=col.presence_ratio,
                description=col.description,
                enrichment_status=col.enrichment_status,
            )
            for col in detail["columns"]
        ]

        log.info("Retrieved source detail successfully", column_count=len(columns))
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

    except yaml.YAMLError as e:
        log.error("YAML parsing error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse YAML file for source '{source_id}'. Please check file syntax.",
        ) from e


@router.get(
    "/sources/{source_id}/columns",
    response_model=ColumnListResponse,
    responses={404: {"model": ErrorResponse}},
)
async def list_columns(
    source_id: str,
    repository: Annotated[CatalogFileRepository, Depends(get_catalog_repository)],
    type: str | None = Query(default=None, alias="type"),
    is_required: bool | None = None,
    is_enumerable: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> ColumnListResponse:
    """List columns for a source with optional filters.

    Args:
        source_id: Source ID in format db_name.table_name (e.g., credit.invoice)
        repository: Catalog repository dependency.
        type: Optional filter by inferred type.
        is_required: Optional filter by required status.
        is_enumerable: Optional filter by enumerable status.
        skip: Number of records to skip.
        limit: Maximum number of records.

    Returns:
        Paginated list of columns matching filters.

    Raises:
        HTTPException: 404 if source not found.
    """
    log = logger.bind(
        source_id=source_id,
        type=type,
        is_required=is_required,
        is_enumerable=is_enumerable,
        skip=skip,
        limit=limit,
    )
    log.info("Listing columns for source")

    # Verify source exists
    source = await repository.get_source_by_id(source_id)
    if source is None:
        log.warning("Source not found")
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")

    try:
        columns = await repository.get_columns(
            source_id=source_id,
            inferred_type=type,
            is_required=is_required,
            is_enumerable=is_enumerable,
            skip=skip,
            limit=limit,
        )

        total = await repository.count_columns(
            source_id=source_id,
            inferred_type=type,
            is_required=is_required,
            is_enumerable=is_enumerable,
        )

        items = [
            ColumnDetail(
                id=f"{source_id}.{col.path}",
                column_name=col.name,
                column_path=col.path,
                inferred_type=col.type,
                is_required=col.required,
                is_nullable=col.nullable,
                is_enumerable=col.enumerable,
                unique_values=col.unique_values,
                sample_values=col.sample_values,
                presence_ratio=col.presence_ratio,
                description=col.description,
                enrichment_status=col.enrichment_status,
            )
            for col in columns
        ]

        log.info("Listed columns successfully", total=total, returned=len(items))
        return ColumnListResponse(items=items, total=total, skip=skip, limit=limit)

    except yaml.YAMLError as e:
        log.error("YAML parsing error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse YAML file for source '{source_id}'. Please check file syntax.",
        ) from e
