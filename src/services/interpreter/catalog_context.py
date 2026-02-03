"""Catalog context builder for LLM interpretation.

This service builds the catalog context that is sent to the LLM
to help it understand the available tables, columns, and their types.
"""

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.catalog import CatalogRepository

logger = structlog.get_logger(__name__)


class CatalogContext:
    """Builds and manages catalog context for LLM interpretation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the catalog context builder.

        Args:
            session: Database session for catalog queries.
        """
        self._session = session
        self._repository = CatalogRepository(session)

    async def get_available_tables(self) -> list[dict[str, Any]]:
        """Get list of available tables for query.

        Returns:
            List of table information dictionaries.
        """
        sources = await self._repository.list_sources(limit=100)
        return [
            {
                "db_name": source.db_name,
                "table_name": source.table_name,
                "full_name": f"{source.db_name}.{source.table_name}",
                "document_count": source.document_count,
            }
            for source in sources
        ]

    async def get_table_schema(
        self, db_name: str, table_name: str
    ) -> dict[str, Any] | None:
        """Get detailed schema for a specific table.

        Args:
            db_name: Database name.
            table_name: Table name.

        Returns:
            Table schema dictionary or None if not found.
        """
        source = await self._repository.get_source_by_identity(db_name, table_name)
        if source is None:
            return None

        columns = await self._repository.get_columns(source.id, limit=1000)

        return {
            "table": f"{db_name}.{table_name}",
            "document_count": source.document_count,
            "columns": [
                {
                    "name": col.column_name,
                    "path": col.column_path,
                    "type": col.inferred_type,
                    "is_required": col.is_required,
                    "is_nullable": col.is_nullable,
                    "is_enumerable": col.is_enumerable,
                    "possible_values": col.unique_values if col.is_enumerable else None,
                    "sample_values": (
                        col.sample_values[:5] if col.sample_values else None
                    ),
                    "description": col.description,
                    "presence_ratio": col.presence_ratio,
                }
                for col in columns
            ],
        }

    async def build_llm_context(self) -> str:
        """Build complete catalog context for the LLM prompt.

        This generates a Markdown-formatted context string containing
        all available tables and their schemas, which helps the LLM
        understand the data model for query generation.

        Returns:
            Markdown-formatted catalog context string.
        """
        sources = await self.get_available_tables()

        if not sources:
            return "# Catálogo de Dados QA\n\nNenhuma tabela disponível no catálogo."

        context_parts = ["# Catálogo de Dados QA\n"]

        for source in sources:
            schema = await self.get_table_schema(
                source["db_name"], source["table_name"]
            )
            if schema is None:
                continue

            # Table header
            doc_count = schema["document_count"]
            context_parts.append(f"\n## {schema['table']} ({doc_count:,} documentos)\n")

            # Column table header
            context_parts.append("| Coluna | Tipo | Obrigatório | Valores Possíveis |")
            context_parts.append("|--------|------|-------------|-------------------|")

            # Column rows
            for col in schema["columns"]:
                required = "✅ Sim" if col["is_required"] else "❌ Não"

                # Format possible values
                if col["possible_values"]:
                    values = ", ".join(f"`{v}`" for v in col["possible_values"][:10])
                    if len(col["possible_values"]) > 10:
                        values += f" ... (+{len(col['possible_values']) - 10})"
                else:
                    values = "-"

                context_parts.append(
                    f"| {col['name']} | {col['type']} | {required} | {values} |"
                )

        return "\n".join(context_parts)

    async def build_compact_context(self) -> dict[str, Any]:
        """Build compact catalog context for programmatic use.

        Returns:
            Dictionary with structured catalog information.
        """
        sources = await self.get_available_tables()
        tables: dict[str, Any] = {}

        for source in sources:
            schema = await self.get_table_schema(
                source["db_name"], source["table_name"]
            )
            if schema:
                tables[schema["table"]] = {
                    "document_count": schema["document_count"],
                    "columns": {
                        col["name"]: {
                            "type": col["type"],
                            "is_required": col["is_required"],
                            "possible_values": col["possible_values"],
                        }
                        for col in schema["columns"]
                    },
                }

        return {"tables": tables, "table_count": len(tables)}

    async def validate_table_exists(self, full_table_name: str) -> bool:
        """Check if a table exists in the catalog.

        Args:
            full_table_name: Table name in format 'db_name.table_name'.

        Returns:
            True if table exists, False otherwise.
        """
        parts = full_table_name.split(".", 1)
        if len(parts) != 2:
            return False

        db_name, table_name = parts
        source = await self._repository.get_source_by_identity(db_name, table_name)
        return source is not None

    async def validate_column_exists(
        self, full_table_name: str, column_name: str
    ) -> bool:
        """Check if a column exists in a table.

        Args:
            full_table_name: Table name in format 'db_name.table_name'.
            column_name: Column name to check.

        Returns:
            True if column exists, False otherwise.
        """
        parts = full_table_name.split(".", 1)
        if len(parts) != 2:
            return False

        db_name, table_name = parts
        source = await self._repository.get_source_by_identity(db_name, table_name)
        if source is None:
            return False

        columns = await self._repository.get_columns(source.id, limit=1000)
        return any(col.column_name == column_name for col in columns)

    async def find_similar_terms(
        self, term: str, max_results: int = 5
    ) -> list[dict[str, str]]:
        """Find catalog terms similar to a given term.

        This is used for error messages and suggestions when
        unrecognized terms are used in prompts.

        Args:
            term: The term to find matches for.
            max_results: Maximum number of similar terms to return.

        Returns:
            List of similar terms with their types (table/column).
        """
        term_lower = term.lower()
        similar: list[dict[str, str]] = []

        # Check table names
        sources = await self._repository.list_sources(limit=100)
        for source in sources:
            full_name = f"{source.db_name}.{source.table_name}"
            if term_lower in full_name.lower():
                similar.append({"term": full_name, "type": "table"})

        # Check column names
        for source in sources:
            columns = await self._repository.get_columns(source.id, limit=500)
            for col in columns:
                if term_lower in col.column_name.lower():
                    similar.append(
                        {
                            "term": col.column_name,
                            "type": "column",
                            "table": f"{source.db_name}.{source.table_name}",
                        }
                    )

        return similar[:max_results]
