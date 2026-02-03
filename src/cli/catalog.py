"""CLI commands for catalog schema extraction."""

import asyncio
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

import structlog
import typer
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.database import DatabaseManager
from src.services.catalog_service import CatalogService

logger = structlog.get_logger(__name__)

app = typer.Typer(
    name="qa-catalog",
    help="Catalog schema extraction CLI",
    no_args_is_help=True,
)

# Lista de fontes conhecidas (mesma da API atual)
KNOWN_SOURCES = [
    ("card_account_authorization", "account_main"),
    ("card_account_authorization", "card_main"),
    ("credit", "invoice"),
    ("credit", "closed_invoice"),
]


@app.command()
def extract(
    db_name: Annotated[str, typer.Argument(help="Database name")],
    table_name: Annotated[str, typer.Argument(help="Table/collection name")],
    sample_size: Annotated[int, typer.Option(help="Documents to sample")] = 500,
) -> None:
    """Extract schema from a single external source."""
    asyncio.run(_extract_single(db_name, table_name, sample_size))


@app.command()
def extract_all(
    sample_size: Annotated[int, typer.Option(help="Documents to sample")] = 500,
) -> None:
    """Extract schemas from all known sources."""
    asyncio.run(_extract_all(sample_size))


@app.command()
def list_known() -> None:
    """List all known sources available for extraction."""
    typer.echo("Known sources:")
    for db_name, table_name in KNOWN_SOURCES:
        typer.echo(f"  - {db_name}.{table_name}")


@asynccontextmanager
async def _get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for CLI commands.

    Yields:
        An async database session.
    """
    settings = get_settings()
    db_manager = DatabaseManager(
        database_url=settings.database_url,
        echo=settings.debug,
    )
    try:
        async with db_manager.session() as session:
            yield session
    finally:
        await db_manager.close()


async def _extract_single(db_name: str, table_name: str, sample_size: int) -> None:
    """Internal async implementation for single extraction."""
    settings = get_settings()
    log = logger.bind(db_name=db_name, table_name=table_name, sample_size=sample_size)

    log.info("Starting extraction")
    typer.echo(f"Extracting schema from {db_name}.{table_name}...")

    try:
        async with _get_db_session() as session:
            service = CatalogService(
                session=session,
                sample_size=sample_size,
                cardinality_limit=settings.enumerable_cardinality_limit,
            )
            result = await service.extract_and_persist(
                db_name=db_name,
                table_name=table_name,
                sample_size=sample_size,
            )

        typer.echo("Extraction completed successfully:")
        typer.echo(f"  - Source ID: {result['source_id']}")
        typer.echo(f"  - Columns extracted: {result['columns_extracted']}")
        typer.echo(f"  - Enumerable columns: {result['enumerable_columns']}")

    except Exception as e:
        log.error("Extraction failed", error=str(e))
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _extract_all(sample_size: int) -> None:
    """Internal async implementation for batch extraction."""
    settings = get_settings()
    log = logger.bind(sample_size=sample_size)

    log.info("Starting batch extraction")
    typer.echo(f"Extracting schemas from {len(KNOWN_SOURCES)} known sources...")

    success_count = 0
    error_count = 0

    try:
        async with _get_db_session() as session:
            service = CatalogService(
                session=session,
                sample_size=sample_size,
                cardinality_limit=settings.enumerable_cardinality_limit,
            )

            for db_name, table_name in KNOWN_SOURCES:
                typer.echo(f"\nExtracting {db_name}.{table_name}...")

                try:
                    result = await service.extract_and_persist(
                        db_name=db_name,
                        table_name=table_name,
                        sample_size=sample_size,
                    )
                    typer.echo(f"  - Source ID: {result['source_id']}")
                    typer.echo(f"  - Columns: {result['columns_extracted']}")
                    success_count += 1

                except Exception as e:
                    log.error(
                        "Extraction failed",
                        db_name=db_name,
                        table_name=table_name,
                        error=str(e),
                    )
                    typer.echo(f"  - Error: {e}", err=True)
                    error_count += 1

        typer.echo("\nBatch extraction completed:")
        typer.echo(f"  - Successful: {success_count}")
        typer.echo(f"  - Failed: {error_count}")

        if error_count > 0:
            sys.exit(1)

    except Exception as e:
        log.error("Batch extraction failed", error=str(e))
        typer.echo(f"Fatal error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    app()
