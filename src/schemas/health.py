"""Health check schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.enums import CheckStatus, HealthStatus


class DependencyCheck(BaseModel):
    """Individual dependency check result."""

    name: str = Field(description="Name of the dependency")
    status: CheckStatus = Field(description="Check status")
    latency_ms: int | None = Field(default=None, description="Latency in milliseconds")
    message: str | None = Field(default=None, description="Additional message")


class HealthCheckResponse(BaseModel):
    """Full health check response."""

    status: HealthStatus = Field(description="Overall health status")
    timestamp: datetime = Field(description="Timestamp of the check")
    version: str = Field(description="Application version")
    uptime_seconds: int = Field(description="Seconds since application start")
    checks: list[DependencyCheck] = Field(description="Individual dependency checks")


class LivenessResponse(BaseModel):
    """Liveness probe response."""

    alive: bool = Field(description="Whether the application is alive")


class ReadinessResponse(BaseModel):
    """Readiness probe response."""

    ready: bool = Field(description="Whether the application is ready")
    reason: str | None = Field(default=None, description="Reason if not ready")
