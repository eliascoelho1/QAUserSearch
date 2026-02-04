"""Catalog YAML validation service using JSON Schema.

This module provides validation of catalog YAML files against the JSON Schema
defined in catalog/schema/source.schema.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog
import yaml
from jsonschema import Draft7Validator
from jsonschema import ValidationError as JsonSchemaValidationError

from src.config import get_settings

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ValidationError:
    """Represents a validation error with context.

    Attributes:
        field: The field path where the error occurred.
        message: Human-readable error message (in Portuguese when possible).
        file_path: Optional path to the file being validated.
    """

    field: str
    message: str
    file_path: Path | None = None

    def __str__(self) -> str:
        """Return a formatted string representation of the error."""
        if self.file_path:
            return f"{self.file_path}: {self.field} - {self.message}"
        return f"{self.field} - {self.message}"


# Portuguese error message templates
_ERROR_MESSAGES = {
    "required": "Campo obrigatório '{field}' não encontrado",
    "type": "Campo '{field}' deve ser do tipo {expected}, mas recebeu {actual}",
    "enum": "Campo '{field}' deve ser um dos valores: {expected}",
    "minimum": "Campo '{field}' deve ser maior ou igual a {limit}",
    "maximum": "Campo '{field}' deve ser menor ou igual a {limit}",
    "minItems": "Campo '{field}' deve ter pelo menos {limit} item(s)",
    "maxItems": "Campo '{field}' deve ter no máximo {limit} item(s)",
    "minLength": "Campo '{field}' deve ter pelo menos {limit} caractere(s)",
    "pattern": "Campo '{field}' não corresponde ao padrão esperado: {pattern}",
    "additionalProperties": "Campo '{field}' não é permitido neste objeto",
    "format": "Campo '{field}' deve estar no formato {expected}",
}


def _format_error_message(error: JsonSchemaValidationError) -> str:
    """Format a JSON Schema validation error into a Portuguese message.

    Args:
        error: The JSON Schema validation error.

    Returns:
        A human-readable error message in Portuguese.
    """
    validator = error.validator
    field = _get_field_path(error)

    if validator == "required":
        missing_field = error.message.split("'")[1] if "'" in error.message else "?"
        return _ERROR_MESSAGES["required"].format(field=missing_field)

    if validator == "type":
        expected = error.validator_value
        actual = type(error.instance).__name__
        return _ERROR_MESSAGES["type"].format(
            field=field, expected=expected, actual=actual
        )

    if validator == "enum":
        expected = ", ".join(str(v) for v in error.validator_value)  # type: ignore[union-attr]
        return _ERROR_MESSAGES["enum"].format(field=field, expected=expected)

    if validator in ("minimum", "maximum", "minItems", "maxItems", "minLength"):
        # validator is guaranteed to be a valid key at this point
        validator_key = str(validator)
        return _ERROR_MESSAGES[validator_key].format(
            field=field,
            limit=error.validator_value,
        )

    if validator == "pattern":
        return _ERROR_MESSAGES["pattern"].format(
            field=field, pattern=error.validator_value
        )

    if validator == "additionalProperties":
        # Extract the additional property name from the error
        # The instance is a dict, and schema has properties
        instance_keys = (
            set(error.instance.keys()) if hasattr(error.instance, "keys") else set()
        )
        schema_props = (
            error.schema.get("properties", {}) if isinstance(error.schema, dict) else {}
        )
        extra_props = list(instance_keys - set(schema_props.keys()))
        if extra_props:
            return _ERROR_MESSAGES["additionalProperties"].format(field=extra_props[0])
        return _ERROR_MESSAGES["additionalProperties"].format(field=field)

    if validator == "format":
        return _ERROR_MESSAGES["format"].format(
            field=field, expected=error.validator_value
        )

    # Fallback to original message
    return error.message


def _get_field_path(error: JsonSchemaValidationError) -> str:
    """Extract the field path from a JSON Schema validation error.

    Args:
        error: The JSON Schema validation error.

    Returns:
        The field path as a string (e.g., "columns[0].type").
    """
    if not error.absolute_path:
        # For required field errors, the field is in the message
        if error.validator == "required":
            missing = error.message.split("'")[1] if "'" in error.message else ""
            return missing
        return ""

    parts: list[str] = []
    for part in error.absolute_path:
        if isinstance(part, int):
            parts.append(f"[{part}]")
        else:
            if parts and not parts[-1].endswith("]"):
                parts.append(f".{part}")
            else:
                parts.append(str(part))

    return "".join(parts)


class CatalogValidator:
    """Validates catalog YAML files against the JSON Schema.

    This class provides methods to validate individual YAML data dicts,
    YAML files, or all YAML files in the catalog directory.

    Example:
        >>> validator = CatalogValidator()
        >>> errors = validator.validate_file(Path("catalog/sources/credit/invoice.yaml"))
        >>> if errors:
        ...     for error in errors:
        ...         print(error)
    """

    def __init__(
        self,
        schema_path: Path | str | None = None,
        catalog_path: Path | str | None = None,
    ) -> None:
        """Initialize the validator with schema and catalog paths.

        Args:
            schema_path: Path to the JSON Schema file. If None, uses default
                from settings (catalog/schema/source.schema.json).
            catalog_path: Path to the catalog directory. If None, uses default
                from settings.
        """
        settings = get_settings()

        if catalog_path is None:
            self._catalog_path = Path(settings.catalog_path)
        else:
            self._catalog_path = Path(catalog_path)

        if schema_path is None:
            self._schema_path = self._catalog_path / "schema" / "source.schema.json"
        else:
            self._schema_path = Path(schema_path)

        self._schema = self._load_schema()
        self._validator = Draft7Validator(self._schema)
        self._log = logger.bind(
            schema_path=str(self._schema_path),
            catalog_path=str(self._catalog_path),
        )

    def _load_schema(self) -> dict[str, Any]:
        """Load the JSON Schema from the schema file.

        Returns:
            The JSON Schema as a dictionary.

        Raises:
            FileNotFoundError: If the schema file doesn't exist.
        """
        if not self._schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self._schema_path}")

        with open(self._schema_path) as f:
            schema: dict[str, Any] = json.load(f)
            return schema

    def validate(self, data: dict[str, Any]) -> list[ValidationError]:
        """Validate a source metadata dictionary against the schema.

        Args:
            data: The source metadata dictionary to validate.

        Returns:
            A list of ValidationError objects. Empty list if valid.
        """
        errors: list[ValidationError] = []

        for error in self._validator.iter_errors(data):
            field = _get_field_path(error)
            message = _format_error_message(error)
            errors.append(ValidationError(field=field, message=message))

        return errors

    def validate_file(self, file_path: Path | str) -> list[ValidationError]:
        """Validate a YAML file against the schema.

        Args:
            file_path: Path to the YAML file to validate.

        Returns:
            A list of ValidationError objects. Empty list if valid.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self._log.debug("Validating file", file=str(file_path))

        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return [
                ValidationError(
                    field="",
                    message=f"Erro ao fazer parse do YAML: {e}",
                    file_path=file_path,
                )
            ]

        if data is None:
            return [
                ValidationError(
                    field="",
                    message="Arquivo YAML está vazio",
                    file_path=file_path,
                )
            ]

        errors = self.validate(data)

        # Add file path context to all errors
        return [
            ValidationError(
                field=error.field,
                message=error.message,
                file_path=file_path,
            )
            for error in errors
        ]

    def validate_all(self) -> list[ValidationError]:
        """Validate all YAML files in the catalog sources directory.

        Returns:
            A list of ValidationError objects from all files. Empty list if all valid.
        """
        sources_dir = self._catalog_path / "sources"

        if not sources_dir.exists():
            self._log.warning("Sources directory not found", path=str(sources_dir))
            return []

        all_errors: list[ValidationError] = []

        # Find all YAML files in sources directory
        yaml_files = list(sources_dir.glob("**/*.yaml")) + list(
            sources_dir.glob("**/*.yml")
        )

        self._log.info("Validating catalog files", count=len(yaml_files))

        for yaml_file in yaml_files:
            # Skip catalog.yaml index file if in sources
            if yaml_file.name == "catalog.yaml":
                continue

            try:
                errors = self.validate_file(yaml_file)
                all_errors.extend(errors)
            except Exception as e:
                self._log.error(
                    "Error validating file", file=str(yaml_file), error=str(e)
                )
                all_errors.append(
                    ValidationError(
                        field="",
                        message=f"Erro ao validar arquivo: {e}",
                        file_path=yaml_file,
                    )
                )

        return all_errors
