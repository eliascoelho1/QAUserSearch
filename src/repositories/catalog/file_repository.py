"""File-based catalog repository using YAML files."""

from pathlib import Path
from typing import Any

import structlog
import yaml

from src.repositories.catalog.cache import AsyncTTLCache
from src.schemas.catalog_yaml import (
    CatalogIndex,
    ColumnMetadataYaml,
    IndexEntry,
    SourceMetadataYaml,
)

logger = structlog.get_logger(__name__)


class CatalogFileRepository:
    """Repository for reading catalog metadata from YAML files.

    This repository reads catalog data from YAML files stored in the filesystem.
    It uses an in-memory TTL cache to reduce file I/O for repeated reads.

    Attributes:
        _catalog_path: Base path for catalog files.
        _index_cache: Cache for the catalog index.
        _source_cache: Cache for individual source files.
    """

    def __init__(
        self,
        catalog_path: str | Path,
        cache_ttl_seconds: float = 60.0,
    ) -> None:
        """Initialize the file repository.

        Args:
            catalog_path: Path to the catalog directory.
            cache_ttl_seconds: TTL for cache entries in seconds.
        """
        self._catalog_path = Path(catalog_path)
        self._index_cache: AsyncTTLCache[CatalogIndex] = AsyncTTLCache(
            ttl_seconds=cache_ttl_seconds
        )
        self._source_cache: AsyncTTLCache[SourceMetadataYaml] = AsyncTTLCache(
            ttl_seconds=cache_ttl_seconds
        )
        self._log = logger.bind(catalog_path=str(catalog_path))

    @property
    def catalog_path(self) -> Path:
        """Get the catalog base path."""
        return self._catalog_path

    async def _load_index(self) -> CatalogIndex:
        """Load the catalog index from YAML file.

        Returns:
            CatalogIndex object.

        Raises:
            FileNotFoundError: If catalog.yaml doesn't exist.
            yaml.YAMLError: If YAML parsing fails.
        """
        index_path = self._catalog_path / "catalog.yaml"
        self._log.debug("Loading catalog index", path=str(index_path))

        if not index_path.exists():
            self._log.warning("Catalog index not found, returning empty index")
            # Return empty index if file doesn't exist
            import datetime as dt

            return CatalogIndex(
                version="1.0",
                generated_at=dt.datetime.now(dt.UTC),
                sources=[],
            )

        with index_path.open("r", encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}

        return CatalogIndex.from_yaml_dict(data)

    async def _load_source(self, file_path: str) -> SourceMetadataYaml:
        """Load a source metadata file.

        Args:
            file_path: Relative path to the source YAML file.

        Returns:
            SourceMetadataYaml object.

        Raises:
            FileNotFoundError: If source file doesn't exist.
            yaml.YAMLError: If YAML parsing fails.
        """
        full_path = self._catalog_path / file_path
        self._log.debug("Loading source file", path=str(full_path))

        with full_path.open("r", encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}

        return SourceMetadataYaml.from_yaml_dict(data)

    async def _get_index(self) -> CatalogIndex:
        """Get catalog index with caching.

        Returns:
            CatalogIndex object.
        """
        return await self._index_cache.get_or_load("index", self._load_index)

    async def _load_source_cached(self, entry: IndexEntry) -> SourceMetadataYaml:
        """Load source with caching using an index entry.

        Args:
            entry: Index entry for the source.

        Returns:
            SourceMetadataYaml object.
        """
        return await self._source_cache.get_or_load(
            entry.source_id,
            lambda: self._load_source(entry.file_path),
        )

    async def get_source_by_id(self, source_id: str) -> SourceMetadataYaml | None:
        """Get source metadata by composite ID.

        Args:
            source_id: The source ID in format db_name.table_name.

        Returns:
            SourceMetadataYaml if found, None otherwise.
        """
        self._log.debug("Getting source by ID", source_id=source_id)

        # Parse source_id
        parts = source_id.split(".", 1)
        if len(parts) != 2:
            self._log.warning("Invalid source ID format", source_id=source_id)
            return None

        db_name, table_name = parts
        return await self.get_source_by_identity(db_name, table_name)

    async def get_source_by_identity(
        self, db_name: str, table_name: str
    ) -> SourceMetadataYaml | None:
        """Get source by database and table name.

        Args:
            db_name: Database name.
            table_name: Table name.

        Returns:
            SourceMetadataYaml if found, None otherwise.
        """
        self._log.debug(
            "Getting source by identity", db_name=db_name, table_name=table_name
        )

        index = await self._get_index()
        entry = index.find_source(db_name, table_name)

        if entry is None:
            self._log.debug(
                "Source not found in index", db_name=db_name, table_name=table_name
            )
            return None

        # Load source file with caching
        try:
            return await self._source_cache.get_or_load(
                entry.source_id,
                lambda: self._load_source(entry.file_path),
            )
        except FileNotFoundError:
            self._log.error(
                "Source file not found",
                file_path=entry.file_path,
                db_name=db_name,
                table_name=table_name,
            )
            return None
        except yaml.YAMLError as e:
            self._log.error(
                "YAML parsing error",
                file_path=entry.file_path,
                error=str(e),
            )
            raise

    async def list_sources(
        self, db_name: str | None = None, skip: int = 0, limit: int = 100
    ) -> list[SourceMetadataYaml]:
        """List sources with optional filtering.

        Args:
            db_name: Optional filter by database name.
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            List of SourceMetadataYaml objects.
        """
        self._log.debug("Listing sources", db_name=db_name, skip=skip, limit=limit)

        index = await self._get_index()

        # Filter by db_name if provided
        entries = index.sources
        if db_name:
            entries = [e for e in entries if e.db_name == db_name]

        # Apply pagination
        paginated = entries[skip : skip + limit]

        # Load each source
        sources: list[SourceMetadataYaml] = []
        for entry in paginated:
            try:
                source = await self._load_source_cached(entry)
                sources.append(source)
            except FileNotFoundError:
                self._log.warning(
                    "Source file missing, skipping",
                    source_id=entry.source_id,
                    file_path=entry.file_path,
                )
            except yaml.YAMLError as e:
                self._log.error(
                    "YAML parsing error, skipping",
                    source_id=entry.source_id,
                    error=str(e),
                )

        return sources

    async def count_sources(self, db_name: str | None = None) -> int:
        """Count total sources.

        Args:
            db_name: Optional filter by database name.

        Returns:
            Total count.
        """
        index = await self._get_index()

        if db_name:
            return sum(1 for e in index.sources if e.db_name == db_name)

        return len(index.sources)

    async def get_source_detail(self, source_id: str) -> dict[str, Any] | None:
        """Get detailed information about a source.

        Args:
            source_id: The source ID in format db_name.table_name.

        Returns:
            Source details with columns and stats, or None if not found.
        """
        source = await self.get_source_by_id(source_id)
        if source is None:
            return None

        # Calculate stats
        types_distribution: dict[str, int] = {}
        required_count = 0
        enumerable_count = 0

        for col in source.columns:
            col_type = col.type.value
            types_distribution[col_type] = types_distribution.get(col_type, 0) + 1

            if col.required:
                required_count += 1
            if col.enumerable:
                enumerable_count += 1

        return {
            "id": source.source_id,
            "db_name": source.db_name,
            "table_name": source.table_name,
            "document_count": source.document_count,
            "cataloged_at": source.extracted_at,
            "updated_at": source.updated_at or source.extracted_at,
            "columns": source.columns,
            "stats": {
                "total_columns": len(source.columns),
                "required_columns": required_count,
                "enumerable_columns": enumerable_count,
                "types_distribution": types_distribution,
            },
        }

    async def get_columns(
        self,
        source_id: str,
        inferred_type: str | None = None,
        is_required: bool | None = None,
        is_enumerable: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ColumnMetadataYaml]:
        """Get columns for a source with optional filters.

        Args:
            source_id: The source ID.
            inferred_type: Optional type filter.
            is_required: Optional required filter.
            is_enumerable: Optional enumerable filter.
            skip: Records to skip.
            limit: Maximum records.

        Returns:
            List of ColumnMetadataYaml objects.
        """
        source = await self.get_source_by_id(source_id)
        if source is None:
            return []

        columns = source.columns

        # Apply filters
        if inferred_type:
            columns = [c for c in columns if c.type.value == inferred_type]
        if is_required is not None:
            columns = [c for c in columns if c.required == is_required]
        if is_enumerable is not None:
            columns = [c for c in columns if c.enumerable == is_enumerable]

        # Apply pagination
        return columns[skip : skip + limit]

    async def count_columns(
        self,
        source_id: str,
        inferred_type: str | None = None,
        is_required: bool | None = None,
        is_enumerable: bool | None = None,
    ) -> int:
        """Count columns for a source with optional filters.

        Args:
            source_id: The source ID.
            inferred_type: Optional type filter.
            is_required: Optional required filter.
            is_enumerable: Optional enumerable filter.

        Returns:
            Total count.
        """
        source = await self.get_source_by_id(source_id)
        if source is None:
            return 0

        columns = source.columns

        # Apply filters
        if inferred_type:
            columns = [c for c in columns if c.type.value == inferred_type]
        if is_required is not None:
            columns = [c for c in columns if c.required == is_required]
        if is_enumerable is not None:
            columns = [c for c in columns if c.enumerable == is_enumerable]

        return len(columns)

    def invalidate_cache(self) -> None:
        """Invalidate all cached data."""
        self._index_cache.clear()
        self._source_cache.clear()
        self._log.info("Cache invalidated")
