"""Catalog repository dependency factory."""

from functools import lru_cache

from src.config import get_settings
from src.repositories.catalog.file_repository import CatalogFileRepository


@lru_cache
def get_catalog_repository() -> CatalogFileRepository:
    """Get the catalog file repository instance.

    Returns a cached instance of CatalogFileRepository configured
    with settings from the application configuration.

    Returns:
        CatalogFileRepository instance.
    """
    settings = get_settings()
    return CatalogFileRepository(
        catalog_path=settings.catalog_path,
        cache_ttl_seconds=float(settings.catalog_cache_ttl_seconds),
    )
