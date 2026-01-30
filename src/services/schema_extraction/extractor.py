"""Schema extraction service for inferring types and flattening JSON documents."""

import contextlib
import re
from typing import Any

from src.schemas.enums import InferredType


class TypeInferrer:
    """Infers data types from JSON values."""

    # Regex patterns for special string types
    _OBJECTID_PATTERN = re.compile(r"^[a-f0-9]{24}$", re.IGNORECASE)
    _DATETIME_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
    )

    def infer(self, value: Any) -> InferredType:
        """Infer the type of a single value.

        Args:
            value: The value to infer type from.

        Returns:
            The inferred type as an InferredType enum.
        """
        if value is None:
            return InferredType.NULL

        if isinstance(value, bool):
            return InferredType.BOOLEAN

        if isinstance(value, int):
            return InferredType.INTEGER

        if isinstance(value, float):
            return InferredType.NUMBER

        if isinstance(value, str):
            return self._infer_string_type(value)

        if isinstance(value, list):
            return InferredType.ARRAY

        if isinstance(value, dict):
            return InferredType.OBJECT

        return InferredType.UNKNOWN

    def _infer_string_type(self, value: str) -> InferredType:
        """Infer type for string values (may be datetime or objectid)."""
        if self._OBJECTID_PATTERN.match(value):
            return InferredType.OBJECTID

        if self._DATETIME_PATTERN.match(value):
            return InferredType.DATETIME

        return InferredType.STRING


def flatten_fields(document: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested document into dot-notation paths.

    Args:
        document: The document to flatten.
        prefix: Current path prefix for recursion.

    Returns:
        A flattened dictionary with dot-notation keys.
    """
    result: dict[str, Any] = {}

    for key, value in document.items():
        path = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            # Recursively flatten nested objects
            nested = flatten_fields(value, path)
            result.update(nested)
        else:
            # Leaf value (including arrays)
            result[path] = value

    return result


class SchemaExtractor:
    """Extracts schema information from a collection of JSON documents."""

    def __init__(self) -> None:
        """Initialize the extractor with a type inferrer."""
        self._inferrer = TypeInferrer()

    def extract(self, documents: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Extract schema from a list of documents.

        Args:
            documents: List of JSON documents to extract schema from.

        Returns:
            A dictionary mapping field paths to their metadata:
            - inferred_type: The inferred data type
            - values: List of all values encountered
            - present_count: Number of documents containing this field
            - sample_values: Up to 5 unique sample values
        """
        schema: dict[str, dict[str, Any]] = {}

        for doc in documents:
            flattened = flatten_fields(doc)

            for path, value in flattened.items():
                if path not in schema:
                    schema[path] = {
                        "inferred_type": None,
                        "values": [],
                        "present_count": 0,
                        "sample_values": set(),
                    }

                field = schema[path]
                field["values"].append(value)
                field["present_count"] += 1

                # Collect sample values (up to 5 unique non-None values)
                if value is not None and len(field["sample_values"]) < 5:
                    # Convert unhashable types for the sample set
                    with contextlib.suppress(TypeError):
                        field["sample_values"].add(value)

                # Infer type (skip None to avoid overwriting good inferences)
                if value is not None:
                    inferred = self._inferrer.infer(value)
                    # Use first non-null inference
                    if field["inferred_type"] is None:
                        field["inferred_type"] = inferred
                    elif field["inferred_type"] != inferred:
                        # Type conflict - keep first seen or mark as unknown
                        pass

        # Finalize schema
        for _path, field in schema.items():
            # Convert sample_values set to list
            field["sample_values"] = list(field["sample_values"])

            # Default type to NULL if only nulls were seen
            if field["inferred_type"] is None:
                field["inferred_type"] = InferredType.NULL

        return schema
