"""Contract tests for CatalogValidator JSON Schema validation.

These tests verify that the CatalogValidator correctly validates YAML files
against the JSON Schema defined in catalog/schema/source.schema.json.
"""

from pathlib import Path
from typing import Any

import pytest

from src.services.catalog_validator import CatalogValidator


@pytest.fixture
def validator() -> CatalogValidator:
    """Create a CatalogValidator instance with the default schema."""
    return CatalogValidator()


@pytest.fixture
def valid_source_data() -> dict[str, Any]:
    """Return a valid source metadata dict that passes schema validation."""
    return {
        "db_name": "credit",
        "table_name": "invoice",
        "document_count": 1500,
        "extracted_at": "2026-02-03T10:30:00+00:00",
        "updated_at": "2026-02-03T10:30:00+00:00",
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
                "unique_values": ["OPEN", "PAID", "OVERDUE"],
                "description": "Status da fatura",
                "enrichment_status": "enriched",
            },
        ],
    }


class TestCatalogValidatorValidYaml:
    """Contract tests for CatalogValidator.validate() with valid YAML (T057)."""

    def test_validate_valid_source_returns_no_errors(
        self, validator: CatalogValidator, valid_source_data: dict[str, Any]
    ) -> None:
        """Validate that a well-formed source passes validation."""
        errors = validator.validate(valid_source_data)
        assert errors == []

    def test_validate_minimal_valid_source(self, validator: CatalogValidator) -> None:
        """Validate minimal valid source with only required fields."""
        minimal_source = {
            "db_name": "test_db",
            "table_name": "test_table",
            "document_count": 0,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1, 2, 3],
                }
            ],
        }
        errors = validator.validate(minimal_source)
        assert errors == []

    def test_validate_all_column_types_accepted(
        self, validator: CatalogValidator
    ) -> None:
        """Validate that all valid column types are accepted."""
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
        for col_type in valid_types:
            source = {
                "db_name": "test",
                "table_name": "test",
                "document_count": 1,
                "extracted_at": "2026-01-01T00:00:00Z",
                "columns": [
                    {
                        "path": "field",
                        "name": "field",
                        "type": col_type,
                        "required": True,
                        "nullable": False,
                        "enumerable": False,
                        "presence_ratio": 1.0,
                        "sample_values": [],
                    }
                ],
            }
            errors = validator.validate(source)
            assert errors == [], f"Type {col_type} should be valid"

    def test_validate_all_enrichment_status_values_accepted(
        self, validator: CatalogValidator
    ) -> None:
        """Validate that all valid enrichment_status values are accepted."""
        valid_statuses = ["not_enriched", "pending_enrichment", "enriched"]
        for status in valid_statuses:
            source = {
                "db_name": "test",
                "table_name": "test",
                "document_count": 1,
                "extracted_at": "2026-01-01T00:00:00Z",
                "columns": [
                    {
                        "path": "field",
                        "name": "field",
                        "type": "string",
                        "required": True,
                        "nullable": False,
                        "enumerable": False,
                        "presence_ratio": 1.0,
                        "sample_values": ["a"],
                        "enrichment_status": status,
                    }
                ],
            }
            errors = validator.validate(source)
            assert errors == [], f"Status {status} should be valid"

    def test_validate_optional_column_fields(self, validator: CatalogValidator) -> None:
        """Validate that optional column fields are accepted."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "field",
                    "name": "field",
                    "type": "string",
                    "required": True,
                    "nullable": False,
                    "enumerable": True,
                    "presence_ratio": 1.0,
                    "sample_values": ["a", "b"],
                    "unique_values": ["a", "b", "c"],
                    "description": "A test field",
                    "enrichment_status": "enriched",
                }
            ],
        }
        errors = validator.validate(source)
        assert errors == []


class TestCatalogValidatorMissingRequiredField:
    """Contract tests for CatalogValidator.validate() with missing required fields (T058)."""

    def test_validate_missing_db_name(self, validator: CatalogValidator) -> None:
        """Validate that missing db_name is reported."""
        source = {
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) == 1
        assert errors[0].field == "db_name"
        assert (
            "required" in errors[0].message.lower()
            or "obrigatório" in errors[0].message.lower()
        )

    def test_validate_missing_table_name(self, validator: CatalogValidator) -> None:
        """Validate that missing table_name is reported."""
        source = {
            "db_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) == 1
        assert errors[0].field == "table_name"

    def test_validate_missing_document_count(self, validator: CatalogValidator) -> None:
        """Validate that missing document_count is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) == 1
        assert errors[0].field == "document_count"

    def test_validate_missing_extracted_at(self, validator: CatalogValidator) -> None:
        """Validate that missing extracted_at is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": 1,
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) == 1
        assert errors[0].field == "extracted_at"

    def test_validate_missing_columns(self, validator: CatalogValidator) -> None:
        """Validate that missing columns is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
        }
        errors = validator.validate(source)
        assert len(errors) == 1
        assert errors[0].field == "columns"

    def test_validate_empty_columns_array(self, validator: CatalogValidator) -> None:
        """Validate that empty columns array is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [],
        }
        errors = validator.validate(source)
        assert len(errors) == 1
        assert errors[0].field == "columns"

    def test_validate_missing_column_required_field(
        self, validator: CatalogValidator
    ) -> None:
        """Validate that missing required column field is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    # missing "type"
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) == 1
        # The error message should mention 'type' is required
        assert "type" in errors[0].message.lower()

    def test_validate_multiple_missing_fields(
        self, validator: CatalogValidator
    ) -> None:
        """Validate that multiple missing fields are all reported."""
        source = {
            "db_name": "test",
            # missing table_name
            # missing document_count
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) == 2
        field_names = {e.field for e in errors}
        assert "table_name" in field_names
        assert "document_count" in field_names


class TestCatalogValidatorIncorrectType:
    """Contract tests for CatalogValidator.validate() with incorrect types (T059)."""

    def test_validate_db_name_not_string(self, validator: CatalogValidator) -> None:
        """Validate that non-string db_name is reported."""
        source = {
            "db_name": 123,  # should be string
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) >= 1
        assert any("db_name" in e.field for e in errors)

    def test_validate_document_count_not_integer(
        self, validator: CatalogValidator
    ) -> None:
        """Validate that non-integer document_count is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": "1500",  # should be integer
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) >= 1
        assert any("document_count" in e.field for e in errors)

    def test_validate_document_count_negative(
        self, validator: CatalogValidator
    ) -> None:
        """Validate that negative document_count is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": -1,  # should be >= 0
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) >= 1
        assert any("document_count" in e.field for e in errors)

    def test_validate_invalid_column_type(self, validator: CatalogValidator) -> None:
        """Validate that invalid column type is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "invalid_type",  # not in enum
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) >= 1
        assert any("type" in e.field for e in errors)

    def test_validate_invalid_enrichment_status(
        self, validator: CatalogValidator
    ) -> None:
        """Validate that invalid enrichment_status is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                    "enrichment_status": "invalid_status",  # not in enum
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) >= 1
        assert any("enrichment_status" in e.field for e in errors)

    def test_validate_presence_ratio_out_of_range(
        self, validator: CatalogValidator
    ) -> None:
        """Validate that presence_ratio > 1 is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.5,  # should be <= 1.0
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) >= 1
        assert any("presence_ratio" in e.field for e in errors)

    def test_validate_presence_ratio_negative(
        self, validator: CatalogValidator
    ) -> None:
        """Validate that negative presence_ratio is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": -0.5,  # should be >= 0.0
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) >= 1
        assert any("presence_ratio" in e.field for e in errors)

    def test_validate_columns_not_array(self, validator: CatalogValidator) -> None:
        """Validate that non-array columns is reported."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": "not_an_array",  # should be array
        }
        errors = validator.validate(source)
        assert len(errors) >= 1
        assert any("columns" in e.field for e in errors)

    def test_validate_invalid_db_name_pattern(
        self, validator: CatalogValidator
    ) -> None:
        """Validate that db_name not matching pattern is reported."""
        source = {
            "db_name": "123invalid",  # must start with letter or underscore
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) >= 1
        assert any("db_name" in e.field for e in errors)

    def test_validate_additional_properties_rejected(
        self, validator: CatalogValidator
    ) -> None:
        """Validate that unknown properties are rejected."""
        source = {
            "db_name": "test",
            "table_name": "test",
            "document_count": 1,
            "extracted_at": "2026-01-01T00:00:00Z",
            "unknown_field": "should not be here",
            "columns": [
                {
                    "path": "id",
                    "name": "id",
                    "type": "integer",
                    "required": True,
                    "nullable": False,
                    "enumerable": False,
                    "presence_ratio": 1.0,
                    "sample_values": [1],
                }
            ],
        }
        errors = validator.validate(source)
        assert len(errors) >= 1


class TestCatalogValidatorValidateFile:
    """Contract tests for CatalogValidator.validate_file()."""

    def test_validate_file_returns_errors_with_file_path(
        self, validator: CatalogValidator, tmp_path: Path
    ) -> None:
        """Validate that errors include file path context."""
        yaml_content = """
db_name: test
# missing table_name
document_count: 1
extracted_at: "2026-01-01T00:00:00Z"
columns:
  - path: id
    name: id
    type: integer
    required: true
    nullable: false
    enumerable: false
    presence_ratio: 1.0
    sample_values: [1]
"""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text(yaml_content)

        errors = validator.validate_file(yaml_file)
        assert len(errors) == 1
        assert errors[0].file_path == yaml_file

    def test_validate_file_valid_yaml(
        self, validator: CatalogValidator, tmp_path: Path
    ) -> None:
        """Validate that valid YAML file returns no errors."""
        yaml_content = """
db_name: test
table_name: test
document_count: 1
extracted_at: "2026-01-01T00:00:00Z"
columns:
  - path: id
    name: id
    type: integer
    required: true
    nullable: false
    enumerable: false
    presence_ratio: 1.0
    sample_values: [1]
"""
        yaml_file = tmp_path / "valid.yaml"
        yaml_file.write_text(yaml_content)

        errors = validator.validate_file(yaml_file)
        assert errors == []

    def test_validate_file_nonexistent_raises(
        self, validator: CatalogValidator, tmp_path: Path
    ) -> None:
        """Validate that nonexistent file raises FileNotFoundError."""
        nonexistent = tmp_path / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError):
            validator.validate_file(nonexistent)

    def test_validate_file_invalid_yaml_syntax(
        self, validator: CatalogValidator, tmp_path: Path
    ) -> None:
        """Validate that invalid YAML syntax returns parse error."""
        yaml_content = """
db_name: test
  invalid indentation: here
"""
        yaml_file = tmp_path / "invalid_syntax.yaml"
        yaml_file.write_text(yaml_content)

        errors = validator.validate_file(yaml_file)
        assert len(errors) == 1
        assert (
            "yaml" in errors[0].message.lower() or "parse" in errors[0].message.lower()
        )


class TestCatalogValidatorValidateAll:
    """Contract tests for CatalogValidator.validate_all()."""

    @pytest.fixture
    def schema_content(self) -> str:
        """Return the JSON schema content for tests."""
        return """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["db_name", "table_name", "document_count", "extracted_at", "columns"],
  "additionalProperties": false,
  "properties": {
    "db_name": {"type": "string", "minLength": 1},
    "table_name": {"type": "string", "minLength": 1},
    "document_count": {"type": "integer", "minimum": 0},
    "extracted_at": {"type": "string", "format": "date-time"},
    "updated_at": {"type": "string", "format": "date-time"},
    "columns": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["path", "name", "type", "required", "nullable", "enumerable", "presence_ratio", "sample_values"],
        "properties": {
          "path": {"type": "string", "minLength": 1},
          "name": {"type": "string", "minLength": 1},
          "type": {"type": "string"},
          "required": {"type": "boolean"},
          "nullable": {"type": "boolean"},
          "enumerable": {"type": "boolean"},
          "presence_ratio": {"type": "number", "minimum": 0, "maximum": 1},
          "sample_values": {"type": "array"}
        }
      }
    }
  }
}"""

    def test_validate_all_returns_all_errors(
        self, tmp_path: Path, schema_content: str
    ) -> None:
        """Validate that validate_all returns errors from all files."""
        # Create catalog structure with schema
        schema_dir = tmp_path / "schema"
        schema_dir.mkdir(parents=True)
        (schema_dir / "source.schema.json").write_text(schema_content)

        sources_dir = tmp_path / "sources" / "test_db"
        sources_dir.mkdir(parents=True)

        # Valid file
        valid_yaml = """
db_name: test_db
table_name: valid
document_count: 1
extracted_at: "2026-01-01T00:00:00Z"
columns:
  - path: id
    name: id
    type: integer
    required: true
    nullable: false
    enumerable: false
    presence_ratio: 1.0
    sample_values: [1]
"""
        (sources_dir / "valid.yaml").write_text(valid_yaml)

        # Invalid file
        invalid_yaml = """
db_name: test_db
# missing table_name
document_count: 1
extracted_at: "2026-01-01T00:00:00Z"
columns:
  - path: id
    name: id
    type: integer
    required: true
    nullable: false
    enumerable: false
    presence_ratio: 1.0
    sample_values: [1]
"""
        (sources_dir / "invalid.yaml").write_text(invalid_yaml)

        # Create validator with custom catalog path
        custom_validator = CatalogValidator(catalog_path=tmp_path)
        errors = custom_validator.validate_all()

        assert len(errors) == 1
        assert "table_name" in errors[0].field

    def test_validate_all_empty_catalog(
        self, tmp_path: Path, schema_content: str
    ) -> None:
        """Validate that validate_all with empty catalog returns no errors."""
        # Create schema
        schema_dir = tmp_path / "schema"
        schema_dir.mkdir(parents=True)
        (schema_dir / "source.schema.json").write_text(schema_content)

        sources_dir = tmp_path / "sources"
        sources_dir.mkdir(parents=True)

        custom_validator = CatalogValidator(catalog_path=tmp_path)
        errors = custom_validator.validate_all()

        assert errors == []
