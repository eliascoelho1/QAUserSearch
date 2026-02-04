"""Contract tests for Catalog API endpoints.

These tests verify that the API endpoints conform to the OpenAPI contract
defined in specs/002-yaml-catalog/contracts/openapi.yaml.
"""

import tempfile
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml
from httpx import ASGITransport, AsyncClient

from src.config import get_settings
from src.main import app


def create_test_catalog(base_path: Path) -> None:
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
        "generated_at": "2026-02-03T10:00:00+00:00",
        "sources": [
            {
                "db_name": "credit",
                "table_name": "invoice",
                "last_extracted": "2026-02-03T10:00:00+00:00",
                "file_path": "sources/credit/invoice.yaml",
            },
            {
                "db_name": "payment",
                "table_name": "transaction",
                "last_extracted": "2026-02-03T09:00:00+00:00",
                "file_path": "sources/payment/transaction.yaml",
            },
        ],
    }
    with (base_path / "catalog.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(index_data, f, allow_unicode=True)

    # Create credit.invoice source file
    invoice_data: dict[str, Any] = {
        "db_name": "credit",
        "table_name": "invoice",
        "document_count": 1500,
        "extracted_at": "2026-02-03T10:00:00+00:00",
        "updated_at": "2026-02-03T10:00:00+00:00",
        "columns": [
            {
                "path": "_id",
                "name": "_id",
                "type": "objectid",
                "required": True,
                "nullable": False,
                "enumerable": False,
                "presence_ratio": 1.0,
                "sample_values": ["507f1f77bcf86cd799439011"],
            },
            {
                "path": "status",
                "name": "status",
                "type": "string",
                "required": True,
                "nullable": False,
                "enumerable": True,
                "presence_ratio": 1.0,
                "sample_values": ["OPEN", "PAID"],
                "unique_values": ["OPEN", "PAID", "OVERDUE", "CANCELLED"],
                "description": "Status atual da fatura",
                "enrichment_status": "enriched",
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
                "path": "optional_field",
                "name": "optional_field",
                "type": "string",
                "required": False,
                "nullable": True,
                "enumerable": False,
                "presence_ratio": 0.65,
                "sample_values": ["value1", "value2"],
            },
        ],
    }
    with (base_path / "sources" / "credit" / "invoice.yaml").open(
        "w", encoding="utf-8"
    ) as f:
        yaml.dump(invoice_data, f, allow_unicode=True)

    # Create payment.transaction source file
    transaction_data: dict[str, Any] = {
        "db_name": "payment",
        "table_name": "transaction",
        "document_count": 5000,
        "extracted_at": "2026-02-03T09:00:00+00:00",
        "updated_at": "2026-02-03T09:00:00+00:00",
        "columns": [
            {
                "path": "_id",
                "name": "_id",
                "type": "objectid",
                "required": True,
                "nullable": False,
                "enumerable": False,
                "presence_ratio": 1.0,
                "sample_values": ["507f1f77bcf86cd799439012"],
            },
            {
                "path": "type",
                "name": "type",
                "type": "string",
                "required": True,
                "nullable": False,
                "enumerable": True,
                "presence_ratio": 1.0,
                "sample_values": ["PIX", "TED"],
                "unique_values": ["PIX", "TED", "BOLETO"],
            },
        ],
    }
    with (base_path / "sources" / "payment" / "transaction.yaml").open(
        "w", encoding="utf-8"
    ) as f:
        yaml.dump(transaction_data, f, allow_unicode=True)


@pytest.fixture
def temp_catalog() -> Generator[Path, None, None]:
    """Create a temporary catalog directory with test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog_path = Path(temp_dir)
        create_test_catalog(catalog_path)
        yield catalog_path


@pytest.fixture
async def contract_client(
    temp_catalog: Path,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client with test catalog configured."""
    # Override settings to use temp catalog
    settings = get_settings()
    original_path = settings.catalog_path
    settings.catalog_path = str(temp_catalog)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Restore original settings
    settings.catalog_path = original_path


class TestListSourcesContract:
    """Contract tests for GET /api/v1/catalog/sources endpoint."""

    @pytest.mark.anyio
    async def test_list_sources_returns_valid_response_structure(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify response conforms to SourceListResponse schema."""
        response = await contract_client.get("/api/v1/catalog/sources")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields from OpenAPI schema
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data

        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["skip"], int)
        assert isinstance(data["limit"], int)

    @pytest.mark.anyio
    async def test_list_sources_items_conform_to_source_summary_schema(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify each item conforms to SourceSummary schema."""
        response = await contract_client.get("/api/v1/catalog/sources")

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            # Required fields from SourceSummary schema
            assert "id" in item
            assert "db_name" in item
            assert "table_name" in item
            assert "column_count" in item
            assert "enumerable_count" in item
            assert "cataloged_at" in item
            assert "updated_at" in item

            # Verify types
            assert isinstance(item["id"], str)
            assert isinstance(item["db_name"], str)
            assert isinstance(item["table_name"], str)
            assert isinstance(item["column_count"], int)
            assert isinstance(item["enumerable_count"], int)
            assert item["column_count"] >= 0
            assert item["enumerable_count"] >= 0

            # ID format should be db_name.table_name
            assert item["id"] == f"{item['db_name']}.{item['table_name']}"

            # Verify datetime format (ISO 8601)
            datetime.fromisoformat(item["cataloged_at"].replace("Z", "+00:00"))
            datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))

    @pytest.mark.anyio
    async def test_list_sources_pagination_defaults(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify default pagination values."""
        response = await contract_client.get("/api/v1/catalog/sources")

        assert response.status_code == 200
        data = response.json()

        # Default values from OpenAPI spec
        assert data["skip"] == 0
        assert data["limit"] == 100

    @pytest.mark.anyio
    async def test_list_sources_with_db_name_filter(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify db_name filter works correctly."""
        response = await contract_client.get(
            "/api/v1/catalog/sources", params={"db_name": "credit"}
        )

        assert response.status_code == 200
        data = response.json()

        # All items should have db_name == "credit"
        for item in data["items"]:
            assert item["db_name"] == "credit"

    @pytest.mark.anyio
    async def test_list_sources_with_pagination(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify pagination parameters work correctly."""
        response = await contract_client.get(
            "/api/v1/catalog/sources", params={"skip": 1, "limit": 1}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["skip"] == 1
        assert data["limit"] == 1
        assert len(data["items"]) <= 1

    @pytest.mark.anyio
    async def test_list_sources_total_reflects_filter(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify total count reflects applied filters."""
        # Get all sources
        all_response = await contract_client.get("/api/v1/catalog/sources")
        all_data = all_response.json()

        # Get filtered sources
        filtered_response = await contract_client.get(
            "/api/v1/catalog/sources", params={"db_name": "credit"}
        )
        filtered_data = filtered_response.json()

        # Total should be different (assuming multiple db_names in test data)
        assert filtered_data["total"] <= all_data["total"]


class TestGetSourceContract:
    """Contract tests for GET /api/v1/catalog/sources/{source_id} endpoint."""

    @pytest.mark.anyio
    async def test_get_source_returns_valid_response_structure(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify response conforms to SourceDetailResponse schema."""
        response = await contract_client.get("/api/v1/catalog/sources/credit.invoice")

        assert response.status_code == 200
        data = response.json()

        # Required fields from SourceDetailResponse schema
        assert "id" in data
        assert "db_name" in data
        assert "table_name" in data
        assert "document_count" in data
        assert "cataloged_at" in data
        assert "updated_at" in data
        assert "columns" in data
        assert "stats" in data

        # Verify types
        assert isinstance(data["id"], str)
        assert isinstance(data["db_name"], str)
        assert isinstance(data["table_name"], str)
        assert isinstance(data["document_count"], int)
        assert isinstance(data["columns"], list)
        assert isinstance(data["stats"], dict)

    @pytest.mark.anyio
    async def test_get_source_columns_conform_to_column_detail_schema(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify each column conforms to ColumnDetail schema."""
        response = await contract_client.get("/api/v1/catalog/sources/credit.invoice")

        assert response.status_code == 200
        data = response.json()

        for column in data["columns"]:
            # Required fields from ColumnDetail schema
            assert "id" in column
            assert "column_name" in column
            assert "column_path" in column
            assert "inferred_type" in column
            assert "is_required" in column
            assert "is_nullable" in column
            assert "is_enumerable" in column
            assert "presence_ratio" in column
            assert "enrichment_status" in column

            # Verify types
            assert isinstance(column["id"], str)
            assert isinstance(column["column_name"], str)
            assert isinstance(column["column_path"], str)
            assert isinstance(column["inferred_type"], str)
            assert isinstance(column["is_required"], bool)
            assert isinstance(column["is_nullable"], bool)
            assert isinstance(column["is_enumerable"], bool)
            assert isinstance(column["presence_ratio"], float)
            assert 0.0 <= column["presence_ratio"] <= 1.0

            # Verify inferred_type is valid enum value
            valid_types = [
                "string",
                "integer",
                "number",
                "boolean",
                "datetime",
                "objectid",
                "array",
                "object",
                "null",
                "unknown",
            ]
            assert column["inferred_type"] in valid_types

            # Verify enrichment_status is valid enum value
            valid_statuses = ["not_enriched", "pending_enrichment", "enriched"]
            assert column["enrichment_status"] in valid_statuses

    @pytest.mark.anyio
    async def test_get_source_stats_conform_to_schema(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify stats conform to SourceStats schema."""
        response = await contract_client.get("/api/v1/catalog/sources/credit.invoice")

        assert response.status_code == 200
        data = response.json()

        stats = data["stats"]

        # Required fields from SourceStats schema
        assert "total_columns" in stats
        assert "required_columns" in stats
        assert "enumerable_columns" in stats
        assert "types_distribution" in stats

        # Verify types
        assert isinstance(stats["total_columns"], int)
        assert isinstance(stats["required_columns"], int)
        assert isinstance(stats["enumerable_columns"], int)
        assert isinstance(stats["types_distribution"], dict)

        # Verify values are non-negative
        assert stats["total_columns"] >= 0
        assert stats["required_columns"] >= 0
        assert stats["enumerable_columns"] >= 0

        # Verify types_distribution values are integers
        for type_name, count in stats["types_distribution"].items():
            assert isinstance(type_name, str)
            assert isinstance(count, int)
            assert count >= 0

    @pytest.mark.anyio
    async def test_get_source_not_found_returns_404(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify 404 response for non-existent source."""
        response = await contract_client.get(
            "/api/v1/catalog/sources/nonexistent.source"
        )

        assert response.status_code == 404
        data = response.json()

        # Verify error response structure
        assert "detail" in data

    @pytest.mark.anyio
    async def test_get_source_with_manual_description(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify manual descriptions are returned correctly."""
        response = await contract_client.get("/api/v1/catalog/sources/credit.invoice")

        assert response.status_code == 200
        data = response.json()

        # Find the status column which has a description
        status_column = next(
            (c for c in data["columns"] if c["column_name"] == "status"), None
        )
        assert status_column is not None
        assert status_column["description"] == "Status atual da fatura"
        assert status_column["enrichment_status"] == "enriched"


class TestListColumnsContract:
    """Contract tests for GET /api/v1/catalog/sources/{source_id}/columns endpoint."""

    @pytest.mark.anyio
    async def test_list_columns_returns_valid_response_structure(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify response conforms to ColumnListResponse schema."""
        response = await contract_client.get(
            "/api/v1/catalog/sources/credit.invoice/columns"
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields from ColumnListResponse schema
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data

        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["skip"], int)
        assert isinstance(data["limit"], int)

    @pytest.mark.anyio
    async def test_list_columns_items_conform_to_column_detail_schema(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify each item conforms to ColumnDetail schema."""
        response = await contract_client.get(
            "/api/v1/catalog/sources/credit.invoice/columns"
        )

        assert response.status_code == 200
        data = response.json()

        for column in data["items"]:
            # Required fields from ColumnDetail schema
            assert "id" in column
            assert "column_name" in column
            assert "column_path" in column
            assert "inferred_type" in column
            assert "is_required" in column
            assert "is_nullable" in column
            assert "is_enumerable" in column
            assert "presence_ratio" in column
            assert "enrichment_status" in column

    @pytest.mark.anyio
    async def test_list_columns_filter_by_type(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify type filter works correctly."""
        response = await contract_client.get(
            "/api/v1/catalog/sources/credit.invoice/columns", params={"type": "string"}
        )

        assert response.status_code == 200
        data = response.json()

        # All items should have inferred_type == "string"
        for column in data["items"]:
            assert column["inferred_type"] == "string"

    @pytest.mark.anyio
    async def test_list_columns_filter_by_is_required(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify is_required filter works correctly."""
        response = await contract_client.get(
            "/api/v1/catalog/sources/credit.invoice/columns",
            params={"is_required": True},
        )

        assert response.status_code == 200
        data = response.json()

        # All items should have is_required == True
        for column in data["items"]:
            assert column["is_required"] is True

    @pytest.mark.anyio
    async def test_list_columns_filter_by_is_enumerable(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify is_enumerable filter works correctly."""
        response = await contract_client.get(
            "/api/v1/catalog/sources/credit.invoice/columns",
            params={"is_enumerable": True},
        )

        assert response.status_code == 200
        data = response.json()

        # All items should have is_enumerable == True
        for column in data["items"]:
            assert column["is_enumerable"] is True

        # Verify enumerable columns have unique_values
        for column in data["items"]:
            if column["is_enumerable"]:
                assert "unique_values" in column

    @pytest.mark.anyio
    async def test_list_columns_pagination(self, contract_client: AsyncClient) -> None:
        """Verify pagination works correctly."""
        response = await contract_client.get(
            "/api/v1/catalog/sources/credit.invoice/columns",
            params={"skip": 1, "limit": 2},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["skip"] == 1
        assert data["limit"] == 2
        assert len(data["items"]) <= 2

    @pytest.mark.anyio
    async def test_list_columns_source_not_found_returns_404(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify 404 response for non-existent source."""
        response = await contract_client.get(
            "/api/v1/catalog/sources/nonexistent.source/columns"
        )

        assert response.status_code == 404
        data = response.json()

        # Verify error response structure
        assert "detail" in data

    @pytest.mark.anyio
    async def test_list_columns_total_reflects_filter(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify total count reflects applied filters."""
        # Get all columns
        all_response = await contract_client.get(
            "/api/v1/catalog/sources/credit.invoice/columns"
        )
        all_data = all_response.json()

        # Get enumerable columns only
        filtered_response = await contract_client.get(
            "/api/v1/catalog/sources/credit.invoice/columns",
            params={"is_enumerable": True},
        )
        filtered_data = filtered_response.json()

        # Total should be less or equal
        assert filtered_data["total"] <= all_data["total"]

    @pytest.mark.anyio
    async def test_list_columns_with_combined_filters(
        self, contract_client: AsyncClient
    ) -> None:
        """Verify multiple filters can be combined."""
        response = await contract_client.get(
            "/api/v1/catalog/sources/credit.invoice/columns",
            params={"type": "string", "is_required": True, "is_enumerable": True},
        )

        assert response.status_code == 200
        data = response.json()

        # All items should match all filters
        for column in data["items"]:
            assert column["inferred_type"] == "string"
            assert column["is_required"] is True
            assert column["is_enumerable"] is True
