"""Unit tests for CatalogFileWriter."""

import tempfile
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

from src.schemas.catalog_yaml import (
    ColumnMetadataYaml,
    SourceMetadataYaml,
)
from src.schemas.enums import InferredType


def create_sample_source(
    db_name: str = "credit", table_name: str = "invoice"
) -> SourceMetadataYaml:
    """Create a sample source metadata for testing.

    Args:
        db_name: Database name.
        table_name: Table name.

    Returns:
        A SourceMetadataYaml instance.
    """
    return SourceMetadataYaml(
        db_name=db_name,
        table_name=table_name,
        document_count=1000,
        extracted_at=datetime(2026, 2, 3, 10, 0, 0, tzinfo=UTC),
        columns=[
            ColumnMetadataYaml(
                path="_id",
                name="_id",
                type=InferredType.OBJECTID,
                required=True,
                nullable=False,
                enumerable=False,
                presence_ratio=1.0,
                sample_values=["507f1f77bcf86cd799439011"],
            ),
            ColumnMetadataYaml(
                path="status",
                name="status",
                type=InferredType.STRING,
                required=True,
                nullable=False,
                enumerable=True,
                presence_ratio=1.0,
                sample_values=["OPEN", "PAID"],
                unique_values=["OPEN", "PAID", "OVERDUE"],
            ),
            ColumnMetadataYaml(
                path="amount",
                name="amount",
                type=InferredType.NUMBER,
                required=True,
                nullable=False,
                enumerable=False,
                presence_ratio=1.0,
                sample_values=[100.50, 250.00],
            ),
        ],
    )


def create_existing_source_yaml(base_path: Path, db_name: str, table_name: str) -> None:
    """Create an existing source YAML file with manual enrichments.

    Args:
        base_path: Base path for the catalog.
        db_name: Database name.
        table_name: Table name.
    """
    source_dir = base_path / "sources" / db_name
    source_dir.mkdir(parents=True, exist_ok=True)

    # Create a source with manually edited fields
    existing_data: dict[str, Any] = {
        "db_name": db_name,
        "table_name": table_name,
        "document_count": 500,  # Old document count
        "extracted_at": "2026-01-15T10:00:00+00:00",
        "updated_at": "2026-01-20T10:00:00+00:00",
        "columns": [
            {
                "path": "_id",
                "name": "_id",
                "type": "objectid",
                "required": True,
                "nullable": False,
                "enumerable": False,
                "presence_ratio": 1.0,
                "sample_values": ["old_id_1"],
            },
            {
                "path": "status",
                "name": "status",
                "type": "string",
                "required": True,
                "nullable": False,
                "enumerable": True,
                "presence_ratio": 1.0,
                "sample_values": ["OLD_STATUS"],
                "unique_values": ["OLD_STATUS"],
                # MANUALLY EDITED FIELDS - should be preserved
                "description": "Status atual da fatura - descrição manual",
                "enrichment_status": "enriched",
            },
            {
                "path": "old_field",  # This field no longer exists
                "name": "old_field",
                "type": "string",
                "required": False,
                "nullable": True,
                "enumerable": False,
                "presence_ratio": 0.5,
                "sample_values": ["old_value"],
                "description": "Campo antigo que foi removido",
            },
        ],
    }

    with (source_dir / f"{table_name}.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(existing_data, f, allow_unicode=True)


def create_existing_index(base_path: Path) -> None:
    """Create an existing catalog index.

    Args:
        base_path: Base path for the catalog.
    """
    index_data: dict[str, Any] = {
        "version": "1.0",
        "generated_at": "2026-01-15T10:00:00+00:00",
        "sources": [
            {
                "db_name": "credit",
                "table_name": "invoice",
                "last_extracted": "2026-01-15T10:00:00+00:00",
                "file_path": "sources/credit/invoice.yaml",
            },
            {
                "db_name": "payment",
                "table_name": "transaction",
                "last_extracted": "2026-01-10T10:00:00+00:00",
                "file_path": "sources/payment/transaction.yaml",
            },
        ],
    }

    with (base_path / "catalog.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(index_data, f, allow_unicode=True)


@pytest.fixture
def temp_catalog_dir() -> Generator[Path, None, None]:
    """Create a temporary catalog directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        catalog_path = Path(temp_dir)
        yield catalog_path


class TestCatalogFileWriterWriteSource:
    """Tests for CatalogFileWriter.write_source() method."""

    def test_write_source_creates_yaml_file(self, temp_catalog_dir: Path) -> None:
        """Verify write_source creates a YAML file at the correct path."""
        # Import here to allow test to fail properly if class doesn't exist
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source()

        writer.write_source(source)

        expected_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        assert expected_path.exists()

    def test_write_source_creates_directory_structure(
        self, temp_catalog_dir: Path
    ) -> None:
        """Verify write_source creates necessary directory structure."""
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source(db_name="new_db", table_name="new_table")

        writer.write_source(source)

        expected_dir = temp_catalog_dir / "sources" / "new_db"
        assert expected_dir.is_dir()

    def test_write_source_yaml_content_is_valid(self, temp_catalog_dir: Path) -> None:
        """Verify written YAML file has valid content."""
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source()

        writer.write_source(source)

        yaml_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["db_name"] == "credit"
        assert data["table_name"] == "invoice"
        assert data["document_count"] == 1000
        assert "columns" in data
        assert len(data["columns"]) == 3

    def test_write_source_preserves_column_types(self, temp_catalog_dir: Path) -> None:
        """Verify column types are correctly serialized."""
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source()

        writer.write_source(source)

        yaml_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        columns_by_name = {col["name"]: col for col in data["columns"]}

        assert columns_by_name["_id"]["type"] == "objectid"
        assert columns_by_name["status"]["type"] == "string"
        assert columns_by_name["amount"]["type"] == "number"

    def test_write_source_includes_enumerable_unique_values(
        self, temp_catalog_dir: Path
    ) -> None:
        """Verify enumerable columns have unique_values in output."""
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source()

        writer.write_source(source)

        yaml_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        status_col = next(c for c in data["columns"] if c["name"] == "status")
        assert "unique_values" in status_col
        assert status_col["unique_values"] == ["OPEN", "PAID", "OVERDUE"]

    def test_write_source_overwrites_existing_file(
        self, temp_catalog_dir: Path
    ) -> None:
        """Verify write_source overwrites existing YAML file."""
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)

        # Write first version
        source_v1 = create_sample_source()
        source_v1 = SourceMetadataYaml(
            **{**source_v1.model_dump(), "document_count": 100}
        )
        writer.write_source(source_v1)

        # Write second version with updated document_count
        source_v2 = create_sample_source()
        source_v2 = SourceMetadataYaml(
            **{**source_v2.model_dump(), "document_count": 2000}
        )
        writer.write_source(source_v2)

        yaml_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["document_count"] == 2000


class TestCatalogFileWriterMergeManualFields:
    """Tests for CatalogFileWriter._merge_manual_fields() method."""

    def test_merge_preserves_description_from_existing(
        self, temp_catalog_dir: Path
    ) -> None:
        """Verify manual description is preserved during re-extraction."""
        from src.services.catalog_file_writer import CatalogFileWriter

        # Create existing file with manual enrichments
        create_existing_source_yaml(temp_catalog_dir, "credit", "invoice")

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        new_source = create_sample_source()

        # Write new source - should merge manual fields
        writer.write_source(new_source, merge_manual_fields=True)

        yaml_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Find status column
        status_col = next(c for c in data["columns"] if c["name"] == "status")

        # Description should be preserved from existing file
        assert (
            status_col.get("description") == "Status atual da fatura - descrição manual"
        )

    def test_merge_preserves_enrichment_status_from_existing(
        self, temp_catalog_dir: Path
    ) -> None:
        """Verify enrichment_status is preserved during re-extraction."""
        from src.services.catalog_file_writer import CatalogFileWriter

        create_existing_source_yaml(temp_catalog_dir, "credit", "invoice")

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        new_source = create_sample_source()

        writer.write_source(new_source, merge_manual_fields=True)

        yaml_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        status_col = next(c for c in data["columns"] if c["name"] == "status")
        assert status_col.get("enrichment_status") == "enriched"

    def test_merge_updates_extracted_fields(self, temp_catalog_dir: Path) -> None:
        """Verify extracted fields are updated even when preserving manual fields."""
        from src.services.catalog_file_writer import CatalogFileWriter

        create_existing_source_yaml(temp_catalog_dir, "credit", "invoice")

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        new_source = create_sample_source()

        writer.write_source(new_source, merge_manual_fields=True)

        yaml_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Document count should be updated (was 500, now 1000)
        assert data["document_count"] == 1000

        # Status column should have new sample_values
        status_col = next(c for c in data["columns"] if c["name"] == "status")
        assert status_col["sample_values"] == ["OPEN", "PAID"]
        assert status_col["unique_values"] == ["OPEN", "PAID", "OVERDUE"]

    def test_merge_handles_new_columns(self, temp_catalog_dir: Path) -> None:
        """Verify new columns are added without manual fields."""
        from src.services.catalog_file_writer import CatalogFileWriter

        create_existing_source_yaml(temp_catalog_dir, "credit", "invoice")

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)

        # Create source with a new column not in existing file
        new_source = create_sample_source()
        new_columns = list(new_source.columns)
        new_columns.append(
            ColumnMetadataYaml(
                path="new_field",
                name="new_field",
                type=InferredType.STRING,
                required=False,
                nullable=True,
                enumerable=False,
                presence_ratio=0.8,
                sample_values=["value1", "value2"],
            )
        )
        new_source = SourceMetadataYaml(
            **{**new_source.model_dump(), "columns": new_columns}
        )

        writer.write_source(new_source, merge_manual_fields=True)

        yaml_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # New column should exist without description
        new_col = next((c for c in data["columns"] if c["name"] == "new_field"), None)
        assert new_col is not None
        assert new_col.get("description") is None

    def test_merge_removes_deleted_columns(self, temp_catalog_dir: Path) -> None:
        """Verify columns that no longer exist are removed."""
        from src.services.catalog_file_writer import CatalogFileWriter

        create_existing_source_yaml(temp_catalog_dir, "credit", "invoice")

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        new_source = create_sample_source()  # Doesn't have "old_field"

        writer.write_source(new_source, merge_manual_fields=True)

        yaml_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # old_field should not exist
        old_col = next((c for c in data["columns"] if c["name"] == "old_field"), None)
        assert old_col is None

    def test_merge_without_existing_file_works(self, temp_catalog_dir: Path) -> None:
        """Verify merge works when there's no existing file."""
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        new_source = create_sample_source()

        # Should not raise, even with merge_manual_fields=True
        writer.write_source(new_source, merge_manual_fields=True)

        yaml_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        assert yaml_path.exists()


class TestCatalogFileWriterUpdateIndex:
    """Tests for CatalogFileWriter.update_index() method."""

    def test_update_index_creates_new_index(self, temp_catalog_dir: Path) -> None:
        """Verify update_index creates index file if not exists."""
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source()

        writer.update_index(source)

        index_path = temp_catalog_dir / "catalog.yaml"
        assert index_path.exists()

    def test_update_index_adds_new_source(self, temp_catalog_dir: Path) -> None:
        """Verify update_index adds new source to existing index."""
        from src.services.catalog_file_writer import CatalogFileWriter

        create_existing_index(temp_catalog_dir)

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        new_source = create_sample_source(db_name="billing", table_name="charge")

        writer.update_index(new_source)

        with (temp_catalog_dir / "catalog.yaml").open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        source_ids = [f"{s['db_name']}.{s['table_name']}" for s in data["sources"]]
        assert "billing.charge" in source_ids

    def test_update_index_updates_existing_source(self, temp_catalog_dir: Path) -> None:
        """Verify update_index updates existing source entry."""
        from src.services.catalog_file_writer import CatalogFileWriter

        create_existing_index(temp_catalog_dir)

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        # Re-extract existing source
        updated_source = create_sample_source(db_name="credit", table_name="invoice")

        writer.update_index(updated_source)

        with (temp_catalog_dir / "catalog.yaml").open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Should still have same number of credit.invoice entries (1)
        credit_invoices = [
            s
            for s in data["sources"]
            if s["db_name"] == "credit" and s["table_name"] == "invoice"
        ]
        assert len(credit_invoices) == 1

        # Timestamp should be updated
        assert credit_invoices[0]["last_extracted"] != "2026-01-15T10:00:00+00:00"

    def test_update_index_preserves_other_sources(self, temp_catalog_dir: Path) -> None:
        """Verify update_index preserves other sources in index."""
        from src.services.catalog_file_writer import CatalogFileWriter

        create_existing_index(temp_catalog_dir)

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        new_source = create_sample_source(db_name="billing", table_name="charge")

        writer.update_index(new_source)

        with (temp_catalog_dir / "catalog.yaml").open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Original sources should still exist
        source_ids = [f"{s['db_name']}.{s['table_name']}" for s in data["sources"]]
        assert "credit.invoice" in source_ids
        assert "payment.transaction" in source_ids

    def test_update_index_sets_correct_file_path(self, temp_catalog_dir: Path) -> None:
        """Verify update_index sets correct relative file path."""
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source(db_name="billing", table_name="charge")

        writer.update_index(source)

        with (temp_catalog_dir / "catalog.yaml").open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        billing_charge = next(
            s
            for s in data["sources"]
            if s["db_name"] == "billing" and s["table_name"] == "charge"
        )
        assert billing_charge["file_path"] == "sources/billing/charge.yaml"

    def test_update_index_updates_generated_at(self, temp_catalog_dir: Path) -> None:
        """Verify update_index updates the generated_at timestamp."""
        from src.services.catalog_file_writer import CatalogFileWriter

        create_existing_index(temp_catalog_dir)

        # Get original generated_at
        with (temp_catalog_dir / "catalog.yaml").open("r", encoding="utf-8") as f:
            original_data = yaml.safe_load(f)
        original_generated_at = original_data["generated_at"]

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source()

        writer.update_index(source)

        with (temp_catalog_dir / "catalog.yaml").open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["generated_at"] != original_generated_at


class TestCatalogFileWriterEnsureDirectories:
    """Tests for CatalogFileWriter._ensure_directories() method."""

    def test_ensure_directories_creates_sources_dir(
        self, temp_catalog_dir: Path
    ) -> None:
        """Verify _ensure_directories creates sources directory."""
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        writer._ensure_directories("new_db", "new_table")

        expected_dir = temp_catalog_dir / "sources" / "new_db"
        assert expected_dir.is_dir()

    def test_ensure_directories_is_idempotent(self, temp_catalog_dir: Path) -> None:
        """Verify _ensure_directories can be called multiple times."""
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)

        # Call twice - should not raise
        writer._ensure_directories("test_db", "test_table")
        writer._ensure_directories("test_db", "test_table")

        expected_dir = temp_catalog_dir / "sources" / "test_db"
        assert expected_dir.is_dir()


class TestCatalogFileWriterRollback:
    """Tests for CatalogFileWriter.write_source_with_rollback() method."""

    def test_write_with_rollback_succeeds(self, temp_catalog_dir: Path) -> None:
        """Verify write_source_with_rollback succeeds and removes backups."""
        from src.services.catalog_file_writer import CatalogFileWriter

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source()

        result_path = writer.write_source_with_rollback(source)

        # File should exist
        assert result_path.exists()

        # Index should exist
        index_path = temp_catalog_dir / "catalog.yaml"
        assert index_path.exists()

        # No backup files should exist
        backup_path = result_path.with_suffix(".yaml.bak")
        assert not backup_path.exists()

    def test_write_with_rollback_creates_backups_for_existing_files(
        self, temp_catalog_dir: Path
    ) -> None:
        """Verify backups are created for existing files during update."""
        from src.services.catalog_file_writer import CatalogFileWriter

        # Create existing files
        create_existing_source_yaml(temp_catalog_dir, "credit", "invoice")
        create_existing_index(temp_catalog_dir)

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source()

        result_path = writer.write_source_with_rollback(source)

        # File should exist with new content
        assert result_path.exists()
        with result_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["document_count"] == 1000  # New value

        # Backups should have been removed after success
        source_backup = result_path.with_suffix(".yaml.bak")
        index_backup = (temp_catalog_dir / "catalog.yaml").with_suffix(".yaml.bak")
        assert not source_backup.exists()
        assert not index_backup.exists()

    def test_write_with_rollback_restores_on_index_failure(
        self, temp_catalog_dir: Path
    ) -> None:
        """Verify rollback restores files when index update fails."""
        from unittest.mock import patch

        from src.services.catalog_file_writer import (
            CatalogFileWriter,
            ExtractionRollbackError,
        )

        # Create existing files with known content
        create_existing_source_yaml(temp_catalog_dir, "credit", "invoice")
        create_existing_index(temp_catalog_dir)

        # Read original content
        source_path = temp_catalog_dir / "sources" / "credit" / "invoice.yaml"
        original_source_content = source_path.read_text()
        index_path = temp_catalog_dir / "catalog.yaml"
        original_index_content = index_path.read_text()

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source()

        # Make update_index fail after write_source succeeds
        with (
            patch.object(
                writer,
                "update_index",
                side_effect=OSError("Simulated index write failure"),
            ),
            pytest.raises(ExtractionRollbackError) as exc_info,
        ):
            writer.write_source_with_rollback(source)

        # Verify the error wraps the original exception
        assert "credit.invoice" in str(exc_info.value)
        assert isinstance(exc_info.value.original_error, IOError)

        # Verify files were restored to original content
        assert source_path.read_text() == original_source_content
        assert index_path.read_text() == original_index_content

    def test_write_with_rollback_removes_new_file_on_failure(
        self, temp_catalog_dir: Path
    ) -> None:
        """Verify new files are removed on failure (no backup to restore)."""
        from unittest.mock import patch

        from src.services.catalog_file_writer import (
            CatalogFileWriter,
            ExtractionRollbackError,
        )

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source(db_name="new_db", table_name="new_table")

        source_path = temp_catalog_dir / "sources" / "new_db" / "new_table.yaml"

        # Make update_index fail
        with (
            patch.object(
                writer,
                "update_index",
                side_effect=OSError("Simulated failure"),
            ),
            pytest.raises(ExtractionRollbackError),
        ):
            writer.write_source_with_rollback(source)

        # The new file should have been removed
        assert not source_path.exists()

    def test_extraction_rollback_error_contains_original_exception(
        self,
    ) -> None:
        """Verify ExtractionRollbackError properly wraps the original error."""
        from src.services.catalog_file_writer import ExtractionRollbackError

        original = ValueError("Original error message")
        rollback_error = ExtractionRollbackError(
            message="Write failed", original_error=original
        )

        assert rollback_error.original_error is original
        assert "Write failed" in str(rollback_error)

    def test_write_with_rollback_handles_merge_manual_fields(
        self, temp_catalog_dir: Path
    ) -> None:
        """Verify merge_manual_fields works with rollback."""
        from src.services.catalog_file_writer import CatalogFileWriter

        # Create existing file with manual enrichments
        create_existing_source_yaml(temp_catalog_dir, "credit", "invoice")

        writer = CatalogFileWriter(catalog_path=temp_catalog_dir)
        source = create_sample_source()

        result_path = writer.write_source_with_rollback(
            source, merge_manual_fields=True
        )

        with result_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Manual fields should be preserved
        status_col = next(c for c in data["columns"] if c["name"] == "status")
        assert (
            status_col.get("description") == "Status atual da fatura - descrição manual"
        )
