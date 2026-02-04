"""CLI commands for catalog schema extraction.

This CLI extracts schema metadata from external MongoDB sources and writes
directly to YAML files in the catalog directory. No PostgreSQL connection
is required for catalog operations.
"""

import asyncio
import sys
from pathlib import Path
from typing import Annotated

import structlog
import typer

from src.config import get_settings
from src.services.catalog_validator import CatalogValidator
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


@app.command()
def validate(
    path: Annotated[
        Path | None,
        typer.Argument(help="Path to specific YAML file to validate (optional)"),
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show detailed validation output")
    ] = False,
) -> None:
    """Validate catalog YAML files against the JSON Schema.

    If no path is provided, validates all YAML files in the catalog/sources directory.
    If a path is provided, validates only that specific file.

    Examples:
        qa-catalog validate                           # Validate all files
        qa-catalog validate catalog/sources/credit/invoice.yaml  # Validate single file
        qa-catalog validate -v                        # Verbose output
    """
    settings = get_settings()

    try:
        validator = CatalogValidator(catalog_path=settings.catalog_path)
    except FileNotFoundError as e:
        typer.echo(f"Erro: {e}", err=True)
        sys.exit(1)

    if path is not None:
        # Validate single file
        _validate_single_file(validator, path, verbose)
    else:
        # Validate all files
        _validate_all_files(validator, verbose)


def _validate_single_file(
    validator: CatalogValidator, path: Path, verbose: bool
) -> None:
    """Validate a single YAML file.

    Args:
        validator: The CatalogValidator instance.
        path: Path to the YAML file.
        verbose: Whether to show detailed output.
    """
    log = logger.bind(file=str(path))

    if verbose:
        typer.echo(f"Validando arquivo: {path}")

    try:
        errors = validator.validate_file(path)
    except FileNotFoundError:
        typer.echo(f"Erro: Arquivo não encontrado: {path}", err=True)
        sys.exit(1)
    except Exception as e:
        log.error("Validation error", error=str(e))
        typer.echo(f"Erro ao validar arquivo: {e}", err=True)
        sys.exit(1)

    if not errors:
        typer.echo(f"✓ {path}: válido")
        sys.exit(0)

    typer.echo(f"✗ {path}: {len(errors)} erro(s) encontrado(s)", err=True)
    for error in errors:
        if verbose:
            typer.echo(f"  - Campo: {error.field}", err=True)
            typer.echo(f"    Mensagem: {error.message}", err=True)
        else:
            typer.echo(f"  - {error.field}: {error.message}", err=True)

    sys.exit(1)


def _validate_all_files(validator: CatalogValidator, verbose: bool) -> None:
    """Validate all YAML files in the catalog.

    Args:
        validator: The CatalogValidator instance.
        verbose: Whether to show detailed output.
    """
    settings = get_settings()

    if verbose:
        typer.echo(f"Validando todos os arquivos em: {settings.catalog_path}/sources")

    errors = validator.validate_all()

    if not errors:
        typer.echo("✓ Todos os arquivos de catálogo são válidos")
        sys.exit(0)

    # Group errors by file
    errors_by_file: dict[Path, list[str]] = {}
    for error in errors:
        file_path = error.file_path or Path("unknown")
        if file_path not in errors_by_file:
            errors_by_file[file_path] = []
        errors_by_file[file_path].append(f"{error.field}: {error.message}")

    typer.echo(
        f"✗ Validação falhou: {len(errors)} erro(s) em {len(errors_by_file)} arquivo(s)",
        err=True,
    )
    typer.echo("", err=True)

    for file_path, file_errors in errors_by_file.items():
        typer.echo(f"Arquivo: {file_path}", err=True)
        for err_msg in file_errors:
            if verbose:
                typer.echo(f"  - {err_msg}", err=True)
            else:
                # Truncate long messages in non-verbose mode
                if len(err_msg) > 80:
                    err_msg = err_msg[:77] + "..."
                typer.echo(f"  - {err_msg}", err=True)
        typer.echo("", err=True)

    sys.exit(1)


if __name__ == "__main__":
    app()
