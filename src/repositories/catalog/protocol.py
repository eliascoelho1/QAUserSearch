"""Protocol definition for catalog repositories."""

from typing import Any, Protocol

from src.schemas.catalog_yaml import SourceMetadataYaml


class CatalogRepositoryProtocol(Protocol):
    """Protocol for catalog data access.

    This protocol defines the interface for accessing catalog metadata.
    Implementations can be backed by files (YAML), databases, or other storage.
    """

    async def get_source_by_id(self, source_id: str) -> SourceMetadataYaml | None:
        """Get source metadata by composite ID.

        Args:
            source_id: The source ID in format db_name.table_name.

        Returns:
            SourceMetadataYaml if found, None otherwise.
        """
        ...

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
        ...

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
        ...

    async def count_sources(self, db_name: str | None = None) -> int:
        """Count total sources.

        Args:
            db_name: Optional filter by database name.

        Returns:
            Total count.
        """
        ...

    async def get_source_detail(self, source_id: str) -> dict[str, Any] | None:
        """Get detailed information about a source.

        Args:
            source_id: The source ID in format db_name.table_name.

        Returns:
            Source details with columns and stats, or None if not found.
        """
        ...
