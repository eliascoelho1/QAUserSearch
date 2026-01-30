"""Enums used across the application."""

from enum import Enum


class HealthStatus(str, Enum):
    """Overall application health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class CheckStatus(str, Enum):
    """Individual dependency check status."""

    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


class Environment(str, Enum):
    """Application runtime environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging level options."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DataSourceEnvironment(str, Enum):
    """External data source environment."""

    MOCK = "MOCK"  # Local JSON files in res/db/
    PROD = "PROD"  # Direct MongoDB connection


class EnrichmentStatus(str, Enum):
    """LLM enrichment status for column descriptions."""

    NOT_ENRICHED = "not_enriched"  # Default: never processed
    PENDING_ENRICHMENT = "pending_enrichment"  # Failed/timeout, awaiting retry
    ENRICHED = "enriched"  # Description generated successfully


class InferredType(str, Enum):
    """Inferred data types from JSON documents."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"  # Float
    BOOLEAN = "boolean"
    DATETIME = "datetime"  # ISO 8601 strings
    OBJECTID = "objectid"  # MongoDB ObjectId (24 hex chars)
    ARRAY = "array"
    OBJECT = "object"  # Nested object
    NULL = "null"  # Only null values found
    UNKNOWN = "unknown"  # Type not determined
