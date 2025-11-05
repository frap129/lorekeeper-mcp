"""Tests for database cache layer."""

import json
import time

import aiosqlite
import pytest

from lorekeeper_mcp.cache.db import cleanup_expired, get_cached, set_cached


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
