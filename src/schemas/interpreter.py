"""Pydantic schemas for LLM Query Interpreter.

This module contains:
- Core models used as CrewAI response_format/output_pydantic
- Request/Response models for REST API
- Enums for filter operators and interpretation status
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================


class FilterOperator(str, Enum):
    """SQL filter operators supported by the interpreter."""

    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    LIKE = "LIKE"
    IN = "IN"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


class InterpretationStatus(str, Enum):
    """Status of the interpretation process."""

    PENDING = "pending"
    INTERPRETING = "interpreting"
    VALIDATING = "validating"
    REFINING = "refining"
    READY = "ready"
    BLOCKED = "blocked"
    ERROR = "error"


# =============================================================================
# CrewAI Structured Output Models (response_format / output_pydantic)
# =============================================================================


class QueryFilter(BaseModel):
    """Individual filter extracted from the prompt.

    Used in InterpretedQuery as structured output from the Interpreter agent.
    """

    column: str = Field(..., description="Nome da coluna no banco de dados")
    operator: str = Field(
        ..., description="Operador SQL: =, !=, >, <, >=, <=, LIKE, IN, BETWEEN"
    )
    value: str | int | float | list[Any] | None = Field(
        ..., description="Valor do filtro"
    )
    is_temporal: bool = Field(
        default=False,
        description="Se é uma condição temporal (ex: últimos 30 dias)",
    )


class InterpretedQuery(BaseModel):
    """Structured output from the Interpreter Agent.

    Used as response_format in the CrewAI LLM class to ensure
    typed and validated outputs.
    """

    target_tables: list[str] = Field(
        ...,
        min_length=1,
        description="Tabelas identificadas no formato db_name.table_name",
    )
    filters: list[QueryFilter] = Field(
        default_factory=list[QueryFilter],
        description="Filtros extraídos do prompt",
    )
    select_columns: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Colunas a selecionar (default: todas)",
    )
    joins: list[dict[str, Any]] | None = Field(
        default=None,
        description="JOINs necessários entre tabelas",
    )
    natural_explanation: str = Field(
        ...,
        description="Explicação em linguagem natural da interpretação",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confiança da interpretação (0.0 a 1.0)",
    )
    ambiguities: list[str] = Field(
        default_factory=list,
        description="Ambiguidades detectadas no prompt",
    )


class ValidationResult(BaseModel):
    """Structured output from the Validator Agent.

    Used as output_pydantic in the validation Task.
    """

    is_valid: bool = Field(..., description="Se a query é segura para execução")
    blocked_commands: list[str] = Field(
        default_factory=list,
        description="Comandos SQL bloqueados encontrados",
    )
    security_warnings: list[str] = Field(
        default_factory=list,
        description="Avisos de segurança (não bloqueantes)",
    )
    catalog_validation: dict[str, Any] = Field(
        default_factory=dict,
        description="Validação contra o catálogo: tabelas e colunas existentes",
    )


class RefinedQuery(BaseModel):
    """Structured output from the Refiner Agent.

    Used as output_pydantic in the refinement Task.
    """

    sql_query: str = Field(..., description="Query SQL final otimizada")
    explanation: str = Field(..., description="Explicação das otimizações aplicadas")
    applied_optimizations: list[str] = Field(
        default_factory=list,
        description="Lista de otimizações aplicadas",
    )
    estimated_rows: int | None = Field(
        default=None,
        description="Estimativa de linhas retornadas",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Avisos sobre a query (ex: resultado parcial)",
    )
    suggested_limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Limite sugerido de resultados",
    )


class InterpreterCrewOutput(BaseModel):
    """Final output from the Interpreter Crew.

    Combines outputs from all 3 agents.
    """

    interpretation: InterpretedQuery
    validation: ValidationResult
    refined_query: RefinedQuery
    status: str = Field(..., description="Status final: ready, blocked, error")


# =============================================================================
# API Request Models
# =============================================================================


class InterpretPromptRequest(BaseModel):
    """Request body for POST /api/v1/query/interpret."""

    prompt: str = Field(
        ...,
        max_length=2000,
        description="Prompt em linguagem natural descrevendo os dados desejados",
    )


class ExecuteQueryRequest(BaseModel):
    """Request body for POST /api/v1/query/{query_id}/execute."""

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Número máximo de registros a retornar",
    )


# =============================================================================
# API Response Models
# =============================================================================


class EntityResponse(BaseModel):
    """Entity identified in the prompt."""

    name: str = Field(..., description="Nome da entidade identificada")
    table_name: str = Field(..., description="Tabela correspondente no banco")
    alias: str | None = Field(default=None, description="Alias usado na query")


class FilterResponse(BaseModel):
    """Filter extracted from the prompt."""

    field: str = Field(..., description="Campo do filtro")
    operator: FilterOperator = Field(..., description="Operador do filtro")
    value: Any = Field(..., description="Valor do filtro")
    is_temporal: bool = Field(default=False, description="Se é condição temporal")


class InterpretationResponse(BaseModel):
    """Response from prompt interpretation."""

    id: UUID = Field(default_factory=uuid4, description="ID da interpretação")
    status: InterpretationStatus = Field(..., description="Status da interpretação")
    summary: str = Field(
        ..., description="Resumo da interpretação em linguagem natural"
    )
    entities: list[EntityResponse] = Field(
        default_factory=list[EntityResponse], description="Entidades identificadas"
    )
    filters: list[FilterResponse] = Field(
        default_factory=list[FilterResponse], description="Filtros extraídos"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança (0-1)")


class QueryResponse(BaseModel):
    """Generated query details."""

    id: UUID = Field(default_factory=uuid4, description="ID da query")
    sql: str = Field(..., description="Query SQL gerada")
    is_valid: bool = Field(..., description="Se passou na validação de segurança")
    validation_errors: list[str] = Field(
        default_factory=list, description="Erros de validação"
    )


class InterpretationWithQueryResponse(InterpretationResponse):
    """Response with interpretation and generated query."""

    query: QueryResponse = Field(..., description="Query gerada")


class QueryResultResponse(BaseModel):
    """Response from query execution."""

    query_id: UUID = Field(..., description="ID da query executada")
    rows: list[dict[str, Any]] = Field(..., description="Dados retornados")
    row_count: int = Field(..., ge=0, description="Quantidade de registros")
    is_partial: bool = Field(
        default=False, description="Se resultado foi truncado (>100 registros)"
    )
    execution_time_ms: int = Field(..., ge=0, description="Tempo de execução em ms")


class ErrorResponse(BaseModel):
    """Error response with code and suggestions."""

    code: str = Field(..., description="Código do erro")
    message: str = Field(..., description="Mensagem de erro em português")
    details: dict[str, Any] | None = Field(
        default=None, description="Detalhes adicionais"
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Sugestões de como corrigir o problema",
    )


# =============================================================================
# Internal Storage Models
# =============================================================================


def _utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(UTC)


class StoredInterpretation(BaseModel):
    """Internal model for storing interpretations in memory/cache."""

    id: UUID = Field(default_factory=uuid4)
    original_prompt: str
    interpretation: InterpretedQuery
    validation: ValidationResult
    refined_query: RefinedQuery | None = None
    status: InterpretationStatus = InterpretationStatus.PENDING
    created_at: datetime = Field(default_factory=_utc_now)


class StoredQuery(BaseModel):
    """Internal model for storing generated queries."""

    id: UUID = Field(default_factory=uuid4)
    interpretation_id: UUID
    sql: str
    is_valid: bool
    validation_errors: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
    execution_limit: int = 100
