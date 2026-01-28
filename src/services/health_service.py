"""Health check service."""

from datetime import UTC, datetime

from src.config import get_settings
from src.core.database import get_db_manager
from src.core.logging import get_logger
from src.main import get_uptime_seconds
from src.schemas.enums import CheckStatus, HealthStatus
from src.schemas.health import DependencyCheck, HealthCheckResponse

logger = get_logger(__name__)


async def check_database() -> DependencyCheck:
    """Check database connectivity.

    Returns:
        DependencyCheck result for the database.
    """
    try:
        db = get_db_manager()
        is_healthy, latency_ms, error = await db.check_connection()

        if is_healthy:
            return DependencyCheck(
                name="database",
                status=CheckStatus.OK,
                latency_ms=latency_ms,
            )
        else:
            return DependencyCheck(
                name="database",
                status=CheckStatus.ERROR,
                message=error,
            )
    except RuntimeError:
        # Database not initialized
        return DependencyCheck(
            name="database",
            status=CheckStatus.ERROR,
            message="Database not initialized",
        )
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return DependencyCheck(
            name="database",
            status=CheckStatus.ERROR,
            message=str(e),
        )


def determine_health_status(checks: list[DependencyCheck]) -> HealthStatus:
    """Determine overall health status from individual checks.

    Args:
        checks: List of dependency check results.

    Returns:
        Overall health status.
    """
    has_error = any(c.status == CheckStatus.ERROR for c in checks)
    has_warning = any(c.status == CheckStatus.WARNING for c in checks)

    if has_error:
        return HealthStatus.UNHEALTHY
    elif has_warning:
        return HealthStatus.DEGRADED
    else:
        return HealthStatus.HEALTHY


async def get_health_check() -> HealthCheckResponse:
    """Perform full health check.

    Returns:
        Complete health check response.
    """
    settings = get_settings()

    # Run all dependency checks
    checks = [await check_database()]

    # Log health check
    status = determine_health_status(checks)
    logger.info(
        "Health check performed",
        status=status.value,
        checks_count=len(checks),
    )

    return HealthCheckResponse(
        status=status,
        timestamp=datetime.now(UTC),
        version=settings.version,
        uptime_seconds=get_uptime_seconds(),
        checks=checks,
    )


async def is_ready() -> tuple[bool, str | None]:
    """Check if application is ready to serve traffic.

    Returns:
        Tuple of (is_ready, reason_if_not_ready).
    """
    health = await get_health_check()

    if health.status == HealthStatus.UNHEALTHY:
        failed_checks = [c.name for c in health.checks if c.status == CheckStatus.ERROR]
        return False, f"Failed checks: {', '.join(failed_checks)}"

    return True, None
