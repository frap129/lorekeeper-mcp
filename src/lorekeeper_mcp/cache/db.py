"""Database cache layer for entity-based caching using SQLite."""

import json
import time
from pathlib import Path
from typing import Any, cast

import aiosqlite

from lorekeeper_mcp.cache.schema import (
    ENTITY_TYPES,
    INDEXED_FIELDS,
    SCHEMA_VERSION,
    get_table_name,
    init_entity_cache,
)
from lorekeeper_mcp.config import settings


async def init_db() -> None:
    """Initialize the database schema.

    Creates both entity cache tables and legacy api_cache table for backward compatibility.
    Enables WAL mode for concurrent access.
    """

    # Ensure parent directory exists
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize entity cache tables
    await init_entity_cache(str(settings.db_path))

    # Also create legacy api_cache table for backward compatibility
    async with aiosqlite.connect(settings.db_path) as db:
        # Enable WAL mode for better concurrent access
        await db.execute("PRAGMA journal_mode=WAL")

        # Create legacy schema
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


async def bulk_cache_entities(
    entities: list[dict[str, Any]],
    entity_type: str,
    db_path: str | None = None,
    source_api: str = "unknown",
) -> int:
    """Bulk insert or update entities in cache.

    Args:
        entities: List of entity dictionaries
        entity_type: Type of entities (spells, monsters, etc.)
        db_path: Optional database path (defaults to settings.db_path)
        source_api: Source API identifier

    Returns:
        Number of entities processed
    """
    if not entities:
        return 0

    # Validate entity_type to prevent SQL injection
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    db_path_obj = Path(db_path or settings.db_path)
    table_name = get_table_name(entity_type)
    indexed_fields = INDEXED_FIELDS.get(entity_type, [])

    # Build INSERT OR REPLACE query
    base_columns = ["slug", "name", "data", "source_api", "created_at", "updated_at"]
    # Extract just field names from indexed_fields tuples
    field_names = [field_name for field_name, _ in indexed_fields]
    all_columns = base_columns + field_names
    placeholders = ", ".join(["?"] * len(all_columns))
    columns_str = ", ".join(all_columns)

    sql = f"""
        INSERT OR REPLACE INTO {table_name} ({columns_str})
        VALUES ({placeholders})
    """

    async with aiosqlite.connect(db_path_obj) as db:
        now = time.time()

        # Fetch all existing timestamps in a single query to prevent N+1
        slugs_to_check = [e.get("slug") for e in entities if e.get("slug")]
        existing_timestamps: dict[str, float] = {}

        if slugs_to_check:
            placeholders_for_select = ",".join("?" * len(slugs_to_check))
            cursor = await db.execute(
                f"SELECT slug, created_at FROM {table_name} WHERE slug IN ({placeholders_for_select})",
                slugs_to_check,
            )
            existing_rows = await cursor.fetchall()
            existing_timestamps = {row[0]: row[1] for row in existing_rows}

        rows: list[list[Any]] = []
        for entity in entities:
            slug = entity.get("slug")
            name = entity.get("name", "")
            if not slug:
                continue  # Skip entities without slug

            # Get created_at from pre-fetched timestamps
            created_at = existing_timestamps.get(slug, now)

            # Build row with base columns
            row = [
                slug,
                name,
                json.dumps(entity),  # Full entity as JSON
                source_api,
                created_at,
                now,  # updated_at
            ]

            # Add indexed field values
            for field_name, _ in indexed_fields:
                value = entity.get(field_name)
                # Handle nested damage_type object (weapons)
                if field_name == "damage_type" and isinstance(value, dict):
                    value = value.get("key")
                # Handle nested armor_class object (armor)
                if field_name == "armor_class" and isinstance(value, dict):
                    value = value.get("base")
                row.append(value)

            rows.append(row)

        await db.executemany(sql, rows)
        await db.commit()

        return len(rows)


async def get_cached_entity(
    entity_type: str,
    slug: str,
    db_path: str | None = None,
) -> dict[str, Any] | None:
    """Retrieve a single cached entity by slug.

    Args:
        entity_type: Type of entity
        slug: Entity slug
        db_path: Optional database path

    Returns:
        Entity data dictionary or None if not found
    """
    # Validate entity_type to prevent SQL injection
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    db_path_obj = Path(db_path or settings.db_path)
    table_name = get_table_name(entity_type)

    async with aiosqlite.connect(db_path_obj) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(f"SELECT data FROM {table_name} WHERE slug = ?", (slug,))
        row = await cursor.fetchone()

        if row is None:
            return None

        return cast(dict[str, Any], json.loads(row["data"]))


async def query_cached_entities(
    entity_type: str,
    db_path: str | None = None,
    **filters: Any,
) -> list[dict[str, Any]]:
    """Query cached entities with optional filters.

    Args:
        entity_type: Type of entities to query
        db_path: Optional database path
        **filters: Field filters (e.g., level=3, school="Evocation")

    Returns:
        List of matching entity dictionaries

    Raises:
        ValueError: If entity_type is invalid or filter field is not in allowlist
    """
    # Validate entity_type to prevent SQL injection
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    # Validate filter keys against allowlist to prevent SQL injection
    allowed_fields = {field_name for field_name, _ in INDEXED_FIELDS.get(entity_type, [])}
    for field in filters:
        if field not in allowed_fields:
            raise ValueError(
                f"Invalid filter field '{field}' for entity type '{entity_type}'. "
                f"Allowed fields: {sorted(allowed_fields) if allowed_fields else 'none'}"
            )

    db_path_obj = Path(db_path or settings.db_path)
    table_name = get_table_name(entity_type)

    # Build WHERE clause
    where_clauses = []
    params = []

    for field, value in filters.items():
        where_clauses.append(f"{field} = ?")
        params.append(value)

    where_sql = ""
    if where_clauses:
        where_sql = " WHERE " + " AND ".join(where_clauses)

    query = f"SELECT data FROM {table_name}{where_sql}"

    async with aiosqlite.connect(db_path_obj) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        return [cast(dict[str, Any], json.loads(row["data"])) for row in rows]


# Keep existing functions for backward compatibility
async def get_cached(key: str) -> dict[str, Any] | None:
    """Retrieve cached data if not expired (legacy URL-based cache).

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

        return cast(dict[str, Any], json.loads(row["response_data"]))


async def set_cached(
    key: str,
    data: dict[str, Any],
    content_type: str,
    ttl_seconds: int,
    source_api: str = "unknown",
) -> None:
    """Store data in cache with TTL (legacy URL-based cache).

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


async def cleanup_expired() -> int:
    """Remove expired cache entries from the database.

    Returns:
        Number of entries that were deleted
    """
    async with aiosqlite.connect(settings.db_path) as db:
        current_time = time.time()
        cursor = await db.execute("DELETE FROM api_cache WHERE expires_at < ?", (current_time,))
        deleted_count = cursor.rowcount
        await db.commit()
        return deleted_count


async def get_entity_count(
    entity_type: str,
    db_path: str | None = None,
) -> int:
    """Get count of cached entities for a type.

    Args:
        entity_type: Type of entities to count
        db_path: Optional database path

    Returns:
        Number of cached entities, or 0 if table doesn't exist
    """
    db_path_obj = Path(db_path or settings.db_path)
    table_name = get_table_name(entity_type)

    try:
        async with aiosqlite.connect(db_path_obj) as db:
            cursor = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
            row = await cursor.fetchone()
            return row[0] if row else 0
    except aiosqlite.OperationalError:
        # Table doesn't exist
        return 0


async def get_cache_stats(db_path: str | None = None) -> dict[str, Any]:
    """Get comprehensive cache statistics.

    Args:
        db_path: Optional database path

    Returns:
        Dictionary with cache statistics
    """
    final_db_path: str = str(db_path or settings.db_path)

    # Get entity counts per type
    entity_counts = {}
    for entity_type in ENTITY_TYPES:
        count = await get_entity_count(entity_type, final_db_path)
        entity_counts[entity_type] = count

    # Get database file size
    db_size = 0
    path = Path(final_db_path)
    if path.exists():
        db_size = path.stat().st_size

    # Get table count
    async with aiosqlite.connect(final_db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        row = await cursor.fetchone()
        table_count = row[0] if row else 0

    return {
        "entity_counts": entity_counts,
        "db_size_bytes": db_size,
        "schema_version": SCHEMA_VERSION,
        "table_count": table_count,
    }
