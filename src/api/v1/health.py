"""Health check endpoints."""

from fastapi import APIRouter, Response, status

from src.core.logging import get_logger
from src.schemas.enums import HealthStatus
from src.schemas.health import (
    HealthCheckResponse,
    LivenessResponse,
    ReadinessResponse,
)
from src.services.health_service import get_health_check, is_ready

router = APIRouter(prefix="/health", tags=["Health"])
logger = get_logger(__name__)


@router.get(
    "",
    response_model=HealthCheckResponse,
    responses={
        200: {"description": "Application is healthy"},
        503: {"description": "Application has issues"},
    },
)
async def health_check(response: Response) -> HealthCheckResponse:
    """Get full health check status.

    Returns status of the application and all its dependencies.
    """
    logger.debug("Health check requested")
    health = await get_health_check()

    if health.status == HealthStatus.UNHEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return health


@router.get("/live", response_model=LivenessResponse)
async def liveness() -> LivenessResponse:
    """Liveness probe endpoint.

    Returns 200 if the application process is running.
    Used by Kubernetes/container orchestration for process health.
    """
    logger.debug("Liveness probe requested")
    return LivenessResponse(alive=True)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={
        200: {"description": "Application is ready"},
        503: {"description": "Application is not ready"},
    },
)
async def readiness(response: Response) -> ReadinessResponse:
    """Readiness probe endpoint.

    Returns 200 if the application is ready to receive traffic.
    Used by Kubernetes/load balancers to determine if traffic should be routed.
    """
    logger.debug("Readiness probe requested")
    ready, reason = await is_ready()

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(ready=ready, reason=reason)
