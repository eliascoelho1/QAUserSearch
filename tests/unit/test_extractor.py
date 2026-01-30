"""Unit tests for schema extraction (TypeInferrer, flatten_fields)."""

from src.schemas.enums import InferredType


class TestTypeInferrer:
    """Tests for type inference from JSON values."""

    def test_infer_string(self) -> None:
        """Test string type inference."""
        from src.services.schema_extraction.extractor import TypeInferrer

        inferrer = TypeInferrer()
        assert inferrer.infer("hello") == InferredType.STRING
        assert inferrer.infer("") == InferredType.STRING
        assert inferrer.infer("some text with spaces") == InferredType.STRING

    def test_infer_integer(self) -> None:
        """Test integer type inference."""
        from src.services.schema_extraction.extractor import TypeInferrer

        inferrer = TypeInferrer()
        assert inferrer.infer(42) == InferredType.INTEGER
        assert inferrer.infer(0) == InferredType.INTEGER
        assert inferrer.infer(-100) == InferredType.INTEGER

    def test_infer_number_float(self) -> None:
        """Test float/number type inference."""
        from src.services.schema_extraction.extractor import TypeInferrer

        inferrer = TypeInferrer()
        assert inferrer.infer(3.14) == InferredType.NUMBER
        assert inferrer.infer(0.0) == InferredType.NUMBER
        assert inferrer.infer(-2.5) == InferredType.NUMBER

    def test_infer_boolean(self) -> None:
        """Test boolean type inference."""
        from src.services.schema_extraction.extractor import TypeInferrer

        inferrer = TypeInferrer()
        assert inferrer.infer(True) == InferredType.BOOLEAN
        assert inferrer.infer(False) == InferredType.BOOLEAN

    def test_infer_null(self) -> None:
        """Test null type inference."""
        from src.services.schema_extraction.extractor import TypeInferrer

        inferrer = TypeInferrer()
        assert inferrer.infer(None) == InferredType.NULL

    def test_infer_array(self) -> None:
        """Test array type inference."""
        from src.services.schema_extraction.extractor import TypeInferrer

        inferrer = TypeInferrer()
        assert inferrer.infer([]) == InferredType.ARRAY
        assert inferrer.infer([1, 2, 3]) == InferredType.ARRAY
        assert inferrer.infer(["a", "b"]) == InferredType.ARRAY

    def test_infer_object(self) -> None:
        """Test object type inference."""
        from src.services.schema_extraction.extractor import TypeInferrer

        inferrer = TypeInferrer()
        assert inferrer.infer({}) == InferredType.OBJECT
        assert inferrer.infer({"key": "value"}) == InferredType.OBJECT

    def test_infer_datetime_iso8601(self) -> None:
        """Test datetime type inference from ISO 8601 strings."""
        from src.services.schema_extraction.extractor import TypeInferrer

        inferrer = TypeInferrer()
        assert inferrer.infer("2026-01-30T10:00:00Z") == InferredType.DATETIME
        assert inferrer.infer("2026-01-30T10:00:00.123Z") == InferredType.DATETIME
        assert inferrer.infer("2026-01-30T10:00:00+00:00") == InferredType.DATETIME
        assert inferrer.infer("2025-10-07T11:47:09.803Z") == InferredType.DATETIME

    def test_infer_objectid(self) -> None:
        """Test MongoDB ObjectId type inference (24 hex characters)."""
        from src.services.schema_extraction.extractor import TypeInferrer

        inferrer = TypeInferrer()
        assert inferrer.infer("68e527ed7fc3841868bef0aa") == InferredType.OBJECTID
        assert inferrer.infer("507f1f77bcf86cd799439011") == InferredType.OBJECTID
        # Invalid ObjectId (wrong length or non-hex)
        assert inferrer.infer("not-an-objectid") == InferredType.STRING
        assert (
            inferrer.infer("68e527ed7fc3841868bef0") == InferredType.STRING
        )  # 22 chars

    def test_infer_unknown_type(self) -> None:
        """Test unknown type for unusual values."""
        from src.services.schema_extraction.extractor import TypeInferrer

        inferrer = TypeInferrer()

        # Custom objects that aren't dict/list
        class CustomObj:
            pass

        assert inferrer.infer(CustomObj()) == InferredType.UNKNOWN


class TestFlattenFields:
    """Tests for flattening nested JSON structures with dot notation."""

    def test_flatten_simple_object(self) -> None:
        """Test flattening a simple flat object."""
        from src.services.schema_extraction.extractor import flatten_fields

        doc = {"name": "John", "age": 30}
        result = flatten_fields(doc)

        assert "name" in result
        assert "age" in result
        assert result["name"] == "John"
        assert result["age"] == 30

    def test_flatten_nested_object(self) -> None:
        """Test flattening nested objects with dot notation."""
        from src.services.schema_extraction.extractor import flatten_fields

        doc = {"user": {"profile": {"name": "John", "email": "john@example.com"}}}
        result = flatten_fields(doc)

        assert "user.profile.name" in result
        assert "user.profile.email" in result
        assert result["user.profile.name"] == "John"

    def test_flatten_with_arrays(self) -> None:
        """Test that arrays are preserved as values, not flattened."""
        from src.services.schema_extraction.extractor import flatten_fields

        doc = {"tags": ["python", "fastapi"], "count": 2}
        result = flatten_fields(doc)

        assert "tags" in result
        assert result["tags"] == ["python", "fastapi"]
        assert result["count"] == 2

    def test_flatten_mixed_nesting(self) -> None:
        """Test flattening with mixed nesting levels."""
        from src.services.schema_extraction.extractor import flatten_fields

        doc = {
            "_id": "507f1f77bcf86cd799439011",
            "product_data": {
                "type": "HYBRID_LEVERAGED",
                "origin_flow": "manual-processing",
            },
            "status": "A",
        }
        result = flatten_fields(doc)

        assert "_id" in result
        assert "product_data.type" in result
        assert "product_data.origin_flow" in result
        assert "status" in result
        assert result["product_data.type"] == "HYBRID_LEVERAGED"

    def test_flatten_empty_object(self) -> None:
        """Test flattening an empty object."""
        from src.services.schema_extraction.extractor import flatten_fields

        result = flatten_fields({})
        assert result == {}

    def test_flatten_deeply_nested(self) -> None:
        """Test flattening deeply nested structures."""
        from src.services.schema_extraction.extractor import flatten_fields

        doc = {"level1": {"level2": {"level3": {"value": "deep"}}}}
        result = flatten_fields(doc)

        assert "level1.level2.level3.value" in result
        assert result["level1.level2.level3.value"] == "deep"


class TestSchemaExtractor:
    """Tests for the SchemaExtractor service."""

    def test_extract_schema_from_documents(self) -> None:
        """Test extracting schema from a list of documents."""
        from src.services.schema_extraction.extractor import SchemaExtractor

        documents = [
            {"name": "John", "age": 30, "active": True},
            {"name": "Jane", "age": 25, "active": False},
        ]

        extractor = SchemaExtractor()
        result = extractor.extract(documents)

        assert "name" in result
        assert "age" in result
        assert "active" in result
        assert result["name"]["inferred_type"] == InferredType.STRING
        assert result["age"]["inferred_type"] == InferredType.INTEGER
        assert result["active"]["inferred_type"] == InferredType.BOOLEAN

    def test_extract_with_nested_fields(self) -> None:
        """Test extraction with nested document structures."""
        from src.services.schema_extraction.extractor import SchemaExtractor

        documents = [
            {
                "_id": "68e527ed7fc3841868bef0aa",
                "product_data": {
                    "type": "HYBRID_LEVERAGED",
                    "updated_at": "2025-10-07T11:47:09.803Z",
                },
            }
        ]

        extractor = SchemaExtractor()
        result = extractor.extract(documents)

        assert "_id" in result
        assert "product_data.type" in result
        assert "product_data.updated_at" in result
        assert result["_id"]["inferred_type"] == InferredType.OBJECTID
        assert result["product_data.type"]["inferred_type"] == InferredType.STRING
        assert (
            result["product_data.updated_at"]["inferred_type"] == InferredType.DATETIME
        )

    def test_extract_collects_sample_values(self) -> None:
        """Test that extraction collects sample values for each field."""
        from src.services.schema_extraction.extractor import SchemaExtractor

        documents = [
            {"status": "A"},
            {"status": "B"},
            {"status": "C"},
        ]

        extractor = SchemaExtractor()
        result = extractor.extract(documents)

        assert "status" in result
        assert "sample_values" in result["status"]
        assert set(result["status"]["sample_values"]) == {"A", "B", "C"}
