"""External data source repositories."""

from src.config import get_settings
from src.repositories.external.base import ExternalDataSource
from src.schemas.enums import DataSourceEnvironment


def get_external_data_source() -> ExternalDataSource:
    """Factory function to get the appropriate external data source.

    Returns:
        An ExternalDataSource implementation based on the environment.
    """
    settings = get_settings()

    if settings.data_source_environment == DataSourceEnvironment.MOCK:
        from src.repositories.external.mock_repository import MockExternalDataSource

        return MockExternalDataSource()
    else:
        from src.repositories.external.prod_repository import ProdExternalDataSource

        return ProdExternalDataSource(settings.mongodb_uri)


__all__ = ["ExternalDataSource", "get_external_data_source"]
