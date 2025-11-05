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
