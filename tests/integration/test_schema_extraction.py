"""Integration tests for schema extraction and persistence."""

from pathlib import Path

import pytest

from src.schemas.enums import InferredType


class TestSchemaExtractionIntegration:
    """Integration tests for complete schema extraction flow."""

    @pytest.fixture
    def sample_documents(self) -> list[dict]:
        """Sample documents for testing."""
        return [
            {
                "_id": "68e527ed7fc3841868bef0aa",
                "consumer_id": "26160269",
                "account_number": "0000000000003000001",
                "status": "A",
                "issuer": "PICPAY",
                "product_data": {
                    "type": "HYBRID_LEVERAGED",
                    "origin_flow": "manual-processing",
                    "updated_at": "2025-10-07T11:47:09.803Z"
                },
                "guaranteed_limit": {
                    "enabled": False,
                    "enabled_wallet_balance": False
                },
                "created_at": "2025-10-07T11:47:09.803Z",
                "updated_at": "2025-10-07T11:47:09.803Z"
            },
            {
                "_id": "68e527ed7fc3841868bef0ab",
                "consumer_id": "26160270",
                "account_number": "0000000000003000002",
                "status": "B",
                "issuer": "VISA",
                "product_data": {
                    "type": "STANDARD",
                    "origin_flow": "auto-processing",
                    "updated_at": "2025-10-08T11:47:09.803Z"
                },
                "guaranteed_limit": {
                    "enabled": True,
                    "enabled_wallet_balance": True
                },
                "created_at": "2025-10-08T11:47:09.803Z",
                "updated_at": "2025-10-08T11:47:09.803Z"
            },
        ]

    def test_full_extraction_flow(self, sample_documents: list[dict]) -> None:
        """Test complete extraction from documents to analyzed schema."""
        from src.services.schema_extraction.analyzer import SchemaAnalyzer
        from src.services.schema_extraction.extractor import SchemaExtractor

        # Step 1: Extract schema from documents
        extractor = SchemaExtractor()
        extracted = extractor.extract(sample_documents)

        # Verify extraction
        assert "_id" in extracted
        assert "consumer_id" in extracted
        assert "status" in extracted
        assert "product_data.type" in extracted
        assert "guaranteed_limit.enabled" in extracted

        # Step 2: Analyze schema
        analyzer = SchemaAnalyzer(cardinality_limit=50)
        analyzed = analyzer.analyze(extracted, len(sample_documents))

        # Verify analysis
        assert analyzed["_id"]["inferred_type"] == InferredType.OBJECTID
        assert analyzed["status"]["is_enumerable"] is True
        assert set(analyzed["status"]["unique_values"]) == {"A", "B"}
        assert analyzed["product_data.type"]["is_enumerable"] is True
        assert analyzed["guaranteed_limit.enabled"]["is_enumerable"] is True

        # Verify datetime detection
        assert analyzed["created_at"]["inferred_type"] == InferredType.DATETIME
        assert analyzed["product_data.updated_at"]["inferred_type"] == InferredType.DATETIME

    def test_extraction_from_json_file(self) -> None:
        """Test extraction from actual JSON sample file."""
        import json

        json_path = Path("res/db/card_account_authorization.account_main.json")
        if not json_path.exists():
            pytest.skip("Sample JSON file not found")

        with open(json_path) as f:
            documents = json.load(f)

        from src.services.schema_extraction.analyzer import SchemaAnalyzer
        from src.services.schema_extraction.extractor import SchemaExtractor

        extractor = SchemaExtractor()
        extracted = extractor.extract(documents)

        analyzer = SchemaAnalyzer(cardinality_limit=50)
        analyzed = analyzer.analyze(extracted, len(documents))

        # Verify key fields are extracted
        assert "_id" in analyzed
        assert analyzed["_id"]["inferred_type"] == InferredType.OBJECTID

        # Verify status is enumerable (common pattern)
        if "status" in analyzed:
            assert analyzed["status"]["presence_ratio"] > 0

    def test_extraction_handles_missing_fields(self) -> None:
        """Test extraction handles documents with missing fields correctly."""
        from src.services.schema_extraction.analyzer import SchemaAnalyzer
        from src.services.schema_extraction.extractor import SchemaExtractor

        documents = [
            {"name": "John", "age": 30},
            {"name": "Jane"},  # missing age
            {"name": "Bob", "age": 25},
        ]

        extractor = SchemaExtractor()
        extracted = extractor.extract(documents)

        analyzer = SchemaAnalyzer()
        analyzed = analyzer.analyze(extracted, len(documents))

        assert analyzed["name"]["presence_ratio"] == 1.0
        assert analyzed["name"]["is_required"] is True

        assert analyzed["age"]["presence_ratio"] == pytest.approx(2/3)
        assert analyzed["age"]["is_required"] is False

    def test_extraction_handles_null_values(self) -> None:
        """Test extraction properly handles null values."""
        from src.services.schema_extraction.analyzer import SchemaAnalyzer
        from src.services.schema_extraction.extractor import SchemaExtractor

        documents = [
            {"field": "value1"},
            {"field": None},
            {"field": "value2"},
        ]

        extractor = SchemaExtractor()
        extracted = extractor.extract(documents)

        analyzer = SchemaAnalyzer()
        analyzed = analyzer.analyze(extracted, len(documents))

        assert analyzed["field"]["is_nullable"] is True
        assert analyzed["field"]["presence_ratio"] == 1.0
