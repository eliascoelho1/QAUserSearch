"""Unit tests for CatalogRepository."""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestCatalogRepository:
    """Tests for the catalog repository CRUD operations."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create_source(self, mock_session: AsyncMock) -> None:
        """Test creating a new external source."""
        from src.repositories.catalog.catalog_repository import CatalogRepository

        repo = CatalogRepository(mock_session)

        # Mock the execute to return None (no existing source)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await repo.create_or_update_source(
            db_name="test_db",
            table_name="test_table",
            document_count=100
        )

        assert mock_session.add.called
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_get_source_by_id(self, mock_session: AsyncMock) -> None:
        """Test retrieving a source by ID."""
        from src.models.catalog import ExternalSource
        from src.repositories.catalog.catalog_repository import CatalogRepository

        repo = CatalogRepository(mock_session)

        # Mock existing source
        mock_source = MagicMock(spec=ExternalSource)
        mock_source.id = 1
        mock_source.db_name = "test_db"
        mock_source.table_name = "test_table"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_source
        mock_session.execute.return_value = mock_result

        result = await repo.get_source_by_id(1)

        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_list_sources(self, mock_session: AsyncMock) -> None:
        """Test listing all sources."""
        from src.models.catalog import ExternalSource
        from src.repositories.catalog.catalog_repository import CatalogRepository

        repo = CatalogRepository(mock_session)

        # Mock sources list
        mock_sources = [
            MagicMock(spec=ExternalSource, id=1, db_name="db1", table_name="table1"),
            MagicMock(spec=ExternalSource, id=2, db_name="db2", table_name="table2"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_sources
        mock_session.execute.return_value = mock_result

        results = await repo.list_sources()

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_upsert_columns(self, mock_session: AsyncMock) -> None:
        """Test upserting column metadata."""
        from src.repositories.catalog.catalog_repository import CatalogRepository

        repo = CatalogRepository(mock_session)

        columns_data = [
            {
                "column_name": "status",
                "column_path": "status",
                "inferred_type": "string",
                "is_required": True,
                "is_nullable": False,
                "is_enumerable": True,
                "unique_values": ["A", "B"],
                "sample_values": ["A", "B"],
                "presence_ratio": 1.0,
            }
        ]

        # Mock delete and insert
        mock_result = MagicMock()
        mock_session.execute.return_value = mock_result

        await repo.upsert_columns(source_id=1, columns=columns_data)

        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_delete_source(self, mock_session: AsyncMock) -> None:
        """Test deleting a source (cascades to columns)."""
        from src.models.catalog import ExternalSource
        from src.repositories.catalog.catalog_repository import CatalogRepository

        repo = CatalogRepository(mock_session)

        # Mock existing source
        mock_source = MagicMock(spec=ExternalSource)
        mock_source.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_source
        mock_session.execute.return_value = mock_result
        mock_session.delete = AsyncMock()

        deleted = await repo.delete_source(1)

        assert deleted is True
        mock_session.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_source(self, mock_session: AsyncMock) -> None:
        """Test deleting a source that doesn't exist."""
        from src.repositories.catalog.catalog_repository import CatalogRepository

        repo = CatalogRepository(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        deleted = await repo.delete_source(999)

        assert deleted is False
