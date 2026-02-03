"""Interpreter API endpoints for LLM query generation."""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_manager
from src.schemas.interpreter import (
    ErrorResponse,
    ExecuteQueryRequest,
    InterpretationStatus,
    InterpretationWithQueryResponse,
    InterpretPromptRequest,
    QueryResponse,
    QueryResultResponse,
)
from src.services.interpreter.query_executor import QueryExecutionError, QueryExecutor
from src.services.interpreter.service import (
    InterpretationException,
    InterpreterService,
)

router = APIRouter(prefix="/query", tags=["query-interpreter"])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    db_manager = get_db_manager()
    async with db_manager.session() as session:
        yield session


async def get_interpreter_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InterpreterService:
    """Get interpreter service instance."""
    return InterpreterService(session)


async def get_query_executor(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> QueryExecutor:
    """Get query executor instance."""
    return QueryExecutor(session)


@router.post(
    "/interpret",
    response_model=InterpretationWithQueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid prompt or blocked query"},
        422: {"description": "Validation error"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"},
    },
)
async def interpret_prompt(
    request: InterpretPromptRequest,
    service: Annotated[InterpreterService, Depends(get_interpreter_service)],
) -> InterpretationWithQueryResponse:
    """Interpret a natural language prompt and generate a SQL query.

    This endpoint receives a prompt in natural language describing the
    type of test data needed and returns a structured interpretation
    along with the generated SQL query.

    Example prompts:
    - "usuários com cartão de crédito ativo"
    - "faturas vencidas há mais de 30 dias"
    - "contas bloqueadas por fraude"
    """
    try:
        result = await service.interpret_prompt(request.prompt)

        # Check if the query was blocked (return 200 but with blocked status)
        if result.status == InterpretationStatus.BLOCKED:
            # Return the result with blocked status - the client can handle this
            # The query validation_errors will contain the blocked commands
            return result

        return result

    except InterpretationException as e:
        # Map error codes to appropriate HTTP status codes
        status_code_map = {
            "INVALID_PROMPT": 400,
            "PROMPT_TOO_LONG": 400,
            "UNRECOGNIZED_TABLES": 400,
            "UNRECOGNIZED_COLUMNS": 400,
            "AMBIGUOUS_PROMPT": 400,
            "LLM_TIMEOUT": 503,
            "INTERPRETATION_ERROR": 500,
        }
        status_code = status_code_map.get(e.error.code, 500)

        raise HTTPException(
            status_code=status_code,
            detail={
                "code": e.error.code,
                "message": e.error.message,
                "details": e.error.details,
                "suggestions": e.error.suggestions or [],
            },
        ) from e

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_PROMPT",
                "message": str(e),
                "suggestions": [
                    "Verifique se o prompt não está vazio",
                    "O prompt deve ter no máximo 2000 caracteres",
                    "Use termos relacionados aos dados disponíveis no catálogo",
                ],
            },
        ) from e

    except TimeoutError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "LLM_TIMEOUT",
                "message": "O serviço de interpretação demorou mais que o esperado. Tente novamente.",
                "suggestions": [
                    "Simplifique seu prompt",
                    "Divida em buscas menores",
                    "Tente novamente em alguns segundos",
                ],
            },
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERPRETATION_ERROR",
                "message": f"Erro na interpretação: {str(e)}",
                "suggestions": [
                    "Tente reformular o prompt",
                    "Verifique se os termos usados existem no catálogo",
                ],
            },
        ) from e


@router.post(
    "/{query_id}/execute",
    response_model=QueryResultResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Query invalid or blocked"},
        404: {"model": ErrorResponse, "description": "Query not found"},
    },
)
async def execute_query(
    query_id: UUID,
    service: Annotated[InterpreterService, Depends(get_interpreter_service)],
    executor: Annotated[QueryExecutor, Depends(get_query_executor)],
    request: ExecuteQueryRequest | None = None,
) -> QueryResultResponse:
    """Execute a previously generated query.

    Returns the query results with a configurable limit (default 100, max 1000).
    If results exceed the limit, is_partial will be True.
    """
    # Get the stored query
    stored_query = await service.get_query(query_id)

    if stored_query is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "QUERY_NOT_FOUND",
                "message": f"Query {query_id} não encontrada",
                "suggestions": [
                    "Verifique se o ID da query está correto",
                    "Use POST /query/interpret para gerar uma nova query",
                ],
            },
        )

    if not stored_query.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "QUERY_BLOCKED",
                "message": "Esta query foi bloqueada por questões de segurança",
                "details": {
                    "validation_errors": stored_query.validation_errors,
                    "blocked_commands": [
                        cmd
                        for cmd in stored_query.validation_errors
                        if any(
                            dangerous in cmd.upper()
                            for dangerous in [
                                "DELETE",
                                "DROP",
                                "UPDATE",
                                "INSERT",
                                "TRUNCATE",
                                "ALTER",
                            ]
                        )
                    ],
                },
                "suggestions": [
                    "Reformule seu pedido para buscar dados em vez de modificá-los",
                    "Use apenas consultas de leitura (SELECT)",
                    "Não é permitido modificar, deletar ou alterar dados",
                ],
            },
        )

    try:
        limit = request.limit if request else None
        result = await executor.execute_query(stored_query, limit)
        return result

    except QueryExecutionError as e:
        # Map error codes to appropriate HTTP status codes
        status_code_map = {
            "INVALID_QUERY": 400,
            "SQL_COMMAND_BLOCKED": 400,
            "EXECUTION_ERROR": 500,
            "CONNECTION_ERROR": 503,
        }
        status_code = status_code_map.get(e.code, 500)

        raise HTTPException(
            status_code=status_code,
            detail={
                "code": e.code,
                "message": e.message,
                "details": e.details,
                "suggestions": e.suggestions or [],
            },
        ) from e

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "EXECUTION_ERROR",
                "message": str(e),
            },
        ) from e

    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "EXECUTION_FAILED",
                "message": str(e),
                "suggestions": [
                    "Verifique a conectividade com o banco de dados",
                    "Tente novamente em alguns segundos",
                ],
            },
        ) from e


@router.get(
    "/{query_id}",
    response_model=QueryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Query not found"},
    },
)
async def get_query(
    query_id: UUID,
    service: Annotated[InterpreterService, Depends(get_interpreter_service)],
) -> QueryResponse:
    """Get details of a previously generated query.

    Returns the SQL query, validation status, and any validation errors.
    """
    stored_query = await service.get_query(query_id)

    if stored_query is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "QUERY_NOT_FOUND",
                "message": f"Query {query_id} não encontrada",
                "suggestions": [
                    "Verifique se o ID da query está correto",
                    "Use POST /query/interpret para gerar uma nova query",
                ],
            },
        )

    return QueryResponse(
        id=stored_query.id,
        sql=stored_query.sql,
        is_valid=stored_query.is_valid,
        validation_errors=stored_query.validation_errors,
    )
