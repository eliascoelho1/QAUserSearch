"""Query Executor service for running SQL queries against MongoDB.

This module handles the execution of validated SQL queries against
external MongoDB data sources via the SQL layer.
"""

import time
from typing import Any

import structlog
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.schemas.interpreter import QueryResultResponse, StoredQuery
from src.services.interpreter.validator import get_sql_validator

logger = structlog.get_logger(__name__)


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

        if mongo_client is not None:
            self._mongo_client = mongo_client
        else:
            self._mongo_client = AsyncIOMotorClient(self._settings.mongodb_uri)

    async def execute_query(
        self,
        stored_query: StoredQuery,
        limit: int | None = None,
    ) -> QueryResultResponse:
        """Execute a stored query and return results.

        Args:
            stored_query: The query to execute.
            limit: Optional limit override (default from settings).

        Returns:
            QueryResultResponse with query results.

        Raises:
            ValueError: If the query is invalid or blocked.
            RuntimeError: If execution fails.
        """
        log = logger.bind(query_id=str(stored_query.id))
        log.info("Starting query execution")

        # Validate query is safe
        if not stored_query.is_valid:
            raise ValueError("Query is not valid for execution")

        validation = self._sql_validator.validate(stored_query.sql)
        if not validation.is_valid:
            raise ValueError(
                f"Query blocked: {validation.error_message or validation.blocked_command}"
            )

        # Determine effective limit
        effective_limit = self._get_effective_limit(limit)

        # Execute the query
        start_time = time.perf_counter()
        try:
            rows = await self._execute_sql(stored_query.sql, effective_limit)
            execution_time_ms = int((time.perf_counter() - start_time) * 1000)

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

        except Exception as e:
            log.error("Query execution failed", error=str(e))
            raise RuntimeError(f"Query execution failed: {str(e)}")

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
