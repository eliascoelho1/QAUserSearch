"""Catalog service for orchestrating schema extraction and persistence."""

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.catalog import CatalogRepository
from src.repositories.external import get_external_data_source
from src.services.schema_extraction import SchemaAnalyzer, SchemaExtractor

logger = structlog.get_logger(__name__)


class CatalogService:
    """Service for managing the schema catalog."""

    def __init__(
        self,
        session: AsyncSession,
        sample_size: int = 500,
        cardinality_limit: int = 50,
    ) -> None:
        """Initialize the catalog service.

        Args:
            session: Database session for persistence.
            sample_size: Number of documents to sample.
            cardinality_limit: Max unique values for enumerable fields.
        """
        self._session = session
        self._sample_size = sample_size
        self._cardinality_limit = cardinality_limit
        self._repository = CatalogRepository(session)
        self._extractor = SchemaExtractor()
        self._analyzer = SchemaAnalyzer(cardinality_limit=cardinality_limit)

    async def extract_and_persist(
        self, db_name: str, table_name: str, sample_size: int | None = None
    ) -> dict[str, Any]:
        """Extract schema from external source and persist to catalog.

        Args:
            db_name: External database name.
            table_name: External table/collection name.
            sample_size: Optional override for sample size.

        Returns:
            Dictionary with extraction results:
            - source_id: The catalog source ID
            - columns_extracted: Number of columns found
            - enumerable_columns: Number of enumerable columns
        """
        effective_sample_size = sample_size or self._sample_size

        log = logger.bind(
            db_name=db_name,
            table_name=table_name,
            sample_size=effective_sample_size,
        )
        log.info("Starting schema extraction")

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

        # Persist to catalog
        log.info("Persisting to catalog")
        source = await self._repository.create_or_update_source(
            db_name=db_name,
            table_name=table_name,
            document_count=len(documents),
        )

        # Prepare column data
        columns_data = []
        for path, field_info in analyzed_schema.items():
            # Extract column name from path (last segment)
            column_name = path.split(".")[-1]

            # Convert InferredType enum to string value
            inferred_type = field_info["inferred_type"]
            if hasattr(inferred_type, "value"):
                inferred_type = inferred_type.value

            columns_data.append(
                {
                    "column_name": column_name,
                    "column_path": path,
                    "inferred_type": str(inferred_type),
                    "is_required": field_info["is_required"],
                    "is_nullable": field_info["is_nullable"],
                    "is_enumerable": field_info["is_enumerable"],
                    "unique_values": field_info["unique_values"],
                    "sample_values": field_info["sample_values"],
                    "presence_ratio": field_info["presence_ratio"],
                }
            )

        # Upsert columns (replace existing)
        await self._repository.upsert_columns(source.id, columns_data)

        # Count stats
        enumerable_count = sum(1 for c in columns_data if c["is_enumerable"])

        log.info(
            "Schema extraction completed",
            source_id=source.id,
            columns_extracted=len(columns_data),
            enumerable_columns=enumerable_count,
        )

        return {
            "source_id": source.id,
            "columns_extracted": len(columns_data),
            "enumerable_columns": enumerable_count,
        }

    async def extract_all_known_sources(self) -> list[dict[str, Any]]:
        """Extract schemas from all known sources.

        Known sources are the 4 initial tables:
        - card_account_authorization.account_main
        - card_account_authorization.card_main
        - credit.invoice
        - credit.closed_invoice

        Returns:
            List of extraction results for each source.
        """
        known_sources = [
            ("card_account_authorization", "account_main"),
            ("card_account_authorization", "card_main"),
            ("credit", "invoice"),
            ("credit", "closed_invoice"),
        ]

        results = []
        for db_name, table_name in known_sources:
            try:
                result = await self.extract_and_persist(db_name, table_name)
                result["status"] = "success"
                results.append(result)
            except Exception as e:
                logger.error(
                    "Extraction failed",
                    db_name=db_name,
                    table_name=table_name,
                    error=str(e),
                )
                results.append(
                    {
                        "db_name": db_name,
                        "table_name": table_name,
                        "status": "error",
                        "error": str(e),
                    }
                )

        return results

    async def get_source_detail(self, source_id: int) -> dict[str, Any] | None:
        """Get detailed information about a source.

        Args:
            source_id: The source ID.

        Returns:
            Source details with columns and stats, or None if not found.
        """
        source = await self._repository.get_source_by_id(source_id)
        if source is None:
            return None

        columns = await self._repository.get_columns(source_id, limit=1000)

        # Calculate stats
        types_distribution: dict[str, int] = {}
        required_count = 0
        enumerable_count = 0

        for col in columns:
            # Type distribution
            col_type = col.inferred_type
            types_distribution[col_type] = types_distribution.get(col_type, 0) + 1

            if col.is_required:
                required_count += 1
            if col.is_enumerable:
                enumerable_count += 1

        return {
            "id": source.id,
            "db_name": source.db_name,
            "table_name": source.table_name,
            "document_count": source.document_count,
            "cataloged_at": source.cataloged_at,
            "updated_at": source.updated_at,
            "columns": columns,
            "stats": {
                "total_columns": len(columns),
                "required_columns": required_count,
                "enumerable_columns": enumerable_count,
                "types_distribution": types_distribution,
            },
        }

    async def delete_source(self, source_id: int) -> bool:
        """Delete a source from the catalog.

        Args:
            source_id: The source ID.

        Returns:
            True if deleted, False if not found.
        """
        return await self._repository.delete_source(source_id)
