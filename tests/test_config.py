"""Tests for configuration management."""

from pathlib import Path

from lorekeeper_mcp.config import Settings, get_xdg_data_home


class TestSettings:
    """Test configuration loading and defaults."""

    def test_settings_loads_defaults(self, monkeypatch, tmp_path):
        """Test that settings loads with default values (XDG path for new install)."""
        # Ensure no legacy database exists and no env overrides
        monkeypatch.delenv("LOREKEEPER_MILVUS_DB_PATH", raising=False)
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)

        # Mock the legacy path to a non-existent location to simulate new installation
        import lorekeeper_mcp.config

        legacy_path = tmp_path / "nonexistent" / ".lorekeeper" / "milvus.db"
        monkeypatch.setattr(lorekeeper_mcp.config, "LEGACY_MILVUS_DB_PATH", legacy_path)

        # For a fresh install (no legacy db), should use XDG default
        expected_xdg_path = Path("~/.local/share/lorekeeper/milvus.db").expanduser()

        test_settings = Settings()
        # The path should be the XDG path (since no legacy db exists in test env)
        assert test_settings.milvus_db_path == expected_xdg_path
        assert test_settings.cache_ttl_days == 7
        assert test_settings.error_cache_ttl_seconds == 300
        assert test_settings.log_level == "INFO"
        assert test_settings.debug is False
        assert test_settings.open5e_base_url == "https://api.open5e.com"

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


class TestXdgDataHome:
    """Test XDG_DATA_HOME path resolution."""

    def test_get_xdg_data_home_with_env_var(self, monkeypatch, tmp_path):
        """Test that XDG_DATA_HOME environment variable is respected."""
        custom_xdg = tmp_path / "custom_xdg"
        monkeypatch.setenv("XDG_DATA_HOME", str(custom_xdg))

        result = get_xdg_data_home()
        assert result == custom_xdg

    def test_get_xdg_data_home_without_env_var(self, monkeypatch):
        """Test fallback to ~/.local/share when XDG_DATA_HOME is not set."""
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)

        result = get_xdg_data_home()
        assert result == Path("~/.local/share").expanduser()
