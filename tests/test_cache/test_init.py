"""Tests for cache module exports."""


class TestCacheModuleExports:
    """Tests for cache module __all__ exports."""

    def test_cache_protocol_exported(self) -> None:
        """Test that CacheProtocol is exported from cache module."""
        from lorekeeper_mcp.cache import CacheProtocol

        assert CacheProtocol is not None

    def test_sqlite_cache_exported(self) -> None:
        """Test that SQLiteCache is exported from cache module."""
        from lorekeeper_mcp.cache import SQLiteCache

        assert SQLiteCache is not None

    def test_milvus_cache_exported(self) -> None:
        """Test that MilvusCache is exported from cache module."""
        from lorekeeper_mcp.cache import MilvusCache

        assert MilvusCache is not None

    def test_embedding_service_exported(self) -> None:
        """Test that EmbeddingService is exported from cache module."""
        from lorekeeper_mcp.cache import EmbeddingService

        assert EmbeddingService is not None

    def test_create_cache_exported(self) -> None:
        """Test that create_cache is exported from cache module."""
        from lorekeeper_mcp.cache import create_cache

        assert callable(create_cache)

    def test_get_cache_from_config_exported(self) -> None:
        """Test that get_cache_from_config is exported from cache module."""
        from lorekeeper_mcp.cache import get_cache_from_config

        assert callable(get_cache_from_config)

    def test_all_exports_are_defined(self) -> None:
        """Test that __all__ contains expected exports."""
        from lorekeeper_mcp import cache

        expected_exports = [
            "CacheProtocol",
            "SQLiteCache",
            "MilvusCache",
            "EmbeddingService",
            "create_cache",
            "get_cache_from_config",
        ]

        for export in expected_exports:
            assert export in cache.__all__, f"Missing export: {export}"

    def test_backward_compatibility_sqlite_cache(self) -> None:
        """Test that existing SQLiteCache import pattern still works."""
        from lorekeeper_mcp.cache import SQLiteCache

        # Verify class has expected methods
        assert hasattr(SQLiteCache, "get_entities")
        assert hasattr(SQLiteCache, "store_entities")
