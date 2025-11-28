"""Tests for cache factory."""

from pathlib import Path

import pytest


class TestCreateCache:
    """Tests for create_cache factory function."""

    def test_create_cache_milvus_backend(self, tmp_path: Path) -> None:
        """Test creating cache with milvus backend."""
        from lorekeeper_mcp.cache.factory import create_cache
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = create_cache(backend="milvus", db_path=str(db_path))

        assert isinstance(cache, MilvusCache)
        assert cache.db_path == db_path

    def test_create_cache_sqlite_backend(self, tmp_path: Path) -> None:
        """Test creating cache with sqlite backend."""
        from lorekeeper_mcp.cache.factory import create_cache
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        db_path = tmp_path / "test_sqlite.db"
        cache = create_cache(backend="sqlite", db_path=str(db_path))

        assert isinstance(cache, SQLiteCache)
        assert cache.db_path == str(db_path)

    def test_create_cache_invalid_backend(self, tmp_path: Path) -> None:
        """Test creating cache with invalid backend raises ValueError."""
        from lorekeeper_mcp.cache.factory import create_cache

        db_path = tmp_path / "test.db"
        with pytest.raises(ValueError) as exc_info:
            create_cache(backend="invalid", db_path=str(db_path))

        assert "Unknown cache backend" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)

    def test_create_cache_default_backend_is_milvus(self, tmp_path: Path) -> None:
        """Test that default backend is milvus."""
        from lorekeeper_mcp.cache.factory import create_cache
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test.db"
        cache = create_cache(db_path=str(db_path))

        assert isinstance(cache, MilvusCache)

    def test_create_cache_case_insensitive_backend(self, tmp_path: Path) -> None:
        """Test that backend parameter is case-insensitive."""
        from lorekeeper_mcp.cache.factory import create_cache
        from lorekeeper_mcp.cache.milvus import MilvusCache
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        db_path = tmp_path / "test.db"

        cache1 = create_cache(backend="MILVUS", db_path=str(db_path))
        assert isinstance(cache1, MilvusCache)

        cache2 = create_cache(backend="SQLite", db_path=str(tmp_path / "test2.db"))
        assert isinstance(cache2, SQLiteCache)


class TestGetCacheFromConfig:
    """Tests for get_cache_from_config function."""

    def test_get_cache_from_config_uses_env_backend(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_cache_from_config reads backend from environment."""
        from lorekeeper_mcp.cache.factory import get_cache_from_config
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "sqlite")
        monkeypatch.setenv("LOREKEEPER_SQLITE_DB_PATH", str(tmp_path / "cache.db"))

        cache = get_cache_from_config()

        assert isinstance(cache, SQLiteCache)

    def test_get_cache_from_config_milvus_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that get_cache_from_config defaults to milvus."""
        from lorekeeper_mcp.cache.factory import get_cache_from_config
        from lorekeeper_mcp.cache.milvus import MilvusCache

        # Clear any existing env vars
        monkeypatch.delenv("LOREKEEPER_CACHE_BACKEND", raising=False)
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
        monkeypatch.setenv("LOREKEEPER_CACHE_BACKEND", "milvus")
        monkeypatch.setenv("LOREKEEPER_MILVUS_DB_PATH", str(custom_path))

        cache = get_cache_from_config()

        assert isinstance(cache, MilvusCache)
        assert cache.db_path == custom_path
