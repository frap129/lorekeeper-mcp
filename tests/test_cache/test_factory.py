"""Tests for cache factory."""

from pathlib import Path

import pytest


class TestCreateCache:
    """Tests for create_cache factory function."""

    def test_create_cache_milvus_backend(self, tmp_path: Path) -> None:
        """Test creating cache with Milvus backend."""
        from lorekeeper_mcp.cache.factory import create_cache
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = create_cache(db_path=str(db_path))

        assert isinstance(cache, MilvusCache)
        assert cache.db_path == db_path

    def test_create_cache_default_is_milvus(self, tmp_path: Path) -> None:
        """Test that default cache is Milvus."""
        from lorekeeper_mcp.cache.factory import create_cache
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test.db"
        cache = create_cache(db_path=str(db_path))

        assert isinstance(cache, MilvusCache)

    def test_backend_parameter_removed(self, tmp_path: Path) -> None:
        """Test that backend parameter no longer exists."""
        from lorekeeper_mcp.cache.factory import create_cache

        # backend parameter should not exist
        with pytest.raises(TypeError) as exc_info:
            create_cache(backend="milvus", db_path=str(tmp_path / "test.db"))  # type: ignore[call-arg]

        assert "backend" in str(exc_info.value)


class TestGetCacheFromConfig:
    """Tests for get_cache_from_config function."""

    def test_get_cache_from_config_milvus_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_cache_from_config returns Milvus cache."""
        from lorekeeper_mcp.cache.factory import get_cache_from_config
        from lorekeeper_mcp.cache.milvus import MilvusCache

        # Set Milvus path
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(tmp_path / "milvus.db"))

        cache = get_cache_from_config()

        assert isinstance(cache, MilvusCache)

    def test_get_cache_from_config_uses_env_milvus_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_cache_from_config uses LOREKEEPER_MILVUS_DB_PATH."""
        from lorekeeper_mcp.cache.factory import get_cache_from_config
        from lorekeeper_mcp.cache.milvus import MilvusCache

        custom_path = tmp_path / "custom_milvus.db"
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(custom_path))

        cache = get_cache_from_config()

        assert isinstance(cache, MilvusCache)
        assert cache.db_path == custom_path
