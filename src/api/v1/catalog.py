"""Catalog API endpoints for schema management."""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.database import get_db_manager
from src.schemas.catalog import (
    BatchExtractionResponse,
    BatchExtractionTask,
    ColumnDetail,
    ColumnListResponse,
    ExtractionRequest,
    ExtractionResult,
    ExtractionStatusResponse,
    ExtractionTaskResponse,
    SourceDetailResponse,
    SourceListResponse,
    SourceStats,
    SourceSummary,
)
from src.schemas.enums import EnrichmentStatus, InferredType
from src.services.catalog_service import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])

# In-memory task store (for v1 - could be Redis in production)
task_store: dict[str, dict[str, Any]] = {}


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


# Known sources for batch extraction
KNOWN_SOURCES = [
    ("card_account_authorization", "account_main"),
    ("card_account_authorization", "card_main"),
    ("credit", "invoice"),
    ("credit", "closed_invoice"),
]


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


async def run_extraction_task(
    task_id: str,
    db_name: str,
    table_name: str,
    sample_size: int,
) -> None:
    """Background task to run schema extraction."""
    from src.core.database import get_db_manager

    task_store[task_id]["status"] = "running"
    task_store[task_id]["started_at"] = datetime.utcnow().isoformat()

    try:
        db_manager = get_db_manager()
        settings = get_settings()

        async with db_manager.session() as session:
            service = CatalogService(
                session=session,
                sample_size=sample_size,
                cardinality_limit=settings.enumerable_cardinality_limit,
            )
            result = await service.extract_and_persist(
                db_name=db_name,
                table_name=table_name,
                sample_size=sample_size,
            )

        task_store[task_id]["status"] = "completed"
        task_store[task_id]["result"] = result
        task_store[task_id]["completed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        task_store[task_id]["status"] = "failed"
        task_store[task_id]["error"] = str(e)
        task_store[task_id]["completed_at"] = datetime.utcnow().isoformat()


@router.post("/extraction", response_model=ExtractionTaskResponse, status_code=202)
async def start_extraction(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks,
    _service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ExtractionTaskResponse:
    """Start an asynchronous schema extraction task."""
    task_id = str(uuid.uuid4())
    created_at = datetime.utcnow()

    task_store[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "db_name": request.db_name,
        "table_name": request.table_name,
        "created_at": created_at.isoformat(),
    }

    background_tasks.add_task(
        run_extraction_task,
        task_id=task_id,
        db_name=request.db_name,
        table_name=request.table_name,
        sample_size=request.sample_size,
    )

    return ExtractionTaskResponse(
        task_id=task_id,
        status="pending",
        message="Extração iniciada com sucesso",
        created_at=created_at,
    )


@router.get("/extraction/{task_id}", response_model=ExtractionStatusResponse)
async def get_extraction_status(task_id: str) -> ExtractionStatusResponse:
    """Get the status of an extraction task."""
    task = task_store.get(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    result = None
    if task.get("result"):
        result = ExtractionResult(**task["result"])

    return ExtractionStatusResponse(
        task_id=task["task_id"],
        status=task["status"],
        result=result,
        error=task.get("error"),
        started_at=(
            datetime.fromisoformat(task["started_at"])
            if task.get("started_at")
            else None
        ),
        completed_at=(
            datetime.fromisoformat(task["completed_at"])
            if task.get("completed_at")
            else None
        ),
    )


@router.post("/extraction/all", response_model=BatchExtractionResponse, status_code=202)
async def start_batch_extraction(
    background_tasks: BackgroundTasks,
    _service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> BatchExtractionResponse:
    """Start extraction for all known sources."""
    batch_id = str(uuid.uuid4())
    settings = get_settings()
    tasks = []

    for db_name, table_name in KNOWN_SOURCES:
        task_id = str(uuid.uuid4())
        created_at = datetime.utcnow()

        task_store[task_id] = {
            "task_id": task_id,
            "batch_id": batch_id,
            "status": "pending",
            "db_name": db_name,
            "table_name": table_name,
            "created_at": created_at.isoformat(),
        }

        background_tasks.add_task(
            run_extraction_task,
            task_id=task_id,
            db_name=db_name,
            table_name=table_name,
            sample_size=settings.schema_sample_size,
        )

        tasks.append(
            BatchExtractionTask(
                task_id=task_id,
                db_name=db_name,
                table_name=table_name,
            )
        )

    return BatchExtractionResponse(
        batch_id=batch_id,
        tasks=tasks,
        total_tasks=len(tasks),
    )
