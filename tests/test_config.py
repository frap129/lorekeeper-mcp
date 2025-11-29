"""Tests for configuration management."""

from pathlib import Path

from lorekeeper_mcp.config import Settings, settings


class TestSettings:
    """Test configuration loading and defaults."""

    def test_settings_loads_defaults(self):
        """Test that settings loads with default values."""
        assert settings.milvus_db_path == Path("~/.lorekeeper/milvus.db").expanduser()
        assert settings.cache_ttl_days == 7
        assert settings.error_cache_ttl_seconds == 300
        assert settings.log_level == "INFO"
        assert settings.debug is False
        assert settings.open5e_base_url == "https://api.open5e.com"

    def test_settings_respects_env_vars(self, monkeypatch, tmp_path):
        """Test that settings respects environment variable overrides."""
        # Set environment variables (using LOREKEEPER_ prefix)
        custom_milvus_path = tmp_path / "test_milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(custom_milvus_path))
        monkeypatch.setenv("LOREKEEPER_CACHE_TTL_DAYS", "14")
        monkeypatch.setenv("LOREKEEPER_ERROR_CACHE_TTL_SECONDS", "600")
        monkeypatch.setenv("LOREKEEPER_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("LOREKEEPER_DEBUG", "true")
        monkeypatch.setenv("LOREKEEPER_OPEN5E_BASE_URL", "https://test.open5e.com")

        # Create a new Settings instance to pick up environment variables
        test_settings = Settings()

        assert test_settings.milvus_db_path == custom_milvus_path
        assert test_settings.cache_ttl_days == 14
        assert test_settings.error_cache_ttl_seconds == 600
        assert test_settings.log_level == "DEBUG"
        assert test_settings.debug is True
        assert test_settings.open5e_base_url == "https://test.open5e.com"
