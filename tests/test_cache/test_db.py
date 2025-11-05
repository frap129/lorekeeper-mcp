"""Tests for database cache layer."""

import pytest


@pytest.mark.asyncio
async def test_init_db_creates_schema(test_db):
    """Test that init_db creates the database schema with all components."""
    import aiosqlite

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
        for expected_name in expected_columns.keys():
            assert expected_name in column_names

        # Verify column properties
        for col in columns:
            col_name = col[1]
            if col_name in expected_columns:
                expected = expected_columns[col_name]
                assert col[3] == expected[3]  # notnull
                assert col[5] == expected[5]  # pk

        # Verify indexes were created
        cursor = await db.execute("PRAGMA index_list(api_cache)")
        indexes = {row[1] for row in await cursor.fetchall()}
        assert "idx_expires_at" in indexes
        assert "idx_content_type" in indexes

        # Verify WAL mode is enabled
        cursor = await db.execute("PRAGMA journal_mode")
        journal_mode = await cursor.fetchone()
        assert journal_mode is not None
        assert journal_mode[0] == "wal"


@pytest.mark.asyncio
async def test_get_cached_returns_none_for_missing_key(test_db):
    """Test that get_cached returns None for missing keys."""
    from lorekeeper_mcp.cache.db import get_cached

    result = await get_cached("nonexistent_key")

    assert result is None


@pytest.mark.asyncio
async def test_get_cached_returns_none_for_expired_entry(test_db):
    """Test that get_cached returns None for expired entries."""
    import aiosqlite
    import json
    import time

    from lorekeeper_mcp.cache.db import get_cached
    from lorekeeper_mcp.config import settings

    # Insert expired entry directly
    async with aiosqlite.connect(settings.db_path) as db:
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
    import aiosqlite
    import json
    import time

    from lorekeeper_mcp.cache.db import get_cached
    from lorekeeper_mcp.config import settings

    # Insert valid entry
    test_data = {"spell": "Fireball", "level": 3}
    async with aiosqlite.connect(settings.db_path) as db:
        now = time.time()
        await db.execute(
            """INSERT INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("test_key", json.dumps(test_data), now, now + 3600, "spell", "test"),
        )
        await db.commit()

    result = await get_cached("test_key")

    assert result == test_data


@pytest.mark.asyncio
async def test_set_cached_stores_data(test_db):
    """Test that set_cached stores data with TTL and can be retrieved."""
    from lorekeeper_mcp.cache.db import set_cached, get_cached

    test_data = {"spell": "Magic Missile", "level": 1}
    ttl_seconds = 3600

    await set_cached("spell_key", test_data, "spell", ttl_seconds, "d20_api")

    result = await get_cached("spell_key")

    assert result == test_data


@pytest.mark.asyncio
async def test_set_cached_overwrites_existing(test_db):
    """Test that set_cached overwrites existing entries."""
    from lorekeeper_mcp.cache.db import set_cached, get_cached

    # Store initial data
    initial_data = {"spell": "Fireball", "level": 3}
    await set_cached("spell_key", initial_data, "spell", 3600)

    # Overwrite with new data
    new_data = {"spell": "Ice Storm", "level": 4}
    await set_cached("spell_key", new_data, "spell", 3600)

    # Should retrieve the new data
    result = await get_cached("spell_key")

    assert result == new_data


@pytest.mark.asyncio
async def test_cleanup_expired_removes_old_entries(test_db):
    """Test that cleanup_expired removes expired entries and preserves valid ones."""
    import aiosqlite
    import json
    import time

    from lorekeeper_mcp.cache.db import set_cached, get_cached
    from lorekeeper_mcp.config import settings

    now = time.time()

    # Insert expired entries directly
    async with aiosqlite.connect(settings.db_path) as db:
        # Expired entry 1
        await db.execute(
            """INSERT INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("expired_key_1", json.dumps({"data": "old1"}), now - 200, now - 100, "spell", "test"),
        )
        # Expired entry 2
        await db.execute(
            """INSERT INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("expired_key_2", json.dumps({"data": "old2"}), now - 150, now - 50, "monster", "test"),
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
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM api_cache")
        total_before_row = await cursor.fetchone()
        total_before = total_before_row[0] if total_before_row else 0

    # Import cleanup_expired after setting up test data
    from lorekeeper_mcp.cache.db import cleanup_expired

    # Run cleanup
    deleted_count = await cleanup_expired()

    # Verify cleanup deleted the expired entries
    assert deleted_count == 2

    # Verify valid entries still exist
    assert await get_cached("valid_key_1") == valid_data_1
    assert await get_cached("valid_key_2") == valid_data_2

    # Verify expired entries are completely gone from database
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM api_cache WHERE cache_key IN ('expired_key_1', 'expired_key_2')"
        )
        expired_remaining_row = await cursor.fetchone()
        expired_remaining = expired_remaining_row[0] if expired_remaining_row else 0
        assert expired_remaining == 0

    # Verify total count decreased by 2
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM api_cache")
        total_after_row = await cursor.fetchone()
        total_after = total_after_row[0] if total_after_row else 0
        assert total_after == total_before - 2
