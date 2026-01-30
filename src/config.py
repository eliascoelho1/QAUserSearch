"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.schemas.enums import DataSourceEnvironment, Environment, LogLevel


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="qausersearch", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT, description="Runtime environment"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")

    # Database - Application
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/qausersearch",
        description="Application database URL",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # CORS
    allowed_hosts: list[str] = Field(default=["*"], description="Allowed hosts")
    cors_origins: list[str] = Field(default=[], description="CORS allowed origins")

    # Metrics
    metrics_enabled: bool = Field(default=True, description="Enable metrics endpoint")

    # External Data Sources
    data_source_environment: DataSourceEnvironment = Field(
        default=DataSourceEnvironment.MOCK,
        description="External data source environment (MOCK or PROD)",
    )
    schema_sample_size: int = Field(
        default=500,
        description="Number of documents to sample for schema extraction",
        ge=1,
        le=10000,
    )
    enumerable_cardinality_limit: int = Field(
        default=50,
        description="Maximum unique values for a field to be considered enumerable",
        ge=1,
        le=1000,
    )
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI for PROD environment",
    )

    @field_validator("debug", mode="after")
    @classmethod
    def validate_debug_production(cls, v: bool, info: Any) -> bool:
        """Ensure debug is False in production."""
        env = info.data.get("environment")
        if env == Environment.PRODUCTION and v:
            raise ValueError("Debug must be False in production environment")
        return v

    @field_validator("log_level", mode="after")
    @classmethod
    def validate_log_level_production(cls, v: LogLevel, info: Any) -> LogLevel:
        """Ensure log level is INFO or higher in production."""
        env = info.data.get("environment")
        if env == Environment.PRODUCTION and v == LogLevel.DEBUG:
            raise ValueError("Log level must be INFO or higher in production")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
