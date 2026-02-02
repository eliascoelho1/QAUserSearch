"""Unit tests for schema analyzer (field presence, cardinality)."""


class TestAnalyzeFieldPresence:
    """Tests for field presence ratio analysis."""

    def test_all_documents_have_field(self) -> None:
        """Test presence ratio when all documents have the field."""
        from src.services.schema_extraction.analyzer import analyze_field_presence

        field_data = {
            "values": ["a", "b", "c", "d", "e"],
            "present_count": 5,
        }
        total_docs = 5

        result = analyze_field_presence(field_data, total_docs)

        assert result["presence_ratio"] == 1.0
        assert result["is_required"] is True  # >= 95% threshold

    def test_field_presence_below_threshold(self) -> None:
        """Test presence ratio below required threshold (95%)."""
        from src.services.schema_extraction.analyzer import analyze_field_presence

        field_data = {
            "values": ["a", "b"],
            "present_count": 2,
        }
        total_docs = 10

        result = analyze_field_presence(field_data, total_docs)

        assert result["presence_ratio"] == 0.2
        assert result["is_required"] is False

    def test_field_presence_at_threshold(self) -> None:
        """Test presence ratio exactly at threshold (95%)."""
        from src.services.schema_extraction.analyzer import analyze_field_presence

        field_data = {
            "values": ["a"] * 95,
            "present_count": 95,
        }
        total_docs = 100

        result = analyze_field_presence(field_data, total_docs)

        assert result["presence_ratio"] == 0.95
        assert result["is_required"] is True

    def test_nullable_detection_with_nulls(self) -> None:
        """Test is_nullable when null values are present."""
        from src.services.schema_extraction.analyzer import analyze_field_presence

        field_data = {
            "values": ["a", None, "b", None],
            "present_count": 4,
        }
        total_docs = 4

        result = analyze_field_presence(field_data, total_docs)

        assert result["is_nullable"] is True

    def test_nullable_detection_without_nulls(self) -> None:
        """Test is_nullable when no null values are present."""
        from src.services.schema_extraction.analyzer import analyze_field_presence

        field_data = {
            "values": ["a", "b", "c"],
            "present_count": 3,
        }
        total_docs = 3

        result = analyze_field_presence(field_data, total_docs)

        assert result["is_nullable"] is False


class TestAnalyzeCardinality:
    """Tests for field cardinality analysis (enumerable detection)."""

    def test_low_cardinality_enumerable(self) -> None:
        """Test field is enumerable when unique values are below limit."""
        from src.services.schema_extraction.analyzer import analyze_cardinality

        field_data = {
            "values": ["A", "B", "C", "A", "B", "C", "A"],
        }
        cardinality_limit = 50

        result = analyze_cardinality(field_data, cardinality_limit)

        assert result["is_enumerable"] is True
        assert set(result["unique_values"]) == {"A", "B", "C"}

    def test_high_cardinality_not_enumerable(self) -> None:
        """Test field is not enumerable when unique values exceed limit."""
        from src.services.schema_extraction.analyzer import analyze_cardinality

        # Generate many unique values
        field_data = {
            "values": [f"value_{i}" for i in range(100)],
        }
        cardinality_limit = 50

        result = analyze_cardinality(field_data, cardinality_limit)

        assert result["is_enumerable"] is False
        assert result["unique_values"] is None

    def test_cardinality_at_limit(self) -> None:
        """Test field at exact cardinality limit is enumerable."""
        from src.services.schema_extraction.analyzer import analyze_cardinality

        field_data = {
            "values": [f"value_{i}" for i in range(50)],
        }
        cardinality_limit = 50

        result = analyze_cardinality(field_data, cardinality_limit)

        assert result["is_enumerable"] is True
        assert len(result["unique_values"]) == 50

    def test_cardinality_with_nulls_excluded(self) -> None:
        """Test that null values are excluded from cardinality calculation."""
        from src.services.schema_extraction.analyzer import analyze_cardinality

        field_data = {
            "values": ["A", None, "B", None, "A"],
        }
        cardinality_limit = 50

        result = analyze_cardinality(field_data, cardinality_limit)

        assert result["is_enumerable"] is True
        assert set(result["unique_values"]) == {"A", "B"}

    def test_cardinality_preserves_types(self) -> None:
        """Test that unique values preserve their original types."""
        from src.services.schema_extraction.analyzer import analyze_cardinality

        field_data = {
            "values": [True, False, True, False],
        }
        cardinality_limit = 50

        result = analyze_cardinality(field_data, cardinality_limit)

        assert result["is_enumerable"] is True
        assert set(result["unique_values"]) == {True, False}

    def test_empty_values(self) -> None:
        """Test cardinality analysis with no values."""
        from src.services.schema_extraction.analyzer import analyze_cardinality

        field_data: dict[str, list[object]] = {
            "values": [],
        }
        cardinality_limit = 50

        result = analyze_cardinality(field_data, cardinality_limit)

        assert result["is_enumerable"] is False
        assert result["unique_values"] is None


class TestSchemaAnalyzer:
    """Tests for the SchemaAnalyzer service."""

    def test_analyze_complete_schema(self) -> None:
        """Test complete schema analysis combining presence and cardinality."""
        from src.services.schema_extraction.analyzer import SchemaAnalyzer

        extracted_schema = {
            "status": {
                "inferred_type": "string",
                "values": ["A", "B", "C", "A", "B"],
                "present_count": 5,
                "sample_values": ["A", "B", "C"],
            },
            "consumer_id": {
                "inferred_type": "string",
                "values": [f"id_{i}" for i in range(100)],
                "present_count": 100,
                "sample_values": ["id_0", "id_1", "id_2", "id_3", "id_4"],
            },
        }
        total_docs = 100
        cardinality_limit = 50

        analyzer = SchemaAnalyzer(cardinality_limit=cardinality_limit)
        result = analyzer.analyze(extracted_schema, total_docs)

        # status should be enumerable
        assert result["status"]["is_enumerable"] is True
        assert set(result["status"]["unique_values"]) == {"A", "B", "C"}

        # consumer_id should not be enumerable
        assert result["consumer_id"]["is_enumerable"] is False
        assert result["consumer_id"]["unique_values"] is None

    def test_analyze_with_optional_fields(self) -> None:
        """Test analysis correctly identifies optional fields."""
        from src.services.schema_extraction.analyzer import SchemaAnalyzer

        extracted_schema = {
            "required_field": {
                "inferred_type": "string",
                "values": ["a"] * 100,
                "present_count": 100,
                "sample_values": ["a"],
            },
            "optional_field": {
                "inferred_type": "string",
                "values": ["b"] * 50,
                "present_count": 50,
                "sample_values": ["b"],
            },
        }
        total_docs = 100

        analyzer = SchemaAnalyzer()
        result = analyzer.analyze(extracted_schema, total_docs)

        assert result["required_field"]["is_required"] is True
        assert result["required_field"]["presence_ratio"] == 1.0
        assert result["optional_field"]["is_required"] is False
        assert result["optional_field"]["presence_ratio"] == 0.5
