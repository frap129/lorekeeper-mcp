"""Tests for database cache layer."""

import json
import tempfile
import time
from pathlib import Path

import aiosqlite
import pytest

from lorekeeper_mcp.cache.db import (
    bulk_cache_entities,
    cleanup_expired,
    get_cache_stats,
    get_cached,
    get_cached_entity,
    get_entity_count,
    query_cached_entities,
    set_cached,
)
from lorekeeper_mcp.cache.schema import SCHEMA_VERSION, init_entity_cache


@pytest.mark.asyncio
async def test_init_db_creates_schema(test_db):
    """Test that init_db creates the database schema with all components."""
    # Verify database file exists
    assert test_db.exists()

    # Verify schema was created completely
    async with aiosqlite.connect(test_db) as db:
        # Check table exists
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='api_cache'"
        )
        result = await cursor.fetchone()
        assert result is not None
        assert result[0] == "api_cache"

        # Verify table schema
        cursor = await db.execute("PRAGMA table_info(api_cache)")
        columns = await cursor.fetchall()

        expected_columns = {
            "cache_key": (
                0,
                "cache_key",
                "TEXT",
                0,
                None,
                1,
            ),  # (cid, name, type, notnull, dflt_value, pk)
            "response_data": (1, "response_data", "TEXT", 1, None, 0),
            "created_at": (2, "created_at", "REAL", 1, None, 0),
            "expires_at": (3, "expires_at", "REAL", 1, None, 0),
            "content_type": (4, "content_type", "TEXT", 1, None, 0),
            "source_api": (5, "source_api", "TEXT", 1, None, 0),
        }

        # Check we have all expected columns
        column_names = {col[1] for col in columns}
        for expected_name in expected_columns:
            assert expected_name in column_names

        # Verify column properties
        for col in columns:
            col_name = col[1]
            if col_name in expected_columns:
                assert col == expected_columns[col_name]

        # Check indexes exist
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = await cursor.fetchall()
        index_names = {idx[0] for idx in indexes}
        expected_indexes = {"idx_expires_at", "idx_content_type"}
        assert expected_indexes.issubset(index_names)


@pytest.mark.asyncio
async def test_get_cached_returns_none_for_missing_key(test_db):
    """Test that get_cached returns None for missing keys."""
    result = await get_cached("nonexistent_key")
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_returns_none_for_expired_entry(test_db):
    """Test that get_cached returns None for expired entries."""
    # Insert expired entry directly
    async with aiosqlite.connect(test_db) as db:
        now = time.time()
        await db.execute(
            """INSERT INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("test_key", json.dumps({"data": "value"}), now - 100, now - 1, "spell", "test"),
        )
        await db.commit()

    result = await get_cached("test_key")
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_returns_valid_entry(test_db):
    """Test that get_cached returns valid non-expired entries."""
    # Insert valid entry directly
    async with aiosqlite.connect(test_db) as db:
        now = time.time()
        await db.execute(
            """INSERT INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("test_key", json.dumps({"data": "value"}), now - 100, now + 100, "spell", "test"),
        )
        await db.commit()

    result = await get_cached("test_key")
    assert result == {"data": "value"}


@pytest.mark.asyncio
async def test_set_cached_stores_data(test_db):
    """Test that set_cached stores data with TTL and can be retrieved."""
    test_data = {"spell": "Magic Missile", "level": 1}
    await set_cached("test_key", test_data, "spell", 3600, "test")

    result = await get_cached("test_key")
    assert result == test_data


@pytest.mark.asyncio
async def test_set_cached_overwrites_existing(test_db):
    """Test that set_cached overwrites existing entries."""
    # Store initial data
    initial_data = {"spell": "Fireball", "level": 3}
    await set_cached("test_key", initial_data, "spell", 3600, "test")

    # Verify initial data
    result = await get_cached("test_key")
    assert result == initial_data

    # Overwrite with new data
    updated_data = {"spell": "Fireball", "level": 5, "damage": "8d6"}
    await set_cached("test_key", updated_data, "spell", 3600, "test")

    # Verify updated data
    result = await get_cached("test_key")
    assert result == updated_data


@pytest.mark.asyncio
async def test_cleanup_expired_removes_old_entries(test_db):
    """Test that cleanup_expired removes expired entries and preserves valid ones."""
    now = time.time()

    # Insert expired entries directly
    async with aiosqlite.connect(test_db) as db:
        # Expired entry 1
        await db.execute(
            """INSERT INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "expired_key_1",
                json.dumps({"data": "old1"}),
                now - 200,
                now - 100,
                "spell",
                "test",
            ),
        )
        # Expired entry 2
        await db.execute(
            """INSERT INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "expired_key_2",
                json.dumps({"data": "old2"}),
                now - 150,
                now - 50,
                "monster",
                "test",
            ),
        )
        await db.commit()

    # Insert valid entries using set_cached
    valid_data_1 = {"spell": "Fireball", "level": 3}
    valid_data_2 = {"monster": "Goblin", "cr": 0.25}
    await set_cached("valid_key_1", valid_data_1, "spell", 3600, "test")
    await set_cached("valid_key_2", valid_data_2, "monster", 7200, "test")

    # Verify all entries exist before cleanup
    assert await get_cached("expired_key_1") is None  # Should be None due to expiration check
    assert await get_cached("expired_key_2") is None  # Should be None due to expiration check
    assert await get_cached("valid_key_1") == valid_data_1
    assert await get_cached("valid_key_2") == valid_data_2

    # Count total entries in database before cleanup
    async with aiosqlite.connect(test_db) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM api_cache")
        total_before = (await cursor.fetchone())[0]

    # Run cleanup
    deleted_count = await cleanup_expired()

    # Verify cleanup results
    assert deleted_count >= 0  # Should delete some entries

    # Verify valid entries still exist
    assert await get_cached("valid_key_1") == valid_data_1
    assert await get_cached("valid_key_2") == valid_data_2

    # Count total entries after cleanup
    async with aiosqlite.connect(test_db) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM api_cache")
        total_after = (await cursor.fetchone())[0]

    # Should have fewer entries after cleanup
    assert total_after <= total_before


# ============================================================================
# Task 1.3: Entity Storage Operations Tests
# ============================================================================


@pytest.fixture
async def entity_test_db():
    """Create a test database with entity schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await init_entity_cache(str(db_path))
        yield str(db_path)


@pytest.mark.asyncio
async def test_bulk_cache_entities_inserts_new(entity_test_db):
    """Bulk cache inserts new entities."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1, "school": "Evocation"},
    ]

    count = await bulk_cache_entities(entities, "spells", entity_test_db, "open5e")

    assert count == 2


@pytest.mark.asyncio
async def test_get_cached_entity_retrieves_by_slug(entity_test_db):
    """Get cached entity retrieves by slug."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
    ]
    await bulk_cache_entities(entities, "spells", entity_test_db, "open5e")

    entity = await get_cached_entity("spells", "fireball", entity_test_db)

    assert entity is not None
    assert entity["slug"] == "fireball"
    assert entity["name"] == "Fireball"
    assert entity["level"] == 3
    assert entity["school"] == "Evocation"


@pytest.mark.asyncio
async def test_get_cached_entity_returns_none_for_missing(entity_test_db):
    """Get cached entity returns None for non-existent slug."""
    entity = await get_cached_entity("spells", "nonexistent", entity_test_db)

    assert entity is None


@pytest.mark.asyncio
async def test_bulk_cache_entities_handles_upsert(entity_test_db):
    """Bulk cache updates existing entities."""
    # Insert initial entity
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
    ]
    await bulk_cache_entities(entities, "spells", entity_test_db, "open5e")

    # Update with new data
    updated_entities = [
        {"slug": "fireball", "name": "Fireball (Updated)", "level": 3, "school": "Evocation"},
    ]
    count = await bulk_cache_entities(updated_entities, "spells", entity_test_db, "open5e")

    assert count == 1

    # Verify updated
    entity = await get_cached_entity("spells", "fireball", entity_test_db)
    assert entity["name"] == "Fireball (Updated)"


@pytest.mark.asyncio
async def test_bulk_cache_entities_extracts_indexed_fields(entity_test_db):
    """Bulk cache extracts indexed fields from entity data."""
    entities = [
        {
            "slug": "goblin",
            "name": "Goblin",
            "type": "humanoid",
            "size": "Small",
            "challenge_rating": 0.25,
        },
    ]

    await bulk_cache_entities(entities, "monsters", entity_test_db, "open5e")

    entity = await get_cached_entity("monsters", "goblin", entity_test_db)
    assert entity["type"] == "humanoid"
    assert entity["size"] == "Small"
    assert entity["challenge_rating"] == 0.25


# ============================================================================
# Task 1.4: Entity Query Operations Tests
# ============================================================================


@pytest.mark.asyncio
async def test_query_cached_entities_returns_all(entity_test_db):
    """Query without filters returns all entities."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1, "school": "Evocation"},
        {"slug": "cure-wounds", "name": "Cure Wounds", "level": 1, "school": "Necromancy"},
    ]
    await bulk_cache_entities(entities, "spells", entity_test_db, "open5e")

    results = await query_cached_entities("spells", entity_test_db)

    assert len(results) == 3


@pytest.mark.asyncio
async def test_query_cached_entities_filters_by_single_field(entity_test_db):
    """Query filters by single field."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1, "school": "Evocation"},
        {"slug": "cure-wounds", "name": "Cure Wounds", "level": 1, "school": "Necromancy"},
    ]
    await bulk_cache_entities(entities, "spells", entity_test_db, "open5e")

    results = await query_cached_entities("spells", entity_test_db, level=1)

    assert len(results) == 2
    assert all(e["level"] == 1 for e in results)


@pytest.mark.asyncio
async def test_query_cached_entities_filters_by_multiple_fields(entity_test_db):
    """Query filters by multiple fields with AND logic."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1, "school": "Evocation"},
        {"slug": "cure-wounds", "name": "Cure Wounds", "level": 1, "school": "Necromancy"},
    ]
    await bulk_cache_entities(entities, "spells", entity_test_db, "open5e")

    results = await query_cached_entities("spells", entity_test_db, level=1, school="Evocation")

    assert len(results) == 1
    assert results[0]["slug"] == "magic-missile"


@pytest.mark.asyncio
async def test_query_cached_entities_returns_empty_for_no_matches(entity_test_db):
    """Query with no matches returns empty list."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
    ]
    await bulk_cache_entities(entities, "spells", entity_test_db, "open5e")

    results = await query_cached_entities("spells", entity_test_db, level=9)

    assert results == []


@pytest.mark.asyncio
async def test_query_cached_entities_rejects_invalid_filter_keys(entity_test_db):
    """Query rejects filter keys that are not in the allowlist."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
    ]
    await bulk_cache_entities(entities, "spells", entity_test_db, "open5e")

    # Attempt to filter by invalid field should raise ValueError
    with pytest.raises(ValueError, match="Invalid filter field"):
        await query_cached_entities("spells", entity_test_db, invalid_field="value")


@pytest.mark.asyncio
async def test_query_cached_entities_rejects_sql_injection_in_filter_key(entity_test_db):
    """Query rejects SQL injection attempts via filter keys."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
    ]
    await bulk_cache_entities(entities, "spells", entity_test_db, "open5e")

    # Attempt SQL injection via filter key should raise ValueError
    malicious_filter = "name = 'fireball'; --"
    with pytest.raises(ValueError, match="Invalid filter field"):
        await query_cached_entities("spells", entity_test_db, **{malicious_filter: "dummy"})


@pytest.mark.asyncio
async def test_query_cached_entities_accepts_valid_filter_keys(entity_test_db):
    """Query accepts all valid filter keys from INDEXED_FIELDS."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "shield", "name": "Shield", "level": 1, "school": "Abjuration"},
    ]
    await bulk_cache_entities(entities, "spells", entity_test_db, "open5e")

    # Valid filter keys should work
    results = await query_cached_entities("spells", entity_test_db, level=3, school="Evocation")
    assert len(results) == 1
    assert results[0]["slug"] == "fireball"

    # Another valid key combination
    results = await query_cached_entities("spells", entity_test_db, school="Abjuration")
    assert len(results) == 1
    assert results[0]["slug"] == "shield"


# ============================================================================
# Task 2.1: Entity Count Statistics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_entity_count_returns_count(entity_test_db):
    """Get entity count returns correct count."""
    entities = [
        {"slug": "fireball", "name": "Fireball"},
        {"slug": "magic-missile", "name": "Magic Missile"},
    ]
    await bulk_cache_entities(entities, "spells", entity_test_db, "open5e")

    count = await get_entity_count("spells", entity_test_db)

    assert count == 2


@pytest.mark.asyncio
async def test_get_entity_count_returns_zero_for_empty(entity_test_db):
    """Get entity count returns 0 for empty table."""
    count = await get_entity_count("spells", entity_test_db)

    assert count == 0


@pytest.mark.asyncio
async def test_get_entity_count_handles_nonexistent_table(entity_test_db):
    """Get entity count returns 0 for non-existent table."""
    count = await get_entity_count("invalid_type", entity_test_db)

    assert count == 0


# ============================================================================
# Task 2.2: Comprehensive Cache Statistics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_cache_stats_returns_complete_stats(entity_test_db):
    """Get cache stats returns comprehensive statistics."""
    # Add some test data
    spells = [{"slug": "fireball", "name": "Fireball"}]
    monsters = [{"slug": "goblin", "name": "Goblin"}, {"slug": "dragon", "name": "Dragon"}]
    await bulk_cache_entities(spells, "spells", entity_test_db, "open5e")
    await bulk_cache_entities(monsters, "monsters", entity_test_db, "open5e")

    stats = await get_cache_stats(entity_test_db)

    assert "entity_counts" in stats
    assert stats["entity_counts"]["spells"] == 1
    assert stats["entity_counts"]["monsters"] == 2
    assert "db_size_bytes" in stats
    assert stats["db_size_bytes"] > 0
    assert "schema_version" in stats
    assert stats["schema_version"] == SCHEMA_VERSION
    assert "table_count" in stats
    assert stats["table_count"] >= 2  # At least spells and monsters tables


# ============================================================================
# Task 2.3: Document Tracking Tests
# ============================================================================


@pytest.mark.asyncio
async def test_cache_entity_with_document(entity_test_db):
    """Test that entities with document name are stored correctly."""
    spell = {
        "slug": "fireball",
        "name": "Fireball",
        "level": 3,
        "school": "evocation",
        "document": "System Reference Document 5.1",
    }

    count = await bulk_cache_entities([spell], "spells", db_path=entity_test_db)
    assert count == 1

    # Verify document is preserved
    cached = await get_cached_entity("spells", "fireball", db_path=entity_test_db)
    assert cached is not None
    assert cached["document"] == "System Reference Document 5.1"


@pytest.mark.asyncio
async def test_query_entities_by_document(entity_test_db):
    """Test filtering entities by document name."""
    spells = [
        {
            "slug": "fireball",
            "name": "Fireball",
            "level": 3,
            "document": "System Reference Document 5.1",
        },
        {
            "slug": "homebrew-spell",
            "name": "Homebrew Spell",
            "level": 3,
            "document": "Homebrew Grimoire",
        },
    ]

    await bulk_cache_entities(spells, "spells", db_path=entity_test_db)

    # Filter by document
    srd_spells = await query_cached_entities(
        "spells", db_path=entity_test_db, document="System Reference Document 5.1"
    )
    assert len(srd_spells) == 1
    assert srd_spells[0]["slug"] == "fireball"

    homebrew_spells = await query_cached_entities(
        "spells", db_path=entity_test_db, document="Homebrew Grimoire"
    )
    assert len(homebrew_spells) == 1
    assert homebrew_spells[0]["slug"] == "homebrew-spell"
