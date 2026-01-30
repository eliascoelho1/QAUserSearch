"""Mock external data source repository for local JSON files."""

import json
from pathlib import Path
from typing import Any

import aiofiles


class MockExternalDataSource:
    """External data source that reads from local JSON files in res/db/."""

    def __init__(self, base_path: str = "res/db") -> None:
        """Initialize the mock data source.

        Args:
            base_path: Base directory path for JSON files.
        """
        self._base_path = Path(base_path)

    async def get_sample_documents(
        self, db_name: str, table_name: str, sample_size: int
    ) -> list[dict[str, Any]]:
        """Get sample documents from a local JSON file.

        The file should be named: {db_name}.{table_name}.json

        Args:
            db_name: The database name.
            table_name: The table/collection name.
            sample_size: Maximum number of documents to return.

        Returns:
            A list of documents from the JSON file.

        Raises:
            FileNotFoundError: If the JSON file doesn't exist.
        """
        file_name = f"{db_name}.{table_name}.json"
        file_path = self._base_path / file_name

        if not file_path.exists():
            raise FileNotFoundError(
                f"Sample file not found: {file_path}. "
                f"Expected format: {db_name}.{table_name}.json"
            )

        async with aiofiles.open(file_path, encoding="utf-8") as f:
            content = await f.read()
            documents = json.loads(content)

        # Return up to sample_size documents
        if isinstance(documents, list):
            return documents[:sample_size]

        return [documents]

    async def list_tables(self, db_name: str) -> list[str]:
        """List all tables available for a database.

        Scans the res/db/ directory for files matching {db_name}.*.json

        Args:
            db_name: The database name to filter by.

        Returns:
            A list of table names.
        """
        tables: list[str] = []

        if not self._base_path.exists():
            return tables

        for file_path in self._base_path.glob(f"{db_name}.*.json"):
            # Extract table name from filename
            # Format: db_name.table_name.json
            parts = file_path.stem.split(".", 1)
            if len(parts) == 2:
                tables.append(parts[1])

        return sorted(tables)
