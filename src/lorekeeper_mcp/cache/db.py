"""Database cache layer for API responses using SQLite."""

from pathlib import Path

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
