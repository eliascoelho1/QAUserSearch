"""Main InterpreterService for LLM Query Interpretation.

This service orchestrates the interpretation of natural language
prompts into SQL queries using the CrewAI crew.
"""

from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.audit_log import AuditLog
from src.schemas.interpreter import (
    EntityResponse,
    FilterOperator,
    FilterResponse,
    InterpretationStatus,
    InterpretationWithQueryResponse,
    InterpreterCrewOutput,
    QueryResponse,
    StoredInterpretation,
    StoredQuery,
)
from src.services.interpreter.catalog_context import CatalogContext
from src.services.interpreter.crew import get_interpreter_crew
from src.services.interpreter.validator import get_sql_validator

logger = structlog.get_logger(__name__)


class InterpreterService:
    """Service for interpreting natural language prompts into SQL queries."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the interpreter service.

        Args:
            session: Database session for persistence.
        """
        self._session = session
        self._catalog_context = CatalogContext(session)
        self._sql_validator = get_sql_validator()
        self._settings = get_settings()

        # In-memory storage for interpretations and queries
        # In production, this should be Redis or database
        self._interpretations: dict[UUID, StoredInterpretation] = {}
        self._queries: dict[UUID, StoredQuery] = {}

    async def interpret_prompt(self, prompt: str) -> InterpretationWithQueryResponse:
        """Interpret a natural language prompt and generate a SQL query.

        Args:
            prompt: The natural language prompt from the user.

        Returns:
            InterpretationWithQueryResponse with the interpretation and query.

        Raises:
            ValueError: If the prompt is invalid or interpretation fails.
        """
        log = logger.bind(prompt_preview=prompt[:100])
        log.info("Starting prompt interpretation")

        # Validate prompt
        if not prompt or not prompt.strip():
            raise ValueError("Prompt não pode estar vazio")

        if len(prompt) > 2000:
            raise ValueError("Prompt excede o limite de 2000 caracteres")

        # Build catalog context
        catalog_context = await self._catalog_context.build_llm_context()

        # Get crew and run interpretation
        crew = get_interpreter_crew()
        crew_output = await crew.interpret(prompt, catalog_context)

        # Process the crew output
        return await self._process_crew_output(prompt, crew_output)

    async def _process_crew_output(
        self,
        original_prompt: str,
        crew_output: InterpreterCrewOutput,
    ) -> InterpretationWithQueryResponse:
        """Process the crew output and create response objects.

        Args:
            original_prompt: The original user prompt.
            crew_output: Output from the interpreter crew.

        Returns:
            InterpretationWithQueryResponse with processed data.
        """
        interpretation_id = uuid4()
        query_id = uuid4()

        # Determine status
        if crew_output.status == "blocked":
            status = InterpretationStatus.BLOCKED
            # Log blocked query to audit
            await self._log_blocked_query(
                original_prompt,
                crew_output.refined_query.sql_query
                if crew_output.refined_query
                else "",
                crew_output.validation.blocked_commands,
            )
        elif crew_output.status == "ready":
            status = InterpretationStatus.READY
        else:
            status = InterpretationStatus.ERROR

        # Validate the generated SQL
        sql_query = (
            crew_output.refined_query.sql_query if crew_output.refined_query else ""
        )
        sql_validation = self._sql_validator.validate(sql_query)

        if not sql_validation.is_valid:
            status = InterpretationStatus.BLOCKED
            await self._log_blocked_query(
                original_prompt,
                sql_query,
                [sql_validation.blocked_command]
                if sql_validation.blocked_command
                else [],
            )

        # Extract entities from interpretation
        entities = self._extract_entities(crew_output)

        # Extract filters from interpretation
        filters = self._extract_filters(crew_output)

        # Create query response
        query_response = QueryResponse(
            id=query_id,
            sql=sql_query,
            is_valid=sql_validation.is_valid and crew_output.validation.is_valid,
            validation_errors=(sql_validation.security_warnings or [])
            + (crew_output.validation.blocked_commands or []),
        )

        # Store interpretation and query for later retrieval
        stored_interpretation = StoredInterpretation(
            id=interpretation_id,
            original_prompt=original_prompt,
            interpretation=crew_output.interpretation,
            validation=crew_output.validation,
            refined_query=crew_output.refined_query,
            status=status,
        )
        self._interpretations[interpretation_id] = stored_interpretation

        stored_query = StoredQuery(
            id=query_id,
            interpretation_id=interpretation_id,
            sql=sql_query,
            is_valid=query_response.is_valid,
            validation_errors=query_response.validation_errors,
        )
        self._queries[query_id] = stored_query

        return InterpretationWithQueryResponse(
            id=interpretation_id,
            status=status,
            summary=crew_output.interpretation.natural_explanation,
            entities=entities,
            filters=filters,
            confidence=crew_output.interpretation.confidence,
            query=query_response,
        )

    def _extract_entities(
        self, crew_output: InterpreterCrewOutput
    ) -> list[EntityResponse]:
        """Extract entity responses from crew output.

        Args:
            crew_output: Output from the interpreter crew.

        Returns:
            List of EntityResponse objects.
        """
        entities: list[EntityResponse] = []

        for table in crew_output.interpretation.target_tables:
            # Parse table name (format: db_name.table_name)
            parts = table.split(".", 1)
            if len(parts) == 2:
                db_name, table_name = parts
                entities.append(
                    EntityResponse(
                        name=table_name,
                        table_name=table,
                        alias=table_name[0] if table_name else None,
                    )
                )
            else:
                entities.append(
                    EntityResponse(
                        name=table,
                        table_name=table,
                    )
                )

        return entities

    def _extract_filters(
        self, crew_output: InterpreterCrewOutput
    ) -> list[FilterResponse]:
        """Extract filter responses from crew output.

        Args:
            crew_output: Output from the interpreter crew.

        Returns:
            List of FilterResponse objects.
        """
        filters: list[FilterResponse] = []

        for f in crew_output.interpretation.filters:
            # Map string operator to enum
            try:
                operator = FilterOperator(f.operator)
            except ValueError:
                operator = FilterOperator.EQUALS

            filters.append(
                FilterResponse(
                    field=f.column,
                    operator=operator,
                    value=f.value,
                    is_temporal=f.is_temporal,
                )
            )

        return filters

    async def _log_blocked_query(
        self,
        original_prompt: str,
        blocked_query: str,
        blocked_commands: list[str],
    ) -> None:
        """Log a blocked query to the audit log.

        Args:
            original_prompt: The original user prompt.
            blocked_query: The SQL query that was blocked.
            blocked_commands: List of commands that caused blocking.
        """
        if not blocked_commands:
            blocked_commands = ["UNKNOWN"]

        audit_log = AuditLog(
            blocked_query=blocked_query or "N/A",
            original_prompt=original_prompt,
            blocked_command=blocked_commands[0],
            reason=f"Comandos bloqueados: {', '.join(blocked_commands)}",
        )

        self._session.add(audit_log)
        await self._session.flush()

        logger.warning(
            "Query blocked and logged",
            blocked_commands=blocked_commands,
        )

    async def get_query(self, query_id: UUID) -> StoredQuery | None:
        """Get a stored query by ID.

        Args:
            query_id: The query ID.

        Returns:
            StoredQuery or None if not found.
        """
        return self._queries.get(query_id)

    async def get_interpretation(
        self, interpretation_id: UUID
    ) -> StoredInterpretation | None:
        """Get a stored interpretation by ID.

        Args:
            interpretation_id: The interpretation ID.

        Returns:
            StoredInterpretation or None if not found.
        """
        return self._interpretations.get(interpretation_id)


# Dependency injection helper
def get_interpreter_service(session: AsyncSession) -> InterpreterService:
    """Create an InterpreterService with the given session."""
    return InterpreterService(session)
