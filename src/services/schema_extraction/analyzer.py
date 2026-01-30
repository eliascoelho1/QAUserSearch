"""Schema analyzer for field presence and cardinality analysis."""

from typing import Any

from src.schemas.enums import InferredType

# Default threshold for required fields (95%)
REQUIRED_THRESHOLD = 0.95


def analyze_field_presence(
    field_data: dict[str, Any], total_docs: int
) -> dict[str, Any]:
    """Analyze field presence ratio and nullability.

    Args:
        field_data: Extracted field data containing values and present_count.
        total_docs: Total number of documents analyzed.

    Returns:
        Dictionary with:
        - presence_ratio: Ratio of documents containing this field
        - is_required: True if presence_ratio >= 95%
        - is_nullable: True if any null values were found
    """
    present_count = field_data.get("present_count", 0)
    values = field_data.get("values", [])

    presence_ratio = present_count / total_docs if total_docs > 0 else 0.0
    is_required = presence_ratio >= REQUIRED_THRESHOLD
    is_nullable = any(v is None for v in values)

    return {
        "presence_ratio": presence_ratio,
        "is_required": is_required,
        "is_nullable": is_nullable,
    }


def analyze_cardinality(
    field_data: dict[str, Any], cardinality_limit: int
) -> dict[str, Any]:
    """Analyze field cardinality for enumerable detection.

    Args:
        field_data: Extracted field data containing values.
        cardinality_limit: Maximum unique values for a field to be enumerable.

    Returns:
        Dictionary with:
        - is_enumerable: True if unique value count <= cardinality_limit
        - unique_values: List of unique values if enumerable, None otherwise
    """
    values = field_data.get("values", [])

    # Filter out None values for cardinality calculation
    non_null_values = [v for v in values if v is not None]

    if not non_null_values:
        return {
            "is_enumerable": False,
            "unique_values": None,
        }

    # Get unique values, handling unhashable types
    try:
        unique_set = set(non_null_values)
    except TypeError:
        # Contains unhashable types - not enumerable
        return {
            "is_enumerable": False,
            "unique_values": None,
        }

    is_enumerable = len(unique_set) <= cardinality_limit

    return {
        "is_enumerable": is_enumerable,
        "unique_values": list(unique_set) if is_enumerable else None,
    }


class SchemaAnalyzer:
    """Analyzes extracted schema for presence, cardinality, and field properties."""

    def __init__(self, cardinality_limit: int = 50) -> None:
        """Initialize the analyzer.

        Args:
            cardinality_limit: Maximum unique values for enumerable fields.
        """
        self._cardinality_limit = cardinality_limit

    def analyze(
        self, extracted_schema: dict[str, dict[str, Any]], total_docs: int
    ) -> dict[str, dict[str, Any]]:
        """Analyze an extracted schema to add presence and cardinality info.

        Args:
            extracted_schema: Schema extracted by SchemaExtractor.
            total_docs: Total number of documents analyzed.

        Returns:
            Enhanced schema with presence and cardinality analysis.
        """
        analyzed: dict[str, dict[str, Any]] = {}

        for path, field_data in extracted_schema.items():
            # Get base extracted info
            inferred_type = field_data.get("inferred_type", InferredType.UNKNOWN)
            sample_values = field_data.get("sample_values", [])

            # Analyze presence
            presence_info = analyze_field_presence(field_data, total_docs)

            # Analyze cardinality
            cardinality_info = analyze_cardinality(field_data, self._cardinality_limit)

            # Combine all analysis
            analyzed[path] = {
                "inferred_type": inferred_type,
                "sample_values": sample_values[:5],  # Limit to 5 samples
                "presence_ratio": presence_info["presence_ratio"],
                "is_required": presence_info["is_required"],
                "is_nullable": presence_info["is_nullable"],
                "is_enumerable": cardinality_info["is_enumerable"],
                "unique_values": cardinality_info["unique_values"],
            }

        return analyzed
