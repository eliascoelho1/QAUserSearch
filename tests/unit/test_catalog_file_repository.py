"""Unit tests for CatalogFileRepository."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import yaml

from src.repositories.catalog.file_repository import CatalogFileRepository
from src.schemas.enums import InferredType


def create_test_catalog_structure(base_path: Path) -> None:
    """Create a test catalog structure with sample data.

    Args:
        base_path: Base path for the catalog.
    """
    # Create directories
    (base_path / "sources" / "credit").mkdir(parents=True, exist_ok=True)
    (base_path / "sources" / "payment").mkdir(parents=True, exist_ok=True)

    # Create index
    index_data: dict[str, Any] = {
        "version": "1.0",
        "generated_at": "2025-01-15T10:00:00+00:00",
        "sources": [
            {
                "db_name": "credit",
                "table_name": "invoice",
                "last_extracted": "2025-01-15T10:00:00+00:00",
                "file_path": "sources/credit/invoice.yaml",
            },
            {
                "db_name": "credit",
                "table_name": "user",
                "last_extracted": "2025-01-15T10:00:00+00:00",
                "file_path": "sources/credit/user.yaml",
            },
            {
                "db_name": "payment",
                "table_name": "transaction",
                "last_extracted": "2025-01-15T09:00:00+00:00",
                "file_path": "sources/payment/transaction.yaml",
            },
        ],
    }
    with (base_path / "catalog.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(index_data, f, allow_unicode=True)

    # Create source files
    invoice_data: dict[str, Any] = {
        "db_name": "credit",
        "table_name": "invoice",
        "document_count": 1000,
        "extracted_at": "2025-01-15T10:00:00+00:00",
        "updated_at": "2025-01-15T10:00:00+00:00",
        "columns": [
            {
                "path": "_id",
                "name": "_id",
                "type": "string",
                "required": True,
                "nullable": False,
                "enumerable": False,
                "presence_ratio": 1.0,
                "sample_values": ["abc123", "def456"],
            },
            {
                "path": "amount",
                "name": "amount",
                "type": "number",
                "required": True,
                "nullable": False,
                "enumerable": False,
                "presence_ratio": 1.0,
                "sample_values": [100.50, 250.00],
            },
            {
                "path": "status",
                "name": "status",
                "type": "string",
                "required": True,
                "nullable": False,
                "enumerable": True,
                "presence_ratio": 1.0,
                "sample_values": ["paid", "pending"],
                "unique_values": ["paid", "pending", "cancelled"],
            },
        ],
    }
    with (base_path / "sources" / "credit" / "invoice.yaml").open(
        "w", encoding="utf-8"
    ) as f:
        yaml.dump(invoice_data, f, allow_unicode=True)

    user_data: dict[str, Any] = {
        "db_name": "credit",
        "table_name": "user",
        "document_count": 500,
        "extracted_at": "2025-01-15T10:00:00+00:00",
        "updated_at": "2025-01-15T10:00:00+00:00",
        "columns": [
            {
                "path": "_id",
                "name": "_id",
                "type": "string",
                "required": True,
                "nullable": False,
                "enumerable": False,
                "presence_ratio": 1.0,
                "sample_values": ["user1", "user2"],
            },
            {
                "path": "email",
                "name": "email",
                "type": "string",
                "required": True,
                "nullable": False,
                "enumerable": False,
                "presence_ratio": 1.0,
                "sample_values": ["test@example.com"],
            },
        ],
    }
    with (base_path / "sources" / "credit" / "user.yaml").open(
        "w", encoding="utf-8"
    ) as f:
        yaml.dump(user_data, f, allow_unicode=True)

    transaction_data: dict[str, Any] = {
        "db_name": "payment",
        "table_name": "transaction",
        "document_count": 2000,
        "extracted_at": "2025-01-15T09:00:00+00:00",
        "updated_at": "2025-01-15T09:00:00+00:00",
        "columns": [
            {
                "path": "_id",
                "name": "_id",
                "type": "string",
                "required": True,
                "nullable": False,
                "enumerable": False,
                "presence_ratio": 1.0,
                "sample_values": ["tx1", "tx2"],
            },
        ],
    }
    with (base_path / "sources" / "payment" / "transaction.yaml").open(
        "w", encoding="utf-8"
    ) as f:
        yaml.dump(transaction_data, f, allow_unicode=True)


@pytest.fixture
def catalog_dir() -> Generator[Path, None, None]:
    """Create a temporary catalog directory with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        create_test_catalog_structure(base_path)
        yield base_path


@pytest.fixture
def empty_catalog_dir() -> Generator[Path, None, None]:
    """Create an empty temporary catalog directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def repository(catalog_dir: Path) -> CatalogFileRepository:
    """Create a repository with test data."""
    return CatalogFileRepository(catalog_path=catalog_dir, cache_ttl_seconds=60.0)


@pytest.fixture
def empty_repository(empty_catalog_dir: Path) -> CatalogFileRepository:
    """Create a repository with empty catalog."""
    return CatalogFileRepository(catalog_path=empty_catalog_dir, cache_ttl_seconds=60.0)


class TestCatalogFileRepositoryInit:
    """Tests for CatalogFileRepository initialization."""

    def test_init_with_string_path(self, catalog_dir: Path) -> None:
        """Test initialization with string path."""
        repo = CatalogFileRepository(
            catalog_path=str(catalog_dir), cache_ttl_seconds=30.0
        )
        assert repo.catalog_path == catalog_dir

    def test_init_with_path_object(self, catalog_dir: Path) -> None:
        """Test initialization with Path object."""
        repo = CatalogFileRepository(catalog_path=catalog_dir, cache_ttl_seconds=30.0)
        assert repo.catalog_path == catalog_dir


class TestGetSourceById:
    """Tests for CatalogFileRepository.get_source_by_id()."""

    @pytest.mark.asyncio
    async def test_get_source_by_id_found(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test getting a source by valid ID."""
        source = await repository.get_source_by_id("credit.invoice")

        assert source is not None
        assert source.db_name == "credit"
        assert source.table_name == "invoice"
        assert source.document_count == 1000
        assert len(source.columns) == 3

    @pytest.mark.asyncio
    async def test_get_source_by_id_not_found(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test getting a non-existent source returns None."""
        source = await repository.get_source_by_id("nonexistent.table")

        assert source is None

    @pytest.mark.asyncio
    async def test_get_source_by_id_invalid_format(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test getting source with invalid ID format returns None."""
        source = await repository.get_source_by_id("invalid_format")

        assert source is None

    @pytest.mark.asyncio
    async def test_get_source_by_id_empty_id(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test getting source with empty ID returns None."""
        source = await repository.get_source_by_id("")

        assert source is None

    @pytest.mark.asyncio
    async def test_get_source_by_id_caches_result(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test that subsequent calls use cache."""
        # First call
        source1 = await repository.get_source_by_id("credit.invoice")
        # Second call should use cache
        source2 = await repository.get_source_by_id("credit.invoice")

        assert source1 is not None
        assert source2 is not None
        assert source1.db_name == source2.db_name
        assert source1.table_name == source2.table_name


class TestGetSourceByIdentity:
    """Tests for CatalogFileRepository.get_source_by_identity()."""

    @pytest.mark.asyncio
    async def test_get_source_by_identity_found(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test getting a source by db_name and table_name."""
        source = await repository.get_source_by_identity("credit", "invoice")

        assert source is not None
        assert source.db_name == "credit"
        assert source.table_name == "invoice"

    @pytest.mark.asyncio
    async def test_get_source_by_identity_not_found(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test getting non-existent source by identity."""
        source = await repository.get_source_by_identity("nonexistent", "table")

        assert source is None

    @pytest.mark.asyncio
    async def test_get_source_by_identity_empty_catalog(
        self, empty_repository: CatalogFileRepository
    ) -> None:
        """Test getting source from empty catalog returns None."""
        source = await empty_repository.get_source_by_identity("credit", "invoice")

        assert source is None


class TestListSources:
    """Tests for CatalogFileRepository.list_sources()."""

    @pytest.mark.asyncio
    async def test_list_sources_all(self, repository: CatalogFileRepository) -> None:
        """Test listing all sources."""
        sources = await repository.list_sources()

        assert len(sources) == 3
        db_names = {s.db_name for s in sources}
        assert db_names == {"credit", "payment"}

    @pytest.mark.asyncio
    async def test_list_sources_filter_by_db_name(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test filtering sources by db_name."""
        sources = await repository.list_sources(db_name="credit")

        assert len(sources) == 2
        assert all(s.db_name == "credit" for s in sources)

    @pytest.mark.asyncio
    async def test_list_sources_filter_nonexistent_db(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test filtering by non-existent db_name returns empty."""
        sources = await repository.list_sources(db_name="nonexistent")

        assert len(sources) == 0

    @pytest.mark.asyncio
    async def test_list_sources_pagination_skip(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test pagination with skip."""
        sources = await repository.list_sources(skip=1)

        assert len(sources) == 2

    @pytest.mark.asyncio
    async def test_list_sources_pagination_limit(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test pagination with limit."""
        sources = await repository.list_sources(limit=2)

        assert len(sources) == 2

    @pytest.mark.asyncio
    async def test_list_sources_pagination_skip_and_limit(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test pagination with both skip and limit."""
        sources = await repository.list_sources(skip=1, limit=1)

        assert len(sources) == 1

    @pytest.mark.asyncio
    async def test_list_sources_empty_catalog(
        self, empty_repository: CatalogFileRepository
    ) -> None:
        """Test listing sources from empty catalog."""
        sources = await empty_repository.list_sources()

        assert len(sources) == 0


class TestCountSources:
    """Tests for CatalogFileRepository.count_sources()."""

    @pytest.mark.asyncio
    async def test_count_sources_all(self, repository: CatalogFileRepository) -> None:
        """Test counting all sources."""
        count = await repository.count_sources()

        assert count == 3

    @pytest.mark.asyncio
    async def test_count_sources_filter_by_db_name(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test counting sources filtered by db_name."""
        count = await repository.count_sources(db_name="credit")

        assert count == 2

    @pytest.mark.asyncio
    async def test_count_sources_filter_nonexistent_db(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test counting with non-existent db_name."""
        count = await repository.count_sources(db_name="nonexistent")

        assert count == 0

    @pytest.mark.asyncio
    async def test_count_sources_empty_catalog(
        self, empty_repository: CatalogFileRepository
    ) -> None:
        """Test counting sources in empty catalog."""
        count = await empty_repository.count_sources()

        assert count == 0


class TestGetSourceDetail:
    """Tests for CatalogFileRepository.get_source_detail()."""

    @pytest.mark.asyncio
    async def test_get_source_detail_found(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test getting source detail."""
        detail = await repository.get_source_detail("credit.invoice")

        assert detail is not None
        assert detail["id"] == "credit.invoice"
        assert detail["db_name"] == "credit"
        assert detail["table_name"] == "invoice"
        assert detail["document_count"] == 1000
        assert len(detail["columns"]) == 3

    @pytest.mark.asyncio
    async def test_get_source_detail_stats(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test source detail includes computed stats."""
        detail = await repository.get_source_detail("credit.invoice")

        assert detail is not None
        stats = detail["stats"]
        assert stats["total_columns"] == 3
        assert stats["required_columns"] == 3
        assert stats["enumerable_columns"] == 1
        assert "string" in stats["types_distribution"]
        assert "number" in stats["types_distribution"]

    @pytest.mark.asyncio
    async def test_get_source_detail_not_found(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test getting detail for non-existent source."""
        detail = await repository.get_source_detail("nonexistent.table")

        assert detail is None


class TestGetColumns:
    """Tests for CatalogFileRepository.get_columns()."""

    @pytest.mark.asyncio
    async def test_get_columns_all(self, repository: CatalogFileRepository) -> None:
        """Test getting all columns for a source."""
        columns = await repository.get_columns("credit.invoice")

        assert len(columns) == 3

    @pytest.mark.asyncio
    async def test_get_columns_filter_by_type(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test filtering columns by inferred_type."""
        columns = await repository.get_columns("credit.invoice", inferred_type="string")

        assert len(columns) == 2
        assert all(c.type == InferredType.STRING for c in columns)

    @pytest.mark.asyncio
    async def test_get_columns_filter_by_required(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test filtering columns by is_required."""
        columns = await repository.get_columns("credit.invoice", is_required=True)

        assert len(columns) == 3
        assert all(c.required for c in columns)

    @pytest.mark.asyncio
    async def test_get_columns_filter_by_enumerable(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test filtering columns by is_enumerable."""
        columns = await repository.get_columns("credit.invoice", is_enumerable=True)

        assert len(columns) == 1
        assert columns[0].name == "status"
        assert columns[0].enumerable is True

    @pytest.mark.asyncio
    async def test_get_columns_pagination(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test column pagination."""
        columns = await repository.get_columns("credit.invoice", skip=1, limit=1)

        assert len(columns) == 1

    @pytest.mark.asyncio
    async def test_get_columns_nonexistent_source(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test getting columns for non-existent source."""
        columns = await repository.get_columns("nonexistent.table")

        assert len(columns) == 0


class TestCountColumns:
    """Tests for CatalogFileRepository.count_columns()."""

    @pytest.mark.asyncio
    async def test_count_columns_all(self, repository: CatalogFileRepository) -> None:
        """Test counting all columns for a source."""
        count = await repository.count_columns("credit.invoice")

        assert count == 3

    @pytest.mark.asyncio
    async def test_count_columns_filter_by_type(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test counting columns filtered by type."""
        count = await repository.count_columns("credit.invoice", inferred_type="string")

        assert count == 2

    @pytest.mark.asyncio
    async def test_count_columns_filter_by_enumerable(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test counting enumerable columns."""
        count = await repository.count_columns("credit.invoice", is_enumerable=True)

        assert count == 1

    @pytest.mark.asyncio
    async def test_count_columns_nonexistent_source(
        self, repository: CatalogFileRepository
    ) -> None:
        """Test counting columns for non-existent source."""
        count = await repository.count_columns("nonexistent.table")

        assert count == 0


class TestInvalidateCache:
    """Tests for CatalogFileRepository.invalidate_cache()."""

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, repository: CatalogFileRepository) -> None:
        """Test cache invalidation."""
        # Load data into cache
        await repository.get_source_by_id("credit.invoice")

        # Invalidate
        repository.invalidate_cache()

        # Verify cache is empty by checking internal cache size
        assert repository._index_cache.size() == 0
        assert repository._source_cache.size() == 0


class TestCorruptedYaml:
    """Tests for handling corrupted YAML files."""

    @pytest.mark.asyncio
    async def test_corrupted_source_file_raises(self) -> None:
        """Test that corrupted YAML raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            (base_path / "sources" / "db").mkdir(parents=True, exist_ok=True)

            # Create index pointing to corrupted file
            index_data: dict[str, Any] = {
                "version": "1.0",
                "generated_at": "2025-01-15T10:00:00+00:00",
                "sources": [
                    {
                        "db_name": "db",
                        "table_name": "table",
                        "last_extracted": "2025-01-15T10:00:00+00:00",
                        "file_path": "sources/db/table.yaml",
                    },
                ],
            }
            with (base_path / "catalog.yaml").open("w", encoding="utf-8") as f:
                yaml.dump(index_data, f)

            # Create corrupted YAML file
            with (base_path / "sources" / "db" / "table.yaml").open("w") as f:
                f.write("invalid: yaml: content: [")

            repo = CatalogFileRepository(catalog_path=base_path, cache_ttl_seconds=60.0)

            with pytest.raises(yaml.YAMLError):
                await repo.get_source_by_id("db.table")

    @pytest.mark.asyncio
    async def test_missing_source_file_returns_none(self) -> None:
        """Test that missing source file returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # Create index pointing to non-existent file
            index_data: dict[str, Any] = {
                "version": "1.0",
                "generated_at": "2025-01-15T10:00:00+00:00",
                "sources": [
                    {
                        "db_name": "db",
                        "table_name": "table",
                        "last_extracted": "2025-01-15T10:00:00+00:00",
                        "file_path": "sources/db/table.yaml",
                    },
                ],
            }
            with (base_path / "catalog.yaml").open("w", encoding="utf-8") as f:
                yaml.dump(index_data, f)

            repo = CatalogFileRepository(catalog_path=base_path, cache_ttl_seconds=60.0)
            source = await repo.get_source_by_id("db.table")

            assert source is None
