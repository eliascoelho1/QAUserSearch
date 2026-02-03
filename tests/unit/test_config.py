"""Unit tests for configuration."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from src.config import Settings
from src.schemas.enums import Environment, LogLevel


class TestSettings:
    """Tests for Settings class."""

    def test_default_values(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that default values are set correctly."""
        # Clear environment variables that could override defaults
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("APP_NAME", raising=False)
        monkeypatch.delenv("VERSION", raising=False)

        # Change to a temp directory without .env file
        monkeypatch.chdir(tmp_path)

        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
        )

        assert settings.app_name == "qausersearch"
        assert settings.version == "0.1.0"
        assert settings.environment == Environment.DEVELOPMENT
        assert settings.debug is False
        assert settings.log_level == LogLevel.INFO

    def test_environment_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables override defaults."""
        monkeypatch.setenv("APP_NAME", "test-app")
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test"
        )

        settings = Settings()

        assert settings.app_name == "test-app"
        assert settings.environment == Environment.STAGING

    def test_debug_false_in_production(self) -> None:
        """Test that debug must be False in production."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment=Environment.PRODUCTION,
                debug=True,
                database_url="postgresql+asyncpg://user:pass@localhost/db",
            )

        assert "Debug must be False in production" in str(exc_info.value)

    def test_log_level_not_debug_in_production(self) -> None:
        """Test that log level must be INFO or higher in production."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment=Environment.PRODUCTION,
                log_level=LogLevel.DEBUG,
                database_url="postgresql+asyncpg://user:pass@localhost/db",
            )

        assert "Log level must be INFO or higher" in str(exc_info.value)

    def test_production_valid_settings(self) -> None:
        """Test valid production settings."""
        settings = Settings(
            environment=Environment.PRODUCTION,
            debug=False,
            log_level=LogLevel.INFO,
            database_url="postgresql+asyncpg://user:pass@localhost/db",
        )

        assert settings.environment == Environment.PRODUCTION
        assert settings.debug is False
        assert settings.log_level == LogLevel.INFO
