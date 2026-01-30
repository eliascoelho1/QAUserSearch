"""Base protocol for external data sources."""

from typing import Any, Protocol


class ExternalDataSource(Protocol):
    """Protocol for accessing external data sources."""

    async def get_sample_documents(
        self, db_name: str, table_name: str, sample_size: int
    ) -> list[dict[str, Any]]:
        """Get a sample of documents from an external source.

        Args:
            db_name: The name of the database.
            table_name: The name of the table/collection.
            sample_size: Number of documents to sample.

        Returns:
            A list of sample documents as dictionaries.
        """
        ...

    async def list_tables(self, db_name: str) -> list[str]:
        """List all tables/collections in a database.

        Args:
            db_name: The name of the database.

        Returns:
            A list of table/collection names.
        """
        ...
