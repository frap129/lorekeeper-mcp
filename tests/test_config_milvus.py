"""Tests for Milvus-related configuration settings."""

import importlib
import logging
from pathlib import Path

from lorekeeper_mcp.config import get_default_milvus_db_path


class TestMilvusDbPathConfig:
    """Tests for LOREKEEPER_MILVUS_DB_PATH configuration."""

    def test_milvus_db_path_default_xdg(self, monkeypatch, tmp_path):
        """Test that default Milvus DB path uses XDG path for new installations."""
        monkeypatch.delenv("LOREKEEPER_MILVUS_DB_PATH", raising=False)
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)

        import lorekeeper_mcp.config

        # Mock the legacy path to a non-existent location to simulate new installation
        legacy_path = tmp_path / "nonexistent" / ".lorekeeper" / "milvus.db"
        monkeypatch.setattr(lorekeeper_mcp.config, "LEGACY_MILVUS_DB_PATH", legacy_path)

        # For new installations (no legacy path), should use XDG default
        expected = Path("~/.local/share/lorekeeper/milvus.db").expanduser()
        result = lorekeeper_mcp.config.get_default_milvus_db_path()
        assert result == expected

    def test_milvus_db_path_with_xdg_data_home_set(self, monkeypatch, tmp_path):
        """Test that XDG_DATA_HOME environment variable is respected."""
        custom_xdg = tmp_path / "custom_xdg_data"
        monkeypatch.setenv("XDG_DATA_HOME", str(custom_xdg))
        monkeypatch.delenv("LOREKEEPER_MILVUS_DB_PATH", raising=False)

        import lorekeeper_mcp.config

        # Mock the legacy path to a non-existent location to simulate new installation
        legacy_path = tmp_path / "nonexistent" / ".lorekeeper" / "milvus.db"
        monkeypatch.setattr(lorekeeper_mcp.config, "LEGACY_MILVUS_DB_PATH", legacy_path)

        expected = custom_xdg / "lorekeeper" / "milvus.db"
        result = lorekeeper_mcp.config.get_default_milvus_db_path()
        assert result == expected

    def test_milvus_db_path_from_env(self, tmp_path: Path, monkeypatch):
        """Test that Milvus DB path can be set from environment."""
        custom_path = tmp_path / "custom_milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(custom_path))

        import lorekeeper_mcp.config

        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        assert settings.milvus_db_path == custom_path

    def test_milvus_db_path_expands_tilde(self, monkeypatch):
        """Test that tilde in path is expanded."""
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", "~/custom/milvus.db")

        import lorekeeper_mcp.config

        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        # Should expand tilde to actual home directory
        assert "~" not in str(settings.milvus_db_path)
        assert settings.milvus_db_path.is_absolute()


class TestBackwardCompatibility:
    """Tests for backward compatibility with legacy database location."""

    def test_legacy_path_used_when_only_legacy_exists(self, monkeypatch, tmp_path):
        """Test that legacy path is used when only legacy database exists."""
        # Set up mock home directory with legacy path
        legacy_dir = tmp_path / ".lorekeeper"
        legacy_dir.mkdir()
        legacy_db = legacy_dir / "milvus.db"
        legacy_db.touch()

        # Mock the LEGACY_MILVUS_DB_PATH to point to our test path
        import lorekeeper_mcp.config

        monkeypatch.setattr(lorekeeper_mcp.config, "LEGACY_MILVUS_DB_PATH", legacy_db)
        # Set XDG_DATA_HOME to a location without a database
        xdg_data = tmp_path / "xdg_data"
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg_data))
        monkeypatch.delenv("LOREKEEPER_MILVUS_DB_PATH", raising=False)

        result = get_default_milvus_db_path()
        assert result == legacy_db

    def test_xdg_path_used_when_both_exist(self, monkeypatch, tmp_path, caplog):
        """Test that XDG path is preferred when both locations have databases."""
        # Set up legacy path
        legacy_dir = tmp_path / ".lorekeeper"
        legacy_dir.mkdir()
        legacy_db = legacy_dir / "milvus.db"
        legacy_db.touch()

        # Set up XDG path
        xdg_data = tmp_path / "xdg_data"
        xdg_db_dir = xdg_data / "lorekeeper"
        xdg_db_dir.mkdir(parents=True)
        xdg_db = xdg_db_dir / "milvus.db"
        xdg_db.touch()

        import lorekeeper_mcp.config

        monkeypatch.setattr(lorekeeper_mcp.config, "LEGACY_MILVUS_DB_PATH", legacy_db)
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg_data))
        monkeypatch.delenv("LOREKEEPER_MILVUS_DB_PATH", raising=False)

        with caplog.at_level(logging.WARNING):
            result = get_default_milvus_db_path()

        assert result == xdg_db
        assert "both legacy" in caplog.text.lower() or "both" in caplog.text.lower()

    def test_xdg_path_used_when_only_xdg_exists(self, monkeypatch, tmp_path):
        """Test that XDG path is used when only XDG database exists."""
        # Set up XDG path with database
        xdg_data = tmp_path / "xdg_data"
        xdg_db_dir = xdg_data / "lorekeeper"
        xdg_db_dir.mkdir(parents=True)
        xdg_db = xdg_db_dir / "milvus.db"
        xdg_db.touch()

        # Legacy path does not exist
        legacy_db = tmp_path / ".lorekeeper" / "milvus.db"

        import lorekeeper_mcp.config

        monkeypatch.setattr(lorekeeper_mcp.config, "LEGACY_MILVUS_DB_PATH", legacy_db)
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg_data))
        monkeypatch.delenv("LOREKEEPER_MILVUS_DB_PATH", raising=False)

        result = get_default_milvus_db_path()
        assert result == xdg_db

    def test_xdg_path_used_for_new_installation(self, monkeypatch, tmp_path):
        """Test that XDG path is used when neither location has a database."""
        # Neither path exists
        legacy_db = tmp_path / ".lorekeeper" / "milvus.db"
        xdg_data = tmp_path / "xdg_data"

        import lorekeeper_mcp.config

        monkeypatch.setattr(lorekeeper_mcp.config, "LEGACY_MILVUS_DB_PATH", legacy_db)
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg_data))
        monkeypatch.delenv("LOREKEEPER_MILVUS_DB_PATH", raising=False)

        result = get_default_milvus_db_path()
        expected = xdg_data / "lorekeeper" / "milvus.db"
        assert result == expected

    def test_legacy_path_logs_info_message(self, monkeypatch, tmp_path, caplog):
        """Test that using legacy path logs an informational message."""
        # Set up legacy path
        legacy_dir = tmp_path / ".lorekeeper"
        legacy_dir.mkdir()
        legacy_db = legacy_dir / "milvus.db"
        legacy_db.touch()

        # XDG path does not exist
        xdg_data = tmp_path / "xdg_data"

        import lorekeeper_mcp.config

        monkeypatch.setattr(lorekeeper_mcp.config, "LEGACY_MILVUS_DB_PATH", legacy_db)
        monkeypatch.setenv("XDG_DATA_HOME", str(xdg_data))
        monkeypatch.delenv("LOREKEEPER_MILVUS_DB_PATH", raising=False)

        with caplog.at_level(logging.INFO):
            result = get_default_milvus_db_path()

        assert result == legacy_db
        assert "legacy" in caplog.text.lower() or "backward" in caplog.text.lower()


class TestEmbeddingModelConfig:
    """Tests for LOREKEEPER_EMBEDDING_MODEL configuration."""

    def test_embedding_model_default(self, monkeypatch):
        """Test that default embedding model is all-MiniLM-L6-v2."""
        monkeypatch.delenv("LOREKEEPER_EMBEDDING_MODEL", raising=False)

        import lorekeeper_mcp.config

        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        assert settings.embedding_model == "all-MiniLM-L6-v2"

    def test_embedding_model_from_env(self, monkeypatch):
        """Test that embedding model can be set from environment."""
        monkeypatch.setenv("LOREKEEPER_EMBEDDING_MODEL", "custom-model")

        import lorekeeper_mcp.config

        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        assert settings.embedding_model == "custom-model"


class TestConfigIntegration:
    """Integration tests for configuration with cache factory."""

    def test_config_integrates_with_cache_factory(self, tmp_path: Path, monkeypatch):
        """Test that config values work with cache factory."""
        db_path = tmp_path / "integration_milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(db_path))

        import lorekeeper_mcp.config

        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.cache.factory import create_cache
        from lorekeeper_mcp.config import settings

        cache = create_cache(
            db_path=str(settings.milvus_db_path),
        )

        from lorekeeper_mcp.cache.milvus import MilvusCache

        assert isinstance(cache, MilvusCache)
        assert cache.db_path == db_path
