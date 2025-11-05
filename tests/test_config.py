"""Tests for configuration management."""

import os
from pathlib import Path

import pytest

from lorekeeper_mcp.config import settings


class TestSettings:
    """Test configuration loading and defaults."""

    def test_settings_loads_defaults(self):
        """Test that settings loads with default values."""
        assert settings.db_path == Path("./data/cache.db")
        assert settings.cache_ttl_days == 7
        assert settings.error_cache_ttl_seconds == 300
        assert settings.log_level == "INFO"
        assert settings.debug is False
        assert settings.open5e_base_url == "https://api.open5e.com"
        assert settings.dnd5e_base_url == "https://www.dnd5eapi.co/api"

    def test_settings_respects_env_vars(self, monkeypatch):
        """Test that settings respects environment variable overrides."""
        # Set environment variables
        monkeypatch.setenv("DB_PATH", "./data/test.db")
        monkeypatch.setenv("CACHE_TTL_DAYS", "14")
        monkeypatch.setenv("ERROR_CACHE_TTL_SECONDS", "600")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("OPEN5E_BASE_URL", "https://test.open5e.com")
        monkeypatch.setenv("DND5E_BASE_URL", "https://test.dnd5eapi.co/api")

        # Reimport to pick up new environment variables
        import importlib
        import lorekeeper_mcp.config

        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings as reloaded_settings

        assert reloaded_settings.db_path == Path("./data/test.db")
        assert reloaded_settings.cache_ttl_days == 14
        assert reloaded_settings.error_cache_ttl_seconds == 600
        assert reloaded_settings.log_level == "DEBUG"
        assert reloaded_settings.debug is True
        assert reloaded_settings.open5e_base_url == "https://test.open5e.com"
        assert reloaded_settings.dnd5e_base_url == "https://test.dnd5eapi.co/api"
