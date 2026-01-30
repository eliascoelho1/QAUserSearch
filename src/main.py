"""FastAPI application entry point."""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import get_settings
from src.core.database import close_db_manager, init_db_manager
from src.core.logging import get_logger, setup_logging

# Application start time for uptime calculation
_start_time: float = 0.0


def get_uptime_seconds() -> int:
    """Get application uptime in seconds."""
    return int(time.time() - _start_time)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    global _start_time
    settings = get_settings()

    # Startup
    setup_logging(log_level=settings.log_level, environment=settings.environment)
    logger = get_logger(__name__)
    logger.info(
        "Starting application",
        app_name=settings.app_name,
        version=settings.version,
        environment=settings.environment.value,
    )

    # Initialize database
    init_db_manager(
        database_url=settings.database_url,
        echo=settings.debug,
    )

    _start_time = time.time()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_db_manager()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="QAUserSearch API",
        description="API para busca de massas de usuários em ambiente de QA",
        version=settings.version,
        docs_url="/",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Register routers
    from src.api.v1.catalog import router as catalog_router
    from src.api.v1.health import router as health_router
    from src.api.v1.root import router as root_router

    app.include_router(root_router)
    app.include_router(health_router)
    app.include_router(catalog_router, prefix="/api/v1")

    return app


# Create the application instance
app = create_app()
