"""Tests for database cache layer."""

import pytest


@pytest.mark.asyncio
async def test_init_db_creates_schema(tmp_path, monkeypatch):
    """Test that init_db creates the database schema."""
    import aiosqlite

    from lorekeeper_mcp.cache.db import init_db
    from lorekeeper_mcp.config import settings

    # Use temporary database
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(settings, "db_path", db_file)

    await init_db()

    # Verify database file exists
    assert db_file.exists()

    # Verify schema was created
    async with aiosqlite.connect(db_file) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='api_cache'"
        )
        result = await cursor.fetchone()
        assert result is not None
        assert result[0] == "api_cache"
