"""Catalog repository for managing external sources and column metadata."""

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.catalog import ColumnMetadata, ExternalSource


class CatalogRepository:
    """Repository for catalog CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def create_or_update_source(
        self, db_name: str, table_name: str, document_count: int
    ) -> ExternalSource:
        """Create or update an external source.

        Args:
            db_name: Database name.
            table_name: Table name.
            document_count: Number of documents sampled.

        Returns:
            The created or updated ExternalSource.
        """
        # Check if source exists
        stmt = select(ExternalSource).where(
            ExternalSource.db_name == db_name,
            ExternalSource.table_name == table_name,
        )
        result = await self._session.execute(stmt)
        source = result.scalar_one_or_none()

        if source is None:
            # Create new source
            source = ExternalSource(
                db_name=db_name,
                table_name=table_name,
                document_count=document_count,
            )
            self._session.add(source)
        else:
            # Update existing source
            source.document_count = document_count

        await self._session.flush()
        await self._session.refresh(source)
        return source

    async def get_source_by_id(self, source_id: int) -> ExternalSource | None:
        """Get a source by its ID.

        Args:
            source_id: The source ID.

        Returns:
            The ExternalSource or None if not found.
        """
        stmt = select(ExternalSource).where(ExternalSource.id == source_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_source_by_identity(
        self, db_name: str, table_name: str
    ) -> ExternalSource | None:
        """Get a source by database and table name.

        Args:
            db_name: Database name.
            table_name: Table name.

        Returns:
            The ExternalSource or None if not found.
        """
        stmt = select(ExternalSource).where(
            ExternalSource.db_name == db_name,
            ExternalSource.table_name == table_name,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sources(
        self, db_name: str | None = None, skip: int = 0, limit: int = 100
    ) -> list[ExternalSource]:
        """List external sources with optional filtering.

        Args:
            db_name: Optional filter by database name.
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of ExternalSource objects.
        """
        stmt = select(ExternalSource)

        if db_name:
            stmt = stmt.where(ExternalSource.db_name == db_name)

        stmt = stmt.offset(skip).limit(limit).order_by(ExternalSource.id)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_sources(self, db_name: str | None = None) -> int:
        """Count total sources.

        Args:
            db_name: Optional filter by database name.

        Returns:
            Total count.
        """
        from sqlalchemy import func

        stmt = select(func.count()).select_from(ExternalSource)

        if db_name:
            stmt = stmt.where(ExternalSource.db_name == db_name)

        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def delete_source(self, source_id: int) -> bool:
        """Delete a source and its columns (cascade).

        Args:
            source_id: The source ID.

        Returns:
            True if deleted, False if not found.
        """
        source = await self.get_source_by_id(source_id)
        if source is None:
            return False

        await self._session.delete(source)
        return True

    async def upsert_columns(
        self, source_id: int, columns: list[dict[str, Any]]
    ) -> list[ColumnMetadata]:
        """Replace all columns for a source with new data.

        This performs a delete + insert for simplicity in v1.

        Args:
            source_id: The source ID.
            columns: List of column data dictionaries.

        Returns:
            List of created ColumnMetadata objects.
        """
        # Delete existing columns
        delete_stmt = delete(ColumnMetadata).where(
            ColumnMetadata.source_id == source_id
        )
        await self._session.execute(delete_stmt)

        # Insert new columns
        new_columns: list[ColumnMetadata] = []
        for col_data in columns:
            column = ColumnMetadata(
                source_id=source_id,
                column_name=col_data.get("column_name", ""),
                column_path=col_data.get("column_path", ""),
                inferred_type=str(col_data.get("inferred_type", "unknown")),
                is_required=col_data.get("is_required", False),
                is_nullable=col_data.get("is_nullable", True),
                is_enumerable=col_data.get("is_enumerable", False),
                unique_values=col_data.get("unique_values"),
                sample_values=col_data.get("sample_values"),
                presence_ratio=col_data.get("presence_ratio", 0.0),
                description=col_data.get("description"),
                enrichment_status=col_data.get("enrichment_status", "not_enriched"),
            )
            self._session.add(column)
            new_columns.append(column)

        await self._session.flush()
        return new_columns

    async def get_columns(
        self,
        source_id: int,
        inferred_type: str | None = None,
        is_required: bool | None = None,
        is_enumerable: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ColumnMetadata]:
        """Get columns for a source with optional filters.

        Args:
            source_id: The source ID.
            inferred_type: Optional type filter.
            is_required: Optional required filter.
            is_enumerable: Optional enumerable filter.
            skip: Records to skip.
            limit: Maximum records.

        Returns:
            List of ColumnMetadata objects.
        """
        stmt = select(ColumnMetadata).where(ColumnMetadata.source_id == source_id)

        if inferred_type:
            stmt = stmt.where(ColumnMetadata.inferred_type == inferred_type)
        if is_required is not None:
            stmt = stmt.where(ColumnMetadata.is_required == is_required)
        if is_enumerable is not None:
            stmt = stmt.where(ColumnMetadata.is_enumerable == is_enumerable)

        stmt = stmt.offset(skip).limit(limit).order_by(ColumnMetadata.id)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_columns(
        self,
        source_id: int,
        inferred_type: str | None = None,
        is_required: bool | None = None,
        is_enumerable: bool | None = None,
    ) -> int:
        """Count columns for a source.

        Args:
            source_id: The source ID.
            inferred_type: Optional type filter.
            is_required: Optional required filter.
            is_enumerable: Optional enumerable filter.

        Returns:
            Total count.
        """
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(ColumnMetadata)
            .where(ColumnMetadata.source_id == source_id)
        )

        if inferred_type:
            stmt = stmt.where(ColumnMetadata.inferred_type == inferred_type)
        if is_required is not None:
            stmt = stmt.where(ColumnMetadata.is_required == is_required)
        if is_enumerable is not None:
            stmt = stmt.where(ColumnMetadata.is_enumerable == is_enumerable)

        result = await self._session.execute(stmt)
        return result.scalar() or 0
