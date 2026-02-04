"""YAML catalog extraction service."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from src.repositories.external import get_external_data_source
from src.schemas.catalog_yaml import ColumnMetadataYaml, SourceMetadataYaml
from src.schemas.enums import EnrichmentStatus, InferredType
from src.services.catalog_file_writer import CatalogFileWriter
from src.services.schema_extraction import SchemaAnalyzer, SchemaExtractor

logger = structlog.get_logger(__name__)


class CatalogYamlExtractor:
    """Service for extracting schema from external sources and writing to YAML files.

    This service orchestrates the extraction process and outputs directly to YAML,
    bypassing the PostgreSQL database for catalog storage.
    """

    def __init__(
        self,
        catalog_path: Path | str,
        sample_size: int = 500,
        cardinality_limit: int = 50,
    ) -> None:
        """Initialize the YAML catalog extractor.

        Args:
            catalog_path: Path to the catalog directory.
            sample_size: Number of documents to sample.
            cardinality_limit: Max unique values for enumerable fields.
        """
        self._catalog_path = Path(catalog_path)
        self._sample_size = sample_size
        self._cardinality_limit = cardinality_limit
        self._extractor = SchemaExtractor()
        self._analyzer = SchemaAnalyzer(cardinality_limit=cardinality_limit)
        self._writer = CatalogFileWriter(catalog_path=catalog_path)
        self._log = logger.bind(catalog_path=str(catalog_path))

    async def extract_to_yaml(
        self,
        db_name: str,
        table_name: str,
        sample_size: int | None = None,
        merge_manual_fields: bool = True,
    ) -> dict[str, Any]:
        """Extract schema from external source and write to YAML file.

        Args:
            db_name: External database name.
            table_name: External table/collection name.
            sample_size: Optional override for sample size.
            merge_manual_fields: Whether to preserve manual fields from existing file.

        Returns:
            Dictionary with extraction results:
            - source_id: The source ID (db_name.table_name)
            - columns_extracted: Number of columns found
            - enumerable_columns: Number of enumerable columns
            - file_path: Path to the generated YAML file

        Raises:
            ValueError: If no documents are found in the external source.
        """
        effective_sample_size = sample_size or self._sample_size

        log = self._log.bind(
            db_name=db_name,
            table_name=table_name,
            sample_size=effective_sample_size,
        )
        log.info("Starting YAML schema extraction")

        # Get external data source
        data_source = get_external_data_source()

        # Fetch sample documents
        log.info("Fetching sample documents")
        documents = await data_source.get_sample_documents(
            db_name=db_name,
            table_name=table_name,
            sample_size=effective_sample_size,
        )

        if not documents:
            log.warning("No documents found in external source")
            raise ValueError(f"No documents found in {db_name}.{table_name}")

        log.info("Documents fetched", document_count=len(documents))

        # Extract schema
        log.info("Extracting schema from documents")
        extracted_schema = self._extractor.extract(documents)

        # Analyze schema
        log.info("Analyzing schema")
        analyzed_schema = self._analyzer.analyze(extracted_schema, len(documents))

        # Convert to SourceMetadataYaml
        columns = self._convert_to_columns(analyzed_schema)
        source = SourceMetadataYaml(
            db_name=db_name,
            table_name=table_name,
            document_count=len(documents),
            extracted_at=datetime.now(tz=UTC),
            columns=columns,
        )

        # Write to YAML with rollback support
        log.info("Writing source to YAML file (with rollback)")
        file_path = self._writer.write_source_with_rollback(
            source, merge_manual_fields=merge_manual_fields
        )

        # Calculate stats
        enumerable_count = sum(1 for c in columns if c.enumerable)

        log.info(
            "YAML extraction completed",
            source_id=source.source_id,
            columns_extracted=len(columns),
            enumerable_columns=enumerable_count,
            file_path=str(file_path),
        )

        return {
            "source_id": source.source_id,
            "columns_extracted": len(columns),
            "enumerable_columns": enumerable_count,
            "file_path": str(file_path),
        }

    def _convert_to_columns(
        self, analyzed_schema: dict[str, dict[str, Any]]
    ) -> list[ColumnMetadataYaml]:
        """Convert analyzed schema to ColumnMetadataYaml list.

        Args:
            analyzed_schema: Analyzed schema from SchemaAnalyzer.

        Returns:
            List of ColumnMetadataYaml objects.
        """
        columns: list[ColumnMetadataYaml] = []

        for path, field_info in analyzed_schema.items():
            # Extract column name from path (last segment)
            column_name = path.split(".")[-1]

            # Convert InferredType
            inferred_type = field_info["inferred_type"]
            if hasattr(inferred_type, "value"):
                type_value = InferredType(inferred_type.value)
            else:
                type_value = InferredType(str(inferred_type))

            column = ColumnMetadataYaml(
                path=path,
                name=column_name,
                type=type_value,
                required=field_info["is_required"],
                nullable=field_info["is_nullable"],
                enumerable=field_info["is_enumerable"],
                presence_ratio=field_info["presence_ratio"],
                sample_values=field_info.get("sample_values", []),
                unique_values=field_info.get("unique_values"),
                description=None,  # Will be merged from existing if applicable
                enrichment_status=EnrichmentStatus.NOT_ENRICHED,
            )
            columns.append(column)

        return columns
