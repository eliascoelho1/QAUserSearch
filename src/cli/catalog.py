"""CLI commands for catalog schema extraction.

This CLI extracts schema metadata from external MongoDB sources and writes
directly to YAML files in the catalog directory. No PostgreSQL connection
is required for catalog operations.
"""

import asyncio
import sys
from typing import Annotated

import structlog
import typer

from src.config import get_settings
from src.services.catalog_yaml_extractor import CatalogYamlExtractor

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
    no_merge: Annotated[
        bool, typer.Option(help="Don't merge manual fields from existing file")
    ] = False,
) -> None:
    """Extract schema from a single external source and save to YAML."""
    asyncio.run(_extract_single(db_name, table_name, sample_size, merge=not no_merge))


@app.command()
def extract_all(
    sample_size: Annotated[int, typer.Option(help="Documents to sample")] = 500,
    no_merge: Annotated[
        bool, typer.Option(help="Don't merge manual fields from existing files")
    ] = False,
) -> None:
    """Extract schemas from all known sources and save to YAML files."""
    asyncio.run(_extract_all(sample_size, merge=not no_merge))


@app.command()
def list_known() -> None:
    """List all known sources available for extraction."""
    typer.echo("Known sources:")
    for db_name, table_name in KNOWN_SOURCES:
        typer.echo(f"  - {db_name}.{table_name}")


async def _extract_single(
    db_name: str,
    table_name: str,
    sample_size: int,
    *,
    merge: bool = True,
) -> None:
    """Internal async implementation for single extraction.

    Args:
        db_name: External database name.
        table_name: External table/collection name.
        sample_size: Number of documents to sample.
        merge: Whether to preserve manual fields from existing YAML file.
    """
    settings = get_settings()
    log = logger.bind(db_name=db_name, table_name=table_name, sample_size=sample_size)

    log.info("Starting YAML extraction")
    typer.echo(f"Extracting schema from {db_name}.{table_name}...")

    try:
        extractor = CatalogYamlExtractor(
            catalog_path=settings.catalog_path,
            sample_size=sample_size,
            cardinality_limit=settings.enumerable_cardinality_limit,
        )

        result = await extractor.extract_to_yaml(
            db_name=db_name,
            table_name=table_name,
            sample_size=sample_size,
            merge_manual_fields=merge,
        )

        typer.echo("Extraction completed successfully:")
        typer.echo(f"  - Source ID: {result['source_id']}")
        typer.echo(f"  - Columns extracted: {result['columns_extracted']}")
        typer.echo(f"  - Enumerable columns: {result['enumerable_columns']}")
        typer.echo(f"  - File: {result['file_path']}")

    except Exception as e:
        log.error("Extraction failed", error=str(e))
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _extract_all(sample_size: int, *, merge: bool = True) -> None:
    """Internal async implementation for batch extraction.

    Args:
        sample_size: Number of documents to sample per source.
        merge: Whether to preserve manual fields from existing YAML files.
    """
    settings = get_settings()
    log = logger.bind(sample_size=sample_size)

    log.info("Starting batch YAML extraction")
    total_sources = len(KNOWN_SOURCES)
    typer.echo(f"Extracting schemas from {total_sources} known sources...")
    typer.echo(f"Output directory: {settings.catalog_path}")
    typer.echo("")

    success_count = 0
    error_count = 0

    extractor = CatalogYamlExtractor(
        catalog_path=settings.catalog_path,
        sample_size=sample_size,
        cardinality_limit=settings.enumerable_cardinality_limit,
    )

    for idx, (db_name, table_name) in enumerate(KNOWN_SOURCES, start=1):
        progress = f"[{idx}/{total_sources}]"
        typer.echo(f"{progress} Extracting {db_name}.{table_name}...")

        try:
            result = await extractor.extract_to_yaml(
                db_name=db_name,
                table_name=table_name,
                sample_size=sample_size,
                merge_manual_fields=merge,
            )
            typer.echo(f"  - Columns: {result['columns_extracted']}")
            typer.echo(f"  - Enumerable: {result['enumerable_columns']}")
            typer.echo(f"  - File: {result['file_path']}")
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

    typer.echo("")
    typer.echo("Batch extraction completed:")
    typer.echo(f"  - Successful: {success_count}")
    typer.echo(f"  - Failed: {error_count}")

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    app()
