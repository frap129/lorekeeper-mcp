"""Database cache layer for API responses using SQLite."""

import json
import time
from pathlib import Path
from typing import Any

import aiosqlite

from lorekeeper_mcp.config import settings


async def init_db() -> None:
    """Initialize the database schema.

    Creates the api_cache table with indexes if it doesn't exist.
    Also ensures the parent directory exists and enables WAL mode.
    """
    # Ensure parent directory exists
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Enable WAL mode for better concurrent access
        await db.execute("PRAGMA journal_mode=WAL")

        # Create schema
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                response_data TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                content_type TEXT NOT NULL,
                source_api TEXT NOT NULL
            )
        """
        )

        # Create indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON api_cache(expires_at)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_content_type ON api_cache(content_type)")

        await db.commit()


async def get_cached(key: str) -> dict[str, Any] | None:
    """Retrieve cached data if not expired.

    Args:
        key: Cache key to look up

    Returns:
        Cached data as dict if found and not expired, None otherwise
    """
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """SELECT response_data, expires_at
               FROM api_cache
               WHERE cache_key = ?""",
            (key,),
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        # Check if expired
        if row["expires_at"] < time.time():
            return None

        return json.loads(row["response_data"])


async def set_cached(
    key: str,
    data: dict[str, Any],
    content_type: str,
    ttl_seconds: int,
    source_api: str = "unknown",
) -> None:
    """Store data in cache with TTL.

    Args:
        key: Cache key for the data
        data: Data to cache as dictionary
        content_type: Type of content (e.g., "spell", "monster")
        ttl_seconds: Time to live in seconds
        source_api: Source API that provided the data (default: "unknown")
    """
    async with aiosqlite.connect(settings.db_path) as db:
        now = time.time()
        expires_at = now + ttl_seconds

        await db.execute(
            """INSERT OR REPLACE INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (key, json.dumps(data), now, expires_at, content_type, source_api),
        )
        await db.commit()
