"""Database connection and session management using SQLAlchemy async."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """Initialize the database manager.

        Args:
            database_url: The database connection URL.
            echo: Whether to log SQL statements.
        """
        self._engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session.

        Yields:
            An async database session.
        """
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def check_connection(self) -> tuple[bool, int | None, str | None]:
        """Check if the database connection is healthy.

        Returns:
            A tuple of (is_healthy, latency_ms, error_message).
        """
        import time

        start = time.perf_counter()
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            latency_ms = int((time.perf_counter() - start) * 1000)
            return True, latency_ms, None
        except Exception as e:
            logger.error("Database connection check failed", error=str(e))
            return False, None, str(e)

    async def close(self) -> None:
        """Close the database connection pool."""
        await self._engine.dispose()
        logger.info("Database connection pool closed")


# Import text here to avoid circular imports
from sqlalchemy import text  # noqa: E402

# Global database manager instance (initialized in app lifespan)
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance.

    Returns:
        The database manager.

    Raises:
        RuntimeError: If the database manager is not initialized.
    """
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return _db_manager


def init_db_manager(database_url: str, echo: bool = False) -> DatabaseManager:
    """Initialize the global database manager.

    Args:
        database_url: The database connection URL.
        echo: Whether to log SQL statements.

    Returns:
        The initialized database manager.
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url, echo=echo)
    logger.info("Database manager initialized")
    return _db_manager


async def close_db_manager() -> None:
    """Close the global database manager."""
    global _db_manager
    if _db_manager is not None:
        await _db_manager.close()
        _db_manager = None
