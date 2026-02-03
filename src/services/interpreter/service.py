"""Main InterpreterService for LLM Query Interpretation.

This service orchestrates the interpretation of natural language
prompts into SQL queries using the CrewAI crew.
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.audit_log import AuditLog
from src.schemas.interpreter import (
    EntityResponse,
    ErrorResponse,
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
from src.services.interpreter.suggestion_service import get_suggestion_service
from src.services.interpreter.validator import get_sql_validator

logger = structlog.get_logger(__name__)


@dataclass
class InterpretationError:
    """Error details from interpretation process."""

    code: str
    message: str
    details: dict[str, Any] | None = None
    suggestions: list[str] | None = None


class InterpretationException(Exception):
    """Exception raised during interpretation with error details."""

    def __init__(self, error: InterpretationError) -> None:
        """Initialize the exception.

        Args:
            error: The interpretation error details.
        """
        super().__init__(error.message)
        self.error = error

    def to_error_response(self) -> ErrorResponse:
        """Convert to ErrorResponse schema."""
        return ErrorResponse(
            code=self.error.code,
            message=self.error.message,
            details=self.error.details,
            suggestions=self.error.suggestions or [],
        )


class InterpreterService:
    """Service for interpreting natural language prompts into SQL queries."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the interpreter service.

        Args:
            session: Database session for persistence.
        """
        self._session = session
        self._catalog_context = CatalogContext(session)
        self._suggestion_service = get_suggestion_service(session)
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
            InterpretationException: If the prompt is invalid or interpretation fails.
            ValueError: If basic validation fails (for backwards compatibility).
        """
        log = logger.bind(prompt_preview=prompt[:100], prompt_length=len(prompt))
        log.info("Starting prompt interpretation")

        # Validate prompt
        if not prompt or not prompt.strip():
            log.warning("Empty prompt received")
            raise InterpretationException(
                InterpretationError(
                    code="INVALID_PROMPT",
                    message="Prompt não pode estar vazio",
                    suggestions=[
                        "Descreva o tipo de dados que você precisa buscar.",
                        "Use termos de negócio como 'usuários', 'faturas', 'cartões'.",
                    ],
                )
            )

        if len(prompt) > 2000:
            log.warning("Prompt too long", length=len(prompt))
            raise InterpretationException(
                InterpretationError(
                    code="PROMPT_TOO_LONG",
                    message="Prompt excede o limite de 2000 caracteres",
                    suggestions=[
                        "Reduza o tamanho do prompt para menos de 2000 caracteres.",
                        "Divida sua busca em consultas menores.",
                    ],
                )
            )

        # Build catalog context
        log.debug("Building catalog context")
        catalog_context = await self._catalog_context.build_llm_context()
        log.debug("Catalog context built successfully")

        # Get crew and run interpretation
        crew = get_interpreter_crew()
        log.debug("Starting LLM interpretation")

        try:
            crew_output = await crew.interpret(prompt, catalog_context)
            log.info(
                "LLM interpretation completed",
                status=crew_output.status,
                confidence=crew_output.interpretation.confidence,
                tables_count=len(crew_output.interpretation.target_tables),
                filters_count=len(crew_output.interpretation.filters),
            )
        except TimeoutError as err:
            log.error("LLM timeout during interpretation")
            raise InterpretationException(
                InterpretationError(
                    code="LLM_TIMEOUT",
                    message="O serviço de interpretação demorou mais que o esperado.",
                    suggestions=[
                        "Simplifique seu prompt.",
                        "Divida em buscas menores.",
                        "Tente novamente em alguns segundos.",
                    ],
                )
            ) from err
        except Exception as e:
            log.error("Error during crew interpretation", error=str(e))
            raise InterpretationException(
                InterpretationError(
                    code="INTERPRETATION_ERROR",
                    message=f"Erro na interpretação: {str(e)}",
                    suggestions=[
                        "Tente reformular o prompt.",
                        "Verifique se os termos usados existem no catálogo.",
                        "Use termos mais simples e diretos.",
                    ],
                )
            ) from e

        # Validate interpreted tables exist in catalog
        log.debug("Validating interpreted tables")
        unrecognized_tables = await self._validate_interpreted_tables(crew_output)
        if unrecognized_tables:
            log.warning(
                "Unrecognized tables detected",
                unrecognized_tables=unrecognized_tables,
            )
            # Generate suggestions for unrecognized terms
            all_suggestions: list[str] = []
            for table in unrecognized_tables:
                result = await self._suggestion_service.generate_suggestions_for_term(
                    table
                )
                all_suggestions.extend(result.suggestions)

            raise InterpretationException(
                InterpretationError(
                    code="UNRECOGNIZED_TABLES",
                    message=f"Tabelas não encontradas no catálogo: {', '.join(unrecognized_tables)}",
                    details={"unrecognized_tables": unrecognized_tables},
                    suggestions=all_suggestions
                    or [
                        "Verifique se as tabelas mencionadas existem no catálogo.",
                        "Consulte o catálogo para ver as tabelas disponíveis.",
                    ],
                )
            )

        # Validate interpreted columns exist
        log.debug("Validating interpreted columns")
        unrecognized_columns = await self._validate_interpreted_columns(crew_output)
        if unrecognized_columns:
            log.warning(
                "Unrecognized columns detected",
                unrecognized_columns=unrecognized_columns,
            )
            all_suggestions = []
            for col_info in unrecognized_columns:
                result = await self._suggestion_service.generate_suggestions_for_term(
                    col_info["column"]
                )
                all_suggestions.extend(result.suggestions)

            raise InterpretationException(
                InterpretationError(
                    code="UNRECOGNIZED_COLUMNS",
                    message=f"Colunas não encontradas: {', '.join(c['column'] for c in unrecognized_columns)}",
                    details={"unrecognized_columns": unrecognized_columns},
                    suggestions=all_suggestions
                    or [
                        "Verifique se as colunas mencionadas existem nas tabelas.",
                        "Consulte o esquema das tabelas para ver as colunas disponíveis.",
                    ],
                )
            )

        # Check for ambiguities detected by the LLM
        log.debug("Checking for ambiguities")
        ambiguity_info = self._check_ambiguities(crew_output)
        if ambiguity_info["has_critical_ambiguity"]:
            log.warning(
                "Critical ambiguities detected",
                ambiguities=ambiguity_info["ambiguities"],
                confidence=crew_output.interpretation.confidence,
            )
            raise InterpretationException(
                InterpretationError(
                    code="AMBIGUOUS_PROMPT",
                    message=f"O prompt contém ambiguidades: {', '.join(ambiguity_info['ambiguities'])}",
                    details={
                        "ambiguities": ambiguity_info["ambiguities"],
                        "confidence": crew_output.interpretation.confidence,
                    },
                    suggestions=ambiguity_info["suggestions"],
                )
            )

        # Process the crew output
        log.debug("Processing crew output")
        result = await self._process_crew_output(prompt, crew_output)
        log.info(
            "Interpretation completed successfully",
            interpretation_id=str(result.id),
            status=result.status.value,
            query_valid=result.query.is_valid,
        )
        return result

    async def _validate_interpreted_tables(
        self, crew_output: InterpreterCrewOutput
    ) -> list[str]:
        """Validate that interpreted tables exist in the catalog.

        Args:
            crew_output: The crew output containing interpreted tables.

        Returns:
            List of unrecognized table names.
        """
        unrecognized: list[str] = []

        for table in crew_output.interpretation.target_tables:
            exists = await self._catalog_context.validate_table_exists(table)
            if not exists:
                unrecognized.append(table)

        return unrecognized

    async def _validate_interpreted_columns(
        self, crew_output: InterpreterCrewOutput
    ) -> list[dict[str, Any]]:
        """Validate that interpreted columns exist in the catalog.

        Args:
            crew_output: The crew output containing interpreted filters.

        Returns:
            List of dicts with unrecognized column info.
        """
        unrecognized: list[dict[str, Any]] = []

        # Get all tables to check columns against
        tables = crew_output.interpretation.target_tables

        for filter_item in crew_output.interpretation.filters:
            column_name = filter_item.column
            found_in_any_table = False

            # Check if column exists in any of the target tables
            for table in tables:
                exists = await self._catalog_context.validate_column_exists(
                    table, column_name
                )
                if exists:
                    found_in_any_table = True
                    break

            if not found_in_any_table:
                unrecognized.append(
                    {
                        "column": column_name,
                        "searched_tables": tables,
                    }
                )

        return unrecognized

    def _check_ambiguities(self, crew_output: InterpreterCrewOutput) -> dict[str, Any]:
        """Check for ambiguities in the crew output.

        Analyzes the LLM's detected ambiguities and confidence level
        to determine if the interpretation has critical ambiguities
        that require user clarification.

        Args:
            crew_output: Output from the interpreter crew.

        Returns:
            Dict with:
                - has_critical_ambiguity: bool indicating if clarification needed
                - ambiguities: list of ambiguity descriptions
                - suggestions: list of suggestions for the user
        """
        # Confidence threshold below which we consider ambiguity critical
        CONFIDENCE_THRESHOLD = 0.5

        interpretation = crew_output.interpretation
        ambiguities = interpretation.ambiguities or []
        confidence = interpretation.confidence

        # Determine if ambiguity is critical
        # Critical if: low confidence AND has ambiguities, OR many ambiguities
        has_critical_ambiguity = False

        # Critical if: has ambiguities AND (low confidence OR many ambiguities 3+)
        if ambiguities and (confidence < CONFIDENCE_THRESHOLD or len(ambiguities) >= 3):
            has_critical_ambiguity = True

        # Generate suggestions based on ambiguities
        suggestions: list[str] = []

        if has_critical_ambiguity:
            suggestions.append("Reformule o prompt de forma mais específica.")

            # Add specific suggestions based on ambiguity types
            for ambiguity in ambiguities:
                ambiguity_lower = ambiguity.lower()

                if "tabela" in ambiguity_lower or "table" in ambiguity_lower:
                    suggestions.append("Especifique qual tabela você deseja consultar.")
                elif "coluna" in ambiguity_lower or "campo" in ambiguity_lower:
                    suggestions.append("Indique claramente quais campos você precisa.")
                elif "data" in ambiguity_lower or "período" in ambiguity_lower:
                    suggestions.append(
                        "Defina o período de tempo desejado (ex: últimos 30 dias)."
                    )
                elif "valor" in ambiguity_lower or "filtro" in ambiguity_lower:
                    suggestions.append("Especifique os valores exatos para filtragem.")

            # Remove duplicates while preserving order
            suggestions = list(dict.fromkeys(suggestions))

            # Add general suggestion if we don't have enough specific ones
            if len(suggestions) < 2:
                suggestions.append(
                    "Adicione mais detalhes sobre o que você está buscando."
                )

        return {
            "has_critical_ambiguity": has_critical_ambiguity,
            "ambiguities": ambiguities,
            "suggestions": suggestions,
        }

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
