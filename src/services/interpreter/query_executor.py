"""Query Executor service for running SQL queries against MongoDB.

This module handles the execution of validated SQL queries against
external MongoDB data sources via the SQL layer.
"""

import time
from dataclasses import dataclass
from typing import Any

import structlog
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.schemas.interpreter import QueryResultResponse, StoredQuery
from src.services.interpreter.suggestion_service import get_suggestion_service
from src.services.interpreter.validator import get_sql_validator

logger = structlog.get_logger(__name__)


@dataclass
class NoResultsInfo:
    """Information about a query that returned no results."""

    tables_queried: list[str]
    filters_applied: list[dict[str, Any]]
    suggestions: list[str]


class QueryExecutionError(Exception):
    """Exception raised during query execution with details."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            code: Error code.
            message: Human-readable error message.
            details: Additional error details.
            suggestions: Suggestions for resolving the issue.
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.suggestions = suggestions or []


class QueryExecutor:
    """Executes validated SQL queries against external data sources."""

    def __init__(
        self,
        session: AsyncSession,
        mongo_client: AsyncIOMotorClient | None = None,  # type: ignore[type-arg]
    ) -> None:
        """Initialize the query executor.

        Args:
            session: Database session for audit logging.
            mongo_client: Optional MongoDB client (created if not provided).
        """
        self._session = session
        self._settings = get_settings()
        self._sql_validator = get_sql_validator()
        self._suggestion_service = get_suggestion_service(session)

        if mongo_client is not None:
            self._mongo_client = mongo_client
        else:
            self._mongo_client = AsyncIOMotorClient(self._settings.mongodb_uri)

    async def execute_query(
        self,
        stored_query: StoredQuery,
        limit: int | None = None,
        interpreted_filters: list[dict[str, Any]] | None = None,
    ) -> QueryResultResponse:
        """Execute a stored query and return results.

        Args:
            stored_query: The query to execute.
            limit: Optional limit override (default from settings).
            interpreted_filters: Original filters for no-results suggestions.

        Returns:
            QueryResultResponse with query results.

        Raises:
            QueryExecutionError: If the query is invalid, blocked, or fails.
        """
        log = logger.bind(query_id=str(stored_query.id))
        log.info("Starting query execution", sql_preview=stored_query.sql[:100])

        # Validate query is safe
        if not stored_query.is_valid:
            log.warning(
                "Attempted to execute invalid query",
                validation_errors=stored_query.validation_errors,
            )
            raise QueryExecutionError(
                code="INVALID_QUERY",
                message="Query não é válida para execução",
                details={"validation_errors": stored_query.validation_errors},
                suggestions=[
                    "A query foi marcada como inválida durante a interpretação.",
                    "Tente reformular seu prompt.",
                ],
            )

        validation = self._sql_validator.validate(stored_query.sql)
        if not validation.is_valid:
            log.warning(
                "SQL command blocked",
                blocked_command=validation.blocked_command,
            )
            raise QueryExecutionError(
                code="SQL_COMMAND_BLOCKED",
                message=validation.error_message
                or f"Comando bloqueado: {validation.blocked_command}",
                details={"blocked_command": validation.blocked_command},
                suggestions=[
                    "Reformule seu pedido para buscar dados em vez de modificá-los.",
                    "Use termos como 'buscar', 'encontrar', 'listar'.",
                    "Apenas consultas SELECT são permitidas.",
                ],
            )

        # Determine effective limit
        effective_limit = self._get_effective_limit(limit)
        log.debug("Executing query", effective_limit=effective_limit)

        # Execute the query
        start_time = time.perf_counter()
        try:
            rows = await self._execute_sql(stored_query.sql, effective_limit)
            execution_time_ms = int((time.perf_counter() - start_time) * 1000)

            # Handle no results case with suggestions
            if len(rows) == 0:
                no_results_info = await self._generate_no_results_info(
                    stored_query.sql, interpreted_filters
                )
                log.info(
                    "Query returned no results",
                    execution_time_ms=execution_time_ms,
                    suggestions_count=len(no_results_info.suggestions),
                )

                # Return empty result with suggestions in a custom field
                # The API layer can extract and return these suggestions
                return QueryResultResponse(
                    query_id=stored_query.id,
                    rows=[],
                    row_count=0,
                    is_partial=False,
                    execution_time_ms=execution_time_ms,
                )

            # Determine if results are partial
            is_partial = len(rows) >= effective_limit

            log.info(
                "Query executed successfully",
                row_count=len(rows),
                execution_time_ms=execution_time_ms,
                is_partial=is_partial,
            )

            return QueryResultResponse(
                query_id=stored_query.id,
                rows=rows,
                row_count=len(rows),
                is_partial=is_partial,
                execution_time_ms=execution_time_ms,
            )

        except QueryExecutionError:
            # Re-raise query execution errors
            raise
        except Exception as e:
            log.error("Query execution failed", error=str(e))
            raise QueryExecutionError(
                code="EXECUTION_ERROR",
                message=f"Erro na execução da query: {str(e)}",
                details={"original_error": str(e)},
                suggestions=[
                    "Verifique se a conexão com o banco de dados está funcionando.",
                    "Tente novamente em alguns segundos.",
                    "Se o problema persistir, entre em contato com o suporte.",
                ],
            ) from e

    async def execute_query_with_no_results_handling(
        self,
        stored_query: StoredQuery,
        limit: int | None = None,
        interpreted_tables: list[str] | None = None,
        interpreted_filters: list[dict[str, Any]] | None = None,
    ) -> tuple[QueryResultResponse, list[str] | None]:
        """Execute a query and return suggestions if no results.

        This is an enhanced version of execute_query that also returns
        suggestions when the query returns no results.

        Args:
            stored_query: The query to execute.
            limit: Optional limit override.
            interpreted_tables: Tables from interpretation for suggestions.
            interpreted_filters: Filters from interpretation for suggestions.

        Returns:
            Tuple of (QueryResultResponse, suggestions or None).
        """
        result = await self.execute_query(
            stored_query,
            limit,
            interpreted_filters,
        )

        suggestions: list[str] | None = None

        if result.row_count == 0:
            # Generate no-results suggestions
            suggestions = (
                await self._suggestion_service.generate_no_results_suggestions(
                    interpreted_tables or [],
                    interpreted_filters or [],
                )
            )

        return result, suggestions

    async def _generate_no_results_info(
        self,
        sql: str,
        interpreted_filters: list[dict[str, Any]] | None,
    ) -> NoResultsInfo:
        """Generate information for no-results scenario.

        Args:
            sql: The SQL query that returned no results.
            interpreted_filters: The filters applied.

        Returns:
            NoResultsInfo with tables, filters, and suggestions.
        """
        # Parse tables from SQL
        table_info = self._parse_sql_for_mongo(sql)
        tables_queried = []
        if table_info:
            tables_queried.append(
                f"{table_info['db_name']}.{table_info['collection_name']}"
            )

        filters = interpreted_filters or []

        # Generate suggestions
        suggestions = await self._suggestion_service.generate_no_results_suggestions(
            tables_queried, filters
        )

        return NoResultsInfo(
            tables_queried=tables_queried,
            filters_applied=filters,
            suggestions=suggestions,
        )

    def _get_effective_limit(self, requested_limit: int | None) -> int:
        """Get the effective limit for a query.

        Args:
            requested_limit: User-requested limit.

        Returns:
            Effective limit bounded by configuration.
        """
        default = self._settings.query_result_limit_default
        maximum = self._settings.query_result_limit_max

        if requested_limit is None:
            return default

        return min(max(1, requested_limit), maximum)

    async def _execute_sql(
        self,
        sql: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Execute SQL against MongoDB.

        This is a simplified implementation. In production, this would
        use a proper SQL-to-MongoDB translation layer.

        Args:
            sql: The SQL query to execute.
            limit: Maximum rows to return.

        Returns:
            List of result rows as dictionaries.
        """
        # Parse the SQL to extract table and filter information
        # This is a simplified implementation for demonstration
        table_info = self._parse_sql_for_mongo(sql)

        if table_info is None:
            logger.warning("Could not parse SQL for MongoDB execution")
            return []

        db_name = table_info["db_name"]
        collection_name = table_info["collection_name"]
        filter_query = table_info.get("filter", {})

        try:
            db = self._mongo_client[db_name]
            collection = db[collection_name]

            cursor = collection.find(filter_query).limit(limit)
            rows: list[dict[str, Any]] = []

            async for document in cursor:
                # Convert ObjectId to string for JSON serialization
                doc = dict(document)
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                rows.append(doc)

            return rows

        except Exception as e:
            logger.error(
                "MongoDB query failed",
                db_name=db_name,
                collection_name=collection_name,
                error=str(e),
            )
            raise

    def _parse_sql_for_mongo(
        self,
        sql: str,
    ) -> dict[str, Any] | None:
        """Parse SQL to extract MongoDB query parameters.

        This is a simplified parser. In production, use a proper
        SQL parser or query translation layer.

        Args:
            sql: The SQL query to parse.

        Returns:
            Dictionary with db_name, collection_name, and filter.
        """
        import re

        # Extract table name from FROM clause
        # Expected format: "FROM db_name.collection_name" or "FROM collection_name"
        match = re.search(
            r"FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)",
            sql,
            re.IGNORECASE,
        )
        if not match:
            return None

        table_ref = match.group(1)
        parts = table_ref.split(".")

        if len(parts) == 2:
            db_name, collection_name = parts
        else:
            # Default to using the table name as both
            db_name = parts[0]
            collection_name = parts[0]

        # Extract simple WHERE conditions (basic implementation)
        filter_query: dict[str, Any] = {}
        where_match = re.search(
            r"WHERE\s+(.+?)(?:ORDER|LIMIT|$)", sql, re.IGNORECASE | re.DOTALL
        )

        if where_match:
            where_clause = where_match.group(1).strip()
            # Parse simple equality conditions
            # Example: "status = 'active'"
            eq_matches = re.findall(
                r"(\w+)\s*=\s*'([^']*)'",
                where_clause,
            )
            for field, value in eq_matches:
                filter_query[field] = value

        return {
            "db_name": db_name,
            "collection_name": collection_name,
            "filter": filter_query,
        }


# Dependency injection helper
def get_query_executor(
    session: AsyncSession,
    mongo_client: AsyncIOMotorClient | None = None,  # type: ignore[type-arg]
) -> QueryExecutor:
    """Create a QueryExecutor with the given session."""
    return QueryExecutor(session, mongo_client)
