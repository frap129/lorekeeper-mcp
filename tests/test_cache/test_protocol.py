"""Tests for cache protocol definition."""

from typing import Any

import pytest

from lorekeeper_mcp.cache.protocol import CacheProtocol


@pytest.mark.asyncio
async def test_cache_protocol_has_required_methods() -> None:
    """Test that CacheProtocol defines required methods."""
    # Verify CacheProtocol is a Protocol
    assert hasattr(CacheProtocol, "__protocol_attrs__")

    # Verify get_entities method exists
    assert hasattr(CacheProtocol, "get_entities")

    # Verify store_entities method exists
    assert hasattr(CacheProtocol, "store_entities")


@pytest.mark.asyncio
async def test_cache_protocol_get_entities_signature() -> None:
    """Test that get_entities has correct method signature."""
    # Get the get_entities method
    get_entities = CacheProtocol.get_entities

    # Verify it's callable
    assert callable(get_entities)

    # Verify it has correct annotations
    annotations = get_entities.__annotations__
    assert "entity_type" in annotations
    assert "filters" in annotations
    assert "return" in annotations


@pytest.mark.asyncio
async def test_cache_protocol_store_entities_signature() -> None:
    """Test that store_entities has correct method signature."""
    # Get the store_entities method
    store_entities = CacheProtocol.store_entities

    # Verify it's callable
    assert callable(store_entities)

    # Verify it has correct annotations
    annotations = store_entities.__annotations__
    assert "entities" in annotations
    assert "entity_type" in annotations
    assert "return" in annotations


class MockCache:
    """Mock cache implementation for testing protocol compliance."""

    async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        """Get entities by type with optional filters."""
        return []

    async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
        """Store entities in cache."""
        return len(entities)


@pytest.mark.asyncio
async def test_cache_protocol_structural_typing() -> None:
    """Test that implementing classes can satisfy protocol structurally."""
    # Create a mock cache
    mock = MockCache()

    # Test get_entities
    result = await mock.get_entities("spells")
    assert isinstance(result, list)

    # Test store_entities
    entities = [{"slug": "test", "name": "Test Spell"}]
    count = await mock.store_entities(entities, "spells")
    assert count == 1


def test_cache_protocol_has_docstrings() -> None:
    """Test that protocol methods have docstrings."""
    # Verify CacheProtocol has a docstring
    assert CacheProtocol.__doc__ is not None

    # Verify get_entities has a docstring
    get_entities = CacheProtocol.get_entities
    assert get_entities.__doc__ is not None

    # Verify store_entities has a docstring
    store_entities = CacheProtocol.store_entities
    assert store_entities.__doc__ is not None


class TestCacheProtocolSemanticSearch:
    """Tests for semantic_search method in CacheProtocol."""

    def test_protocol_has_semantic_search_method(self) -> None:
        """Test that CacheProtocol defines semantic_search method."""
        import inspect

        # Check that semantic_search is defined in protocol
        assert hasattr(CacheProtocol, "semantic_search")

        # Verify it's a method with correct signature
        sig = inspect.signature(CacheProtocol.semantic_search)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "entity_type" in params
        assert "query" in params
        assert "limit" in params

    def test_milvus_cache_conforms_to_protocol_with_semantic_search(self, tmp_path: Any) -> None:
        """Test that MilvusCache conforms to updated CacheProtocol."""
        from lorekeeper_mcp.cache.milvus import MilvusCache

        db_path = tmp_path / "test_milvus.db"
        cache = MilvusCache(str(db_path))

        # Check it has all protocol methods
        assert hasattr(cache, "get_entities")
        assert hasattr(cache, "store_entities")
        assert hasattr(cache, "semantic_search")
        assert callable(cache.get_entities)
        assert callable(cache.store_entities)
        assert callable(cache.semantic_search)
