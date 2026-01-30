"""Contract tests for Catalog API endpoints."""

import pytest
from httpx import AsyncClient

from src.api.v1 import catalog


class TestCatalogExtractionTaskStore:
    """Contract tests for /catalog/extraction/{task_id} endpoint - no DB needed."""

    @pytest.mark.asyncio
    async def test_get_extraction_status(self, async_client: AsyncClient) -> None:
        """GET /catalog/extraction/{task_id} should return status."""
        task_id = "test-task-id-123"

        # Directly inject test data into the task store
        catalog.task_store[task_id] = {
            "task_id": task_id,
            "status": "completed",
            "result": {
                "source_id": 1,
                "columns_extracted": 10,
                "enumerable_columns": 5,
            },
            "started_at": "2026-01-30T00:00:00",
            "completed_at": "2026-01-30T00:01:00",
        }

        try:
            response = await async_client.get(f"/api/v1/catalog/extraction/{task_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == task_id
            assert data["status"] == "completed"
            assert data["result"]["source_id"] == 1
            assert data["result"]["columns_extracted"] == 10
        finally:
            # Clean up
            catalog.task_store.pop(task_id, None)

    @pytest.mark.asyncio
    async def test_get_extraction_status_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """GET /catalog/extraction/{task_id} should return 404 if not found."""
        response = await async_client.get("/api/v1/catalog/extraction/unknown-id")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_extraction_status_with_error(
        self, async_client: AsyncClient
    ) -> None:
        """GET /catalog/extraction/{task_id} should return error status."""
        task_id = "failed-task-id"

        catalog.task_store[task_id] = {
            "task_id": task_id,
            "status": "failed",
            "error": "Connection timeout",
            "started_at": "2026-01-30T00:00:00",
            "completed_at": "2026-01-30T00:01:00",
        }

        try:
            response = await async_client.get(f"/api/v1/catalog/extraction/{task_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "failed"
            assert data["error"] == "Connection timeout"
        finally:
            catalog.task_store.pop(task_id, None)

    @pytest.mark.asyncio
    async def test_get_extraction_status_pending(
        self, async_client: AsyncClient
    ) -> None:
        """GET /catalog/extraction/{task_id} should return pending status."""
        task_id = "pending-task-id"

        catalog.task_store[task_id] = {
            "task_id": task_id,
            "status": "pending",
        }

        try:
            response = await async_client.get(f"/api/v1/catalog/extraction/{task_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert data["result"] is None
        finally:
            catalog.task_store.pop(task_id, None)


class TestExtractionRequestSchema:
    """Test the ExtractionRequest Pydantic schema validation."""

    def test_extraction_request_valid(self) -> None:
        """Valid extraction request should pass validation."""
        from src.schemas.catalog import ExtractionRequest

        request = ExtractionRequest(
            db_name="test_db",
            table_name="test_table",
            sample_size=500
        )

        assert request.db_name == "test_db"
        assert request.table_name == "test_table"
        assert request.sample_size == 500

    def test_extraction_request_defaults(self) -> None:
        """Extraction request should have default sample_size."""
        from src.schemas.catalog import ExtractionRequest

        request = ExtractionRequest(
            db_name="test_db",
            table_name="test_table"
        )

        assert request.sample_size == 500

    def test_extraction_request_missing_db_name(self) -> None:
        """Missing db_name should raise validation error."""
        from pydantic import ValidationError

        from src.schemas.catalog import ExtractionRequest

        with pytest.raises(ValidationError):
            ExtractionRequest(table_name="test_table")

    def test_extraction_request_missing_table_name(self) -> None:
        """Missing table_name should raise validation error."""
        from pydantic import ValidationError

        from src.schemas.catalog import ExtractionRequest

        with pytest.raises(ValidationError):
            ExtractionRequest(db_name="test_db")

    def test_extraction_request_sample_size_too_large(self) -> None:
        """Sample size > 10000 should raise validation error."""
        from pydantic import ValidationError

        from src.schemas.catalog import ExtractionRequest

        with pytest.raises(ValidationError):
            ExtractionRequest(
                db_name="test_db",
                table_name="test_table",
                sample_size=100000
            )

    def test_extraction_request_sample_size_too_small(self) -> None:
        """Sample size < 1 should raise validation error."""
        from pydantic import ValidationError

        from src.schemas.catalog import ExtractionRequest

        with pytest.raises(ValidationError):
            ExtractionRequest(
                db_name="test_db",
                table_name="test_table",
                sample_size=0
            )

    def test_extraction_request_db_name_too_long(self) -> None:
        """db_name > 100 chars should raise validation error."""
        from pydantic import ValidationError

        from src.schemas.catalog import ExtractionRequest

        with pytest.raises(ValidationError):
            ExtractionRequest(
                db_name="a" * 200,
                table_name="test_table"
            )

    def test_extraction_request_empty_db_name(self) -> None:
        """Empty db_name should raise validation error."""
        from pydantic import ValidationError

        from src.schemas.catalog import ExtractionRequest

        with pytest.raises(ValidationError):
            ExtractionRequest(
                db_name="",
                table_name="test_table"
            )
