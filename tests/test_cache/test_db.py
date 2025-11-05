"""Tests for database cache layer."""

import pytest


@pytest.mark.asyncio
async def test_init_db_creates_schema(tmp_path, monkeypatch):
    """Test that init_db creates the database schema with all components."""
    import aiosqlite

    from lorekeeper_mcp.cache.db import init_db
    from lorekeeper_mcp.config import settings

    # Use temporary database
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "db_path", db_file)

    await init_db()

    # Verify database file exists
    assert db_file.exists()

    # Verify schema was created completely
    async with aiosqlite.connect(db_file) as db:
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
async def test_get_cached_returns_none_for_missing_key(tmp_path, monkeypatch):
    """Test that get_cached returns None for missing keys."""
    from lorekeeper_mcp.cache.db import init_db, get_cached
    from lorekeeper_mcp.config import settings

    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "db_path", db_file)
    await init_db()

    result = await get_cached("nonexistent_key")

    assert result is None


@pytest.mark.asyncio
async def test_get_cached_returns_none_for_expired_entry(tmp_path, monkeypatch):
    """Test that get_cached returns None for expired entries."""
    import aiosqlite
    import json
    import time

    from lorekeeper_mcp.cache.db import init_db, get_cached
    from lorekeeper_mcp.config import settings

    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "db_path", db_file)
    await init_db()

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
async def test_get_cached_returns_valid_entry(tmp_path, monkeypatch):
    """Test that get_cached returns valid non-expired entries."""
    import aiosqlite
    import json
    import time

    from lorekeeper_mcp.cache.db import init_db, get_cached
    from lorekeeper_mcp.config import settings

    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "db_path", db_file)
    await init_db()

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
async def test_set_cached_stores_data(tmp_path, monkeypatch):
    """Test that set_cached stores data with TTL and can be retrieved."""
    from lorekeeper_mcp.cache.db import init_db, set_cached, get_cached
    from lorekeeper_mcp.config import settings

    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "db_path", db_file)
    await init_db()

    test_data = {"spell": "Magic Missile", "level": 1}
    ttl_seconds = 3600

    await set_cached("spell_key", test_data, "spell", ttl_seconds, "d20_api")

    result = await get_cached("spell_key")

    assert result == test_data


@pytest.mark.asyncio
async def test_set_cached_overwrites_existing(tmp_path, monkeypatch):
    """Test that set_cached overwrites existing entries."""
    from lorekeeper_mcp.cache.db import init_db, set_cached, get_cached
    from lorekeeper_mcp.config import settings

    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "db_path", db_file)
    await init_db()

    # Store initial data
    initial_data = {"spell": "Fireball", "level": 3}
    await set_cached("spell_key", initial_data, "spell", 3600)

    # Overwrite with new data
    new_data = {"spell": "Ice Storm", "level": 4}
    await set_cached("spell_key", new_data, "spell", 3600)

    # Should retrieve the new data
    result = await get_cached("spell_key")

    assert result == new_data
