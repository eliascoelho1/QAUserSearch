"""Unit tests for YAML catalog schemas."""

from datetime import UTC, datetime

from src.schemas.catalog_yaml import (
    CatalogIndex,
    ColumnMetadataYaml,
    IndexEntry,
    SourceMetadataYaml,
)
from src.schemas.enums import EnrichmentStatus, InferredType


class TestColumnMetadataYaml:
    """Tests for ColumnMetadataYaml to_yaml_dict and from_yaml_dict."""

    def test_to_yaml_dict_minimal(self) -> None:
        """Test minimal column conversion to YAML dict."""
        column = ColumnMetadataYaml(
            path="_id",
            name="_id",
            type=InferredType.OBJECTID,
            required=True,
            nullable=False,
            enumerable=False,
            presence_ratio=1.0,
            sample_values=["507f1f77bcf86cd799439011"],
        )

        result = column.to_yaml_dict()

        assert result["path"] == "_id"
        assert result["name"] == "_id"
        assert result["type"] == "objectid"
        assert result["required"] is True
        assert result["nullable"] is False
        assert result["enumerable"] is False
        assert result["presence_ratio"] == 1.0
        assert result["sample_values"] == ["507f1f77bcf86cd799439011"]
        # Optional fields should not be present
        assert "unique_values" not in result
        assert "description" not in result
        assert "enrichment_status" not in result  # Not present when default

    def test_to_yaml_dict_full(self) -> None:
        """Test full column conversion with all optional fields."""
        column = ColumnMetadataYaml(
            path="status",
            name="status",
            type=InferredType.STRING,
            required=True,
            nullable=False,
            enumerable=True,
            presence_ratio=1.0,
            sample_values=["OPEN", "PAID"],
            unique_values=["OPEN", "PAID", "OVERDUE"],
            description="Status da fatura",
            enrichment_status=EnrichmentStatus.ENRICHED,
        )

        result = column.to_yaml_dict()

        assert result["unique_values"] == ["OPEN", "PAID", "OVERDUE"]
        assert result["description"] == "Status da fatura"
        assert result["enrichment_status"] == "enriched"

    def test_from_yaml_dict_minimal(self) -> None:
        """Test creating column from minimal YAML dict."""
        data = {
            "path": "customer.name",
            "name": "name",
            "type": "string",
            "required": False,
            "nullable": True,
            "enumerable": False,
            "presence_ratio": 0.87,
            "sample_values": ["John", "Jane"],
        }

        column = ColumnMetadataYaml.from_yaml_dict(data)

        assert column.path == "customer.name"
        assert column.name == "name"
        assert column.type == InferredType.STRING
        assert column.required is False
        assert column.nullable is True
        assert column.enumerable is False
        assert column.presence_ratio == 0.87
        assert column.sample_values == ["John", "Jane"]
        assert column.unique_values is None
        assert column.description is None
        assert column.enrichment_status == EnrichmentStatus.NOT_ENRICHED

    def test_from_yaml_dict_full(self) -> None:
        """Test creating column from full YAML dict with optional fields."""
        data = {
            "path": "status",
            "name": "status",
            "type": "string",
            "required": True,
            "nullable": False,
            "enumerable": True,
            "presence_ratio": 1.0,
            "sample_values": ["OPEN", "PAID"],
            "unique_values": ["OPEN", "PAID", "OVERDUE"],
            "description": "Status da fatura",
            "enrichment_status": "enriched",
        }

        column = ColumnMetadataYaml.from_yaml_dict(data)

        assert column.unique_values == ["OPEN", "PAID", "OVERDUE"]
        assert column.description == "Status da fatura"
        assert column.enrichment_status == EnrichmentStatus.ENRICHED

    def test_roundtrip(self) -> None:
        """Test that to_yaml_dict -> from_yaml_dict preserves data."""
        original = ColumnMetadataYaml(
            path="order.items.price",
            name="price",
            type=InferredType.NUMBER,
            required=True,
            nullable=False,
            enumerable=False,
            presence_ratio=0.95,
            sample_values=[99.99, 149.50],
            unique_values=None,
            description="Preço do item",
            enrichment_status=EnrichmentStatus.ENRICHED,
        )

        yaml_dict = original.to_yaml_dict()
        restored = ColumnMetadataYaml.from_yaml_dict(yaml_dict)

        assert restored.path == original.path
        assert restored.name == original.name
        assert restored.type == original.type
        assert restored.required == original.required
        assert restored.nullable == original.nullable
        assert restored.enumerable == original.enumerable
        assert restored.presence_ratio == original.presence_ratio
        assert restored.sample_values == original.sample_values
        assert restored.description == original.description
        assert restored.enrichment_status == original.enrichment_status


class TestSourceMetadataYaml:
    """Tests for SourceMetadataYaml to_yaml_dict and from_yaml_dict."""

    def test_to_yaml_dict(self) -> None:
        """Test source conversion to YAML dict."""
        column = ColumnMetadataYaml(
            path="_id",
            name="_id",
            type=InferredType.OBJECTID,
            required=True,
            nullable=False,
            enumerable=False,
            presence_ratio=1.0,
            sample_values=["507f1f77bcf86cd799439011"],
        )
        extracted_at = datetime(2026, 2, 3, 10, 30, 0, tzinfo=UTC)
        source = SourceMetadataYaml(
            db_name="credit",
            table_name="invoice",
            document_count=15234,
            extracted_at=extracted_at,
            columns=[column],
        )

        result = source.to_yaml_dict()

        assert result["db_name"] == "credit"
        assert result["table_name"] == "invoice"
        assert result["document_count"] == 15234
        assert result["extracted_at"] == "2026-02-03T10:30:00+00:00"
        # updated_at should default to extracted_at
        assert result["updated_at"] == "2026-02-03T10:30:00+00:00"
        assert len(result["columns"]) == 1
        assert result["columns"][0]["path"] == "_id"

    def test_from_yaml_dict(self) -> None:
        """Test creating source from YAML dict."""
        data = {
            "db_name": "credit",
            "table_name": "invoice",
            "document_count": 15234,
            "extracted_at": "2026-02-03T10:30:00+00:00",
            "updated_at": "2026-02-03T11:00:00+00:00",
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
                }
            ],
        }

        source = SourceMetadataYaml.from_yaml_dict(data)

        assert source.db_name == "credit"
        assert source.table_name == "invoice"
        assert source.document_count == 15234
        assert source.extracted_at == datetime(
            2026, 2, 3, 10, 30, 0, tzinfo=UTC
        )
        assert source.updated_at == datetime(2026, 2, 3, 11, 0, 0, tzinfo=UTC)
        assert len(source.columns) == 1
        assert source.columns[0].path == "_id"

    def test_source_id_property(self) -> None:
        """Test source_id property generates correct composite ID."""
        source = SourceMetadataYaml(
            db_name="credit",
            table_name="invoice",
            document_count=100,
            extracted_at=datetime.now(UTC),
            columns=[],
        )

        assert source.source_id == "credit.invoice"

    def test_roundtrip(self) -> None:
        """Test that to_yaml_dict -> from_yaml_dict preserves data."""
        column = ColumnMetadataYaml(
            path="status",
            name="status",
            type=InferredType.STRING,
            required=True,
            nullable=False,
            enumerable=True,
            presence_ratio=1.0,
            sample_values=["OPEN"],
            unique_values=["OPEN", "PAID"],
            description="Status",
            enrichment_status=EnrichmentStatus.ENRICHED,
        )
        extracted_at = datetime(2026, 2, 3, 10, 30, 0, tzinfo=UTC)
        updated_at = datetime(2026, 2, 3, 11, 0, 0, tzinfo=UTC)
        original = SourceMetadataYaml(
            db_name="credit",
            table_name="invoice",
            document_count=15234,
            extracted_at=extracted_at,
            updated_at=updated_at,
            columns=[column],
        )

        yaml_dict = original.to_yaml_dict()
        restored = SourceMetadataYaml.from_yaml_dict(yaml_dict)

        assert restored.db_name == original.db_name
        assert restored.table_name == original.table_name
        assert restored.document_count == original.document_count
        assert restored.extracted_at == original.extracted_at
        assert restored.updated_at == original.updated_at
        assert len(restored.columns) == len(original.columns)
        assert restored.columns[0].description == original.columns[0].description


class TestCatalogIndex:
    """Tests for CatalogIndex and IndexEntry to_yaml_dict and from_yaml_dict."""

    def test_index_entry_to_yaml_dict(self) -> None:
        """Test index entry conversion to YAML dict."""
        entry = IndexEntry(
            db_name="credit",
            table_name="invoice",
            last_extracted=datetime(2026, 2, 3, 10, 30, 0, tzinfo=UTC),
            file_path="sources/credit/invoice.yaml",
        )

        result = entry.to_yaml_dict()

        assert result["db_name"] == "credit"
        assert result["table_name"] == "invoice"
        assert result["last_extracted"] == "2026-02-03T10:30:00+00:00"
        assert result["file_path"] == "sources/credit/invoice.yaml"

    def test_index_entry_from_yaml_dict(self) -> None:
        """Test creating index entry from YAML dict."""
        data = {
            "db_name": "credit",
            "table_name": "invoice",
            "last_extracted": "2026-02-03T10:30:00+00:00",
            "file_path": "sources/credit/invoice.yaml",
        }

        entry = IndexEntry.from_yaml_dict(data)

        assert entry.db_name == "credit"
        assert entry.table_name == "invoice"
        assert entry.last_extracted == datetime(
            2026, 2, 3, 10, 30, 0, tzinfo=UTC
        )
        assert entry.file_path == "sources/credit/invoice.yaml"

    def test_index_entry_source_id_property(self) -> None:
        """Test source_id property on IndexEntry."""
        entry = IndexEntry(
            db_name="credit",
            table_name="invoice",
            last_extracted=datetime.now(UTC),
            file_path="sources/credit/invoice.yaml",
        )

        assert entry.source_id == "credit.invoice"

    def test_catalog_index_to_yaml_dict(self) -> None:
        """Test catalog index conversion to YAML dict."""
        entry = IndexEntry(
            db_name="credit",
            table_name="invoice",
            last_extracted=datetime(2026, 2, 3, 10, 30, 0, tzinfo=UTC),
            file_path="sources/credit/invoice.yaml",
        )
        index = CatalogIndex(
            version="1.0",
            generated_at=datetime(2026, 2, 3, 10, 30, 0, tzinfo=UTC),
            sources=[entry],
        )

        result = index.to_yaml_dict()

        assert result["version"] == "1.0"
        assert result["generated_at"] == "2026-02-03T10:30:00+00:00"
        assert len(result["sources"]) == 1
        assert result["sources"][0]["db_name"] == "credit"

    def test_catalog_index_from_yaml_dict(self) -> None:
        """Test creating catalog index from YAML dict."""
        data = {
            "version": "1.0",
            "generated_at": "2026-02-03T10:30:00+00:00",
            "sources": [
                {
                    "db_name": "credit",
                    "table_name": "invoice",
                    "last_extracted": "2026-02-03T10:30:00+00:00",
                    "file_path": "sources/credit/invoice.yaml",
                }
            ],
        }

        index = CatalogIndex.from_yaml_dict(data)

        assert index.version == "1.0"
        assert index.generated_at == datetime(
            2026, 2, 3, 10, 30, 0, tzinfo=UTC
        )
        assert len(index.sources) == 1
        assert index.sources[0].db_name == "credit"

    def test_find_source(self) -> None:
        """Test finding source by db_name and table_name."""
        entry1 = IndexEntry(
            db_name="credit",
            table_name="invoice",
            last_extracted=datetime.now(UTC),
            file_path="sources/credit/invoice.yaml",
        )
        entry2 = IndexEntry(
            db_name="credit",
            table_name="closed_invoice",
            last_extracted=datetime.now(UTC),
            file_path="sources/credit/closed_invoice.yaml",
        )
        index = CatalogIndex(
            generated_at=datetime.now(UTC), sources=[entry1, entry2]
        )

        found = index.find_source("credit", "invoice")
        not_found = index.find_source("credit", "nonexistent")

        assert found is not None
        assert found.table_name == "invoice"
        assert not_found is None

    def test_find_source_by_id(self) -> None:
        """Test finding source by composite ID."""
        entry = IndexEntry(
            db_name="credit",
            table_name="invoice",
            last_extracted=datetime.now(UTC),
            file_path="sources/credit/invoice.yaml",
        )
        index = CatalogIndex(generated_at=datetime.now(UTC), sources=[entry])

        found = index.find_source_by_id("credit.invoice")
        not_found = index.find_source_by_id("credit.nonexistent")

        assert found is not None
        assert found.table_name == "invoice"
        assert not_found is None

    def test_roundtrip(self) -> None:
        """Test that to_yaml_dict -> from_yaml_dict preserves data."""
        entry = IndexEntry(
            db_name="credit",
            table_name="invoice",
            last_extracted=datetime(2026, 2, 3, 10, 30, 0, tzinfo=UTC),
            file_path="sources/credit/invoice.yaml",
        )
        original = CatalogIndex(
            version="1.0",
            generated_at=datetime(2026, 2, 3, 10, 30, 0, tzinfo=UTC),
            sources=[entry],
        )

        yaml_dict = original.to_yaml_dict()
        restored = CatalogIndex.from_yaml_dict(yaml_dict)

        assert restored.version == original.version
        assert restored.generated_at == original.generated_at
        assert len(restored.sources) == len(original.sources)
        assert restored.sources[0].source_id == original.sources[0].source_id
