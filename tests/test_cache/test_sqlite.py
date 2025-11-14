"""Tests for SQLiteCache implementation."""

import pytest

from lorekeeper_mcp.cache.sqlite import SQLiteCache


@pytest.mark.asyncio
async def test_sqlite_cache_stores_entities(test_db):
    """Test that SQLiteCache.store_entities stores entities correctly."""
    cache = SQLiteCache(str(test_db))

    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1, "school": "Evocation"},
    ]

    count = await cache.store_entities(entities, "spells")

    assert count == 2


@pytest.mark.asyncio
async def test_sqlite_cache_retrieves_all_entities(test_db):
    """Test that SQLiteCache.get_entities retrieves all entities when no filters."""
    cache = SQLiteCache(str(test_db))

    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1, "school": "Evocation"},
    ]
    await cache.store_entities(entities, "spells")

    retrieved = await cache.get_entities("spells")

    assert len(retrieved) == 2
    slugs = {e["slug"] for e in retrieved}
    assert slugs == {"fireball", "magic-missile"}


@pytest.mark.asyncio
async def test_sqlite_cache_filters_entities(test_db):
    """Test that SQLiteCache.get_entities filters by indexed fields."""
    cache = SQLiteCache(str(test_db))

    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1, "school": "Evocation"},
        {"slug": "cone-of-cold", "name": "Cone of Cold", "level": 5, "school": "Evocation"},
    ]
    await cache.store_entities(entities, "spells")

    # Filter by level
    level_3 = await cache.get_entities("spells", level=3)

    assert len(level_3) == 1
    assert level_3[0]["slug"] == "fireball"


@pytest.mark.asyncio
async def test_sqlite_cache_returns_empty_list_for_no_matches(test_db):
    """Test that SQLiteCache.get_entities returns empty list when no matches."""
    cache = SQLiteCache(str(test_db))

    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
    ]
    await cache.store_entities(entities, "spells")

    # Filter by level that doesn't exist
    results = await cache.get_entities("spells", level=9)

    assert results == []


@pytest.mark.asyncio
async def test_sqlite_cache_raises_on_invalid_entity_type(test_db):
    """Test that SQLiteCache raises ValueError for invalid entity type."""
    cache = SQLiteCache(str(test_db))

    entities = [{"slug": "test", "name": "Test"}]

    with pytest.raises(ValueError, match="Invalid entity type"):
        await cache.store_entities(entities, "invalid_type")


@pytest.mark.asyncio
async def test_sqlite_cache_raises_on_empty_entities(test_db):
    """Test that SQLiteCache raises ValueError for empty entities list."""
    cache = SQLiteCache(str(test_db))

    with pytest.raises(ValueError, match="entities list is empty"):
        await cache.store_entities([], "spells")


@pytest.mark.asyncio
async def test_sqlite_cache_accepts_custom_db_path(tmp_path):
    """Test that SQLiteCache can accept a custom database path."""
    custom_db = tmp_path / "custom.db"

    # This should not raise
    cache = SQLiteCache(str(custom_db))
    assert cache is not None


@pytest.mark.asyncio
async def test_sqlite_cache_get_entities_with_document_filter(test_db):
    """Test SQLiteCache.get_entities with document filter."""
    cache = SQLiteCache(str(test_db))

    # Store some test entities with documents
    entities = [
        {"slug": "spell-1", "name": "Fireball", "document": "srd-5e"},
        {"slug": "spell-2", "name": "Lightning Bolt", "document": "srd-5e"},
        {"slug": "spell-3", "name": "Tasha's Hideous Laughter", "document": "tce"},
    ]
    await cache.store_entities(entities, "spells")

    # Filter by single document
    results = await cache.get_entities("spells", document="srd-5e")
    assert len(results) == 2
    assert all(r["document"] == "srd-5e" for r in results)

    # Filter by multiple documents
    results = await cache.get_entities("spells", document=["srd-5e", "tce"])
    assert len(results) == 3
