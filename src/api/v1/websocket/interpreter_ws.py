"""WebSocket endpoint for real-time query interpretation with streaming feedback.

This module provides the WebSocket endpoint /ws/query/interpret that enables:
- Real-time status updates during interpretation (interpreting, validating, refining, ready)
- Chunk streaming for LLM processing feedback
- Interpretation result with summary and entities/filters before query execution
"""

import json
from typing import Any
from uuid import uuid4

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from src.api.v1.websocket.connection_manager import get_connection_manager
from src.core.database import get_db_manager
from src.schemas.interpreter import (
    EntityResponse,
    FilterOperator,
    FilterResponse,
    InterpretationResponse,
    InterpretationStatus,
    InterpreterCrewOutput,
    QueryResponse,
)
from src.schemas.websocket import (
    WSChunkMessage,
    WSErrorMessage,
    WSInterpretationMessage,
    WSQueryMessage,
    WSStatusMessage,
)
from src.services.interpreter.catalog_context import CatalogContext
from src.services.interpreter.crew import get_interpreter_crew
from src.services.interpreter.validator import get_sql_validator

logger = structlog.get_logger(__name__)

router = APIRouter()


class WSInterpretRequest(BaseModel):
    """WebSocket request for interpretation."""

    type: str  # "interpret"
    prompt: str
    session_context: dict[str, Any] | None = None  # For context preservation


class SessionContext(BaseModel):
    """Session context for prompt refinement."""

    session_id: str
    previous_prompts: list[str] = []
    previous_interpretations: list[dict[str, Any]] = []
    current_entities: list[str] = []
    current_filters: list[dict[str, Any]] = []


# In-memory session storage (in production, use Redis)
_session_contexts: dict[str, SessionContext] = {}


def get_session_context(session_id: str) -> SessionContext:
    """Get or create session context."""
    if session_id not in _session_contexts:
        _session_contexts[session_id] = SessionContext(session_id=session_id)
    return _session_contexts[session_id]


def update_session_context(
    session_id: str,
    prompt: str,
    interpretation: InterpretationResponse,
) -> None:
    """Update session context with new interpretation."""
    context = get_session_context(session_id)
    context.previous_prompts.append(prompt)
    context.previous_interpretations.append(
        {
            "prompt": prompt,
            "summary": interpretation.summary,
            "entities": [e.model_dump() for e in interpretation.entities],
            "filters": [f.model_dump(mode="json") for f in interpretation.filters],
            "confidence": interpretation.confidence,
        }
    )
    # Keep only last 5 interactions
    if len(context.previous_prompts) > 5:
        context.previous_prompts = context.previous_prompts[-5:]
        context.previous_interpretations = context.previous_interpretations[-5:]


class WebSocketInterpreterHandler:
    """Handler for WebSocket interpretation with streaming."""

    def __init__(self, session_id: str, websocket: WebSocket) -> None:
        """Initialize the handler."""
        self._session_id = session_id
        self._websocket = websocket
        self._connection_manager = get_connection_manager()
        self._sql_validator = get_sql_validator()

    async def send_status(self, status: str, message: str) -> None:
        """Send a status update message."""
        msg = WSStatusMessage.create(status=status, message=message)
        await self._connection_manager.send_message(self._session_id, msg)

    async def send_chunk(self, content: str, agent: str) -> None:
        """Send a chunk message from LLM processing."""
        msg = WSChunkMessage.create(content=content, agent=agent)
        await self._connection_manager.send_message(self._session_id, msg)

    async def send_interpretation(self, interpretation: InterpretationResponse) -> None:
        """Send interpretation result message."""
        msg = WSInterpretationMessage(data=interpretation)
        await self._connection_manager.send_message(self._session_id, msg)

    async def send_query(self, query: QueryResponse) -> None:
        """Send generated query message."""
        msg = WSQueryMessage(data=query)
        await self._connection_manager.send_message(self._session_id, msg)

    async def send_error(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ) -> None:
        """Send error message."""
        msg = WSErrorMessage.create(
            code=code,
            message=message,
            details=details,
            suggestions=suggestions,
        )
        await self._connection_manager.send_message(self._session_id, msg)

    async def process_interpret_request(self, prompt: str) -> None:
        """Process an interpretation request with streaming feedback.

        This method orchestrates the interpretation flow with real-time updates:
        1. INTERPRETING - Analyzing the prompt
        2. VALIDATING - Checking security and catalog compliance
        3. REFINING - Generating optimized SQL query
        4. READY - Interpretation complete
        """
        log = logger.bind(
            session_id=self._session_id,
            prompt_preview=prompt[:100] if len(prompt) > 100 else prompt,
        )
        log.info("Starting WebSocket interpretation")

        try:
            # Validate prompt
            if not prompt or not prompt.strip():
                await self.send_error(
                    code="INVALID_PROMPT",
                    message="Prompt não pode estar vazio",
                    suggestions=["Descreva o tipo de dados que você precisa buscar"],
                )
                return

            if len(prompt) > 2000:
                await self.send_error(
                    code="PROMPT_TOO_LONG",
                    message="Prompt excede o limite de 2000 caracteres",
                    suggestions=["Reduza o tamanho do prompt"],
                )
                return

            # Phase 1: INTERPRETING
            await self.send_status(
                status=InterpretationStatus.INTERPRETING.value,
                message="Analisando prompt...",
            )
            await self.send_chunk(
                content="Identificando entidades e termos de negócio...",
                agent="interpreter",
            )

            # Build catalog context
            db_manager = get_db_manager()
            async with db_manager.session() as session:
                catalog_context = CatalogContext(session)
                catalog_markdown = await catalog_context.build_llm_context()

            await self.send_chunk(
                content="Mapeando para tabelas do catálogo...",
                agent="interpreter",
            )

            # Get crew and start interpretation
            crew = get_interpreter_crew()

            # Simulate progress updates during LLM processing
            await self.send_chunk(
                content="Extraindo filtros e condições...",
                agent="interpreter",
            )

            # Phase 2: VALIDATING
            await self.send_status(
                status=InterpretationStatus.VALIDATING.value,
                message="Validando segurança da query...",
            )
            await self.send_chunk(
                content="Verificando comandos SQL permitidos...",
                agent="validator",
            )

            # Phase 3: REFINING
            await self.send_status(
                status=InterpretationStatus.REFINING.value,
                message="Otimizando query...",
            )
            await self.send_chunk(
                content="Aplicando limites e ordenação...",
                agent="refiner",
            )

            # Execute the crew
            crew_output = await crew.interpret(prompt, catalog_markdown)

            # Process the crew output
            interpretation_id = uuid4()
            query_id = uuid4()

            # Determine status
            if crew_output.status == "blocked":
                status = InterpretationStatus.BLOCKED
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
                await self.send_error(
                    code="SQL_COMMAND_BLOCKED",
                    message=f"Comando {sql_validation.blocked_command} não é permitido. Apenas consultas SELECT são aceitas.",
                    details={"blocked_command": sql_validation.blocked_command},
                    suggestions=[
                        "Reformule seu pedido para buscar dados em vez de modificá-los",
                        "Use termos como 'buscar', 'encontrar', 'listar'",
                    ],
                )
                return

            # Extract entities
            entities = self._extract_entities(crew_output)

            # Extract filters
            filters = self._extract_filters(crew_output)

            # Create interpretation response
            interpretation = InterpretationResponse(
                id=interpretation_id,
                status=status,
                summary=crew_output.interpretation.natural_explanation,
                entities=entities,
                filters=filters,
                confidence=crew_output.interpretation.confidence,
            )

            # Send interpretation result BEFORE query execution
            await self.send_interpretation(interpretation)

            # Send confidence feedback as a chunk
            from src.schemas.websocket import (
                get_confidence_description,
                get_confidence_label,
            )

            confidence_pct = int(crew_output.interpretation.confidence * 100)
            confidence_label = get_confidence_label(
                crew_output.interpretation.confidence
            )
            confidence_desc = get_confidence_description(
                crew_output.interpretation.confidence
            )
            await self.send_chunk(
                content=f"Confiança: {confidence_pct}% ({confidence_label}) - {confidence_desc}",
                agent="interpreter",
            )

            # Update session context for future refinements
            update_session_context(self._session_id, prompt, interpretation)

            # Create and send query response
            query = QueryResponse(
                id=query_id,
                sql=sql_query,
                is_valid=sql_validation.is_valid and crew_output.validation.is_valid,
                validation_errors=(sql_validation.security_warnings or [])
                + (crew_output.validation.blocked_commands or []),
            )

            # Phase 4: READY
            await self.send_status(
                status=InterpretationStatus.READY.value,
                message="Interpretação concluída com sucesso",
            )

            await self.send_query(query)

            log.info(
                "WebSocket interpretation completed",
                status=status.value,
                confidence=crew_output.interpretation.confidence,
            )

        except TimeoutError:
            log.error("LLM timeout during interpretation")
            await self.send_error(
                code="LLM_TIMEOUT",
                message="O serviço de interpretação demorou mais que o esperado. Tente novamente.",
                suggestions=[
                    "Simplifique seu prompt",
                    "Divida em buscas menores",
                ],
            )

        except Exception as e:
            log.error("Error during interpretation", error=str(e))
            await self.send_error(
                code="INTERPRETATION_ERROR",
                message=f"Erro na interpretação: {str(e)}",
                suggestions=[
                    "Tente reformular o prompt",
                    "Verifique se os termos usados existem no catálogo",
                ],
            )

    def _extract_entities(
        self, crew_output: InterpreterCrewOutput
    ) -> list[EntityResponse]:
        """Extract entity responses from crew output."""
        entities: list[EntityResponse] = []

        for table in crew_output.interpretation.target_tables:
            # Parse table name (format: db_name.table_name)
            parts = table.split(".", 1)
            if len(parts) == 2:
                _, table_name = parts
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
        """Extract filter responses from crew output."""
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


@router.websocket("/ws/query/interpret")
async def websocket_interpret(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time query interpretation.

    This endpoint provides streaming feedback during the interpretation process:
    - Status updates (interpreting, validating, refining, ready)
    - Chunk messages with partial content from each agent
    - Final interpretation with summary and entities/filters
    - Generated query ready for execution

    Connection Flow:
    1. Connect to the WebSocket
    2. Send a JSON message with type="interpret" and prompt="your prompt"
    3. Receive streaming updates until final result or error

    Example message to send:
    {
        "type": "interpret",
        "prompt": "usuários com cartão de crédito ativo",
        "session_context": null  // Optional: include previous context
    }
    """
    session_id = str(uuid4())
    connection_manager = get_connection_manager()

    await connection_manager.connect(session_id, websocket)
    log = logger.bind(session_id=session_id)
    log.info("WebSocket client connected")

    try:
        handler = WebSocketInterpreterHandler(session_id, websocket)

        while True:
            # Receive message
            raw_message = await websocket.receive_text()

            try:
                data = json.loads(raw_message)
                request = WSInterpretRequest(**data)

                if request.type == "interpret":
                    await handler.process_interpret_request(request.prompt)
                else:
                    await handler.send_error(
                        code="UNKNOWN_MESSAGE_TYPE",
                        message=f"Tipo de mensagem desconhecido: {request.type}",
                        suggestions=["Use type='interpret' para interpretar um prompt"],
                    )

            except json.JSONDecodeError:
                await handler.send_error(
                    code="INVALID_JSON",
                    message="Mensagem JSON inválida",
                    suggestions=["Envie um objeto JSON válido com type e prompt"],
                )

            except ValidationError as e:
                await handler.send_error(
                    code="VALIDATION_ERROR",
                    message="Erro de validação da mensagem",
                    details={"errors": e.errors()},
                    suggestions=["Verifique o formato da mensagem"],
                )

    except WebSocketDisconnect:
        log.info("WebSocket client disconnected")

    finally:
        await connection_manager.disconnect(session_id)


# Export router
__all__ = ["router"]
