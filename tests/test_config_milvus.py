"""Tests for Milvus-related configuration settings."""

import importlib
from pathlib import Path


class TestMilvusDbPathConfig:
    """Tests for LOREKEEPER_MILVUS_DB_PATH configuration."""

    def test_milvus_db_path_default(self, monkeypatch):
        """Test that default Milvus DB path is ~/.lorekeeper/milvus.db."""
        monkeypatch.delenv("LOREKEEPER_MILVUS_DB_PATH", raising=False)

        import lorekeeper_mcp.config

        importlib.reload(lorekeeper_mcp.config)
        from lorekeeper_mcp.config import settings

        expected = Path("~/.lorekeeper/milvus.db").expanduser()
        assert settings.milvus_db_path == expected

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
