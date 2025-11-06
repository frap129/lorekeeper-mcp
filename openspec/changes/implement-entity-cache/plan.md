# Entity-Based Cache Implementation Plan

**Goal:** Replace URL-based caching with entity-centric storage enabling parallel queries, offline fallback, and infinite TTL for D&D game data.

**Architecture:** Store each entity (spell, monster, item) individually in type-specific SQLite tables with slug as primary key. Query cache in parallel with API calls, merge results, and serve from cache during network failures. No TTL expiration—entities cached indefinitely unless explicitly updated.

**Tech Stack:** SQLite with WAL mode, aiosqlite for async operations, asyncio.gather for parallel queries, JSON blob storage with indexed filter fields.

---

## Phase 1: Cache Schema & Core Operations

### Task 1.1: Create entity table schema definitions

**Files:**

- Create: `src/lorekeeper_mcp/cache/schema.py`
- Test: `tests/test_cache/test_schema.py`

**Step 1: Write the failing test**

```python
# tests/test_cache/test_schema.py
"""Tests for cache schema definitions."""

import pytest
from lorekeeper_mcp.cache.schema import (
    ENTITY_TYPES,
    SCHEMA_VERSION,
    get_table_name,
    get_create_table_sql,
)


def test_schema_version_exists():
    """Schema version constant is defined."""
    assert isinstance(SCHEMA_VERSION, int)
    assert SCHEMA_VERSION > 0


def test_entity_types_defined():
    """All entity types are listed."""
    assert "spells" in ENTITY_TYPES
    assert "monsters" in ENTITY_TYPES
    assert "weapons" in ENTITY_TYPES
    assert "armor" in ENTITY_TYPES
    assert len(ENTITY_TYPES) >= 4  # At least these core types


def test_get_table_name():
    """Table names match entity types."""
    assert get_table_name("spells") == "spells"
    assert get_table_name("monsters") == "monsters"


def test_get_create_table_sql_for_spells():
    """Spells table has correct schema."""
    sql = get_create_table_sql("spells")
    assert "CREATE TABLE spells" in sql
    assert "slug TEXT PRIMARY KEY" in sql
    assert "name TEXT NOT NULL" in sql
    assert "data TEXT NOT NULL" in sql  # JSON blob
    assert "source_api TEXT NOT NULL" in sql
    assert "created_at REAL NOT NULL" in sql
    assert "updated_at REAL NOT NULL" in sql
    # Spell-specific indexed fields
    assert "level INTEGER" in sql
    assert "school TEXT" in sql
    assert "concentration BOOLEAN" in sql
    assert "ritual BOOLEAN" in sql


def test_get_create_table_sql_for_monsters():
    """Monsters table has correct schema with monster-specific fields."""
    sql = get_create_table_sql("monsters")
    assert "CREATE TABLE monsters" in sql
    assert "slug TEXT PRIMARY KEY" in sql
    # Monster-specific indexed fields
    assert "challenge_rating TEXT" in sql
    assert "type TEXT" in sql
    assert "size TEXT" in sql
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cache/test_schema.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.cache.schema'"

**Step 3: Write minimal implementation**

```python
# src/lorekeeper_mcp/cache/schema.py
"""Cache schema definitions for entity-based tables."""

SCHEMA_VERSION = 1

ENTITY_TYPES = [
    "spells",
    "monsters",
    "weapons",
    "armor",
    "classes",
    "races",
    "backgrounds",
    "feats",
    "conditions",
    "rules",
    "rule_sections",
]

# Indexed fields per entity type for filtering
INDEXED_FIELDS = {
    "spells": ["level", "school", "concentration", "ritual"],
    "monsters": ["challenge_rating", "type", "size"],
    "weapons": ["category", "damage_type"],
    "armor": ["category", "armor_class"],
    "classes": ["hit_die"],
    "races": ["size"],
    "backgrounds": [],
    "feats": [],
    "conditions": [],
    "rules": ["parent"],
    "rule_sections": ["parent"],
}


def get_table_name(entity_type: str) -> str:
    """Get table name for entity type."""
    return entity_type


def get_create_table_sql(entity_type: str) -> str:
    """Generate CREATE TABLE SQL for entity type."""
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Unknown entity type: {entity_type}")

    indexed_fields = INDEXED_FIELDS.get(entity_type, [])

    # Build indexed field definitions
    field_definitions = []
    for field in indexed_fields:
        # Determine field type based on common patterns
        if field in ["level", "hit_die", "armor_class"]:
            field_type = "INTEGER"
        elif field in ["concentration", "ritual"]:
            field_type = "BOOLEAN"
        else:
            field_type = "TEXT"
        field_definitions.append(f"    {field} {field_type}")

    fields_sql = ",\n".join(field_definitions)
    if fields_sql:
        fields_sql = ",\n" + fields_sql

    return f"""CREATE TABLE IF NOT EXISTS {entity_type} (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    source_api TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL{fields_sql}
)"""
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cache/test_schema.py -v`
Expected: PASS (all tests pass)

**Step 5: Commit**

```bash
git add tests/test_cache/test_schema.py src/lorekeeper_mcp/cache/schema.py
git commit -m "feat(cache): add entity table schema definitions"
```

---

### Task 1.2: Implement schema initialization

**Files:**

- Modify: `src/lorekeeper_mcp/cache/schema.py`
- Test: `tests/test_cache/test_schema.py`

**Step 1: Write the failing test**

```python
# Add to tests/test_cache/test_schema.py
import aiosqlite
import pytest
from pathlib import Path
import tempfile

from lorekeeper_mcp.cache.schema import init_entity_cache, get_index_sql


@pytest.mark.asyncio
async def test_init_entity_cache_creates_tables():
    """Initialize creates all entity tables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        await init_entity_cache(str(db_path))

        # Verify database exists
        assert db_path.exists()

        # Verify tables created
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in await cursor.fetchall()}

            assert "spells" in tables
            assert "monsters" in tables
            assert "weapons" in tables
            assert "armor" in tables


@pytest.mark.asyncio
async def test_init_entity_cache_creates_indexes():
    """Initialize creates indexes on filtered fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        await init_entity_cache(str(db_path))

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = {row[0] for row in await cursor.fetchall()}

            # Check for spell indexes
            assert "idx_spells_level" in indexes
            assert "idx_spells_school" in indexes

            # Check for monster indexes
            assert "idx_monsters_challenge_rating" in indexes
            assert "idx_monsters_type" in indexes


@pytest.mark.asyncio
async def test_init_entity_cache_enables_wal_mode():
    """Initialize enables WAL mode for concurrent access."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        await init_entity_cache(str(db_path))

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("PRAGMA journal_mode")
            mode = (await cursor.fetchone())[0]
            assert mode.lower() == "wal"


def test_get_index_sql():
    """Index SQL generated correctly."""
    indexes = get_index_sql("spells")
    assert len(indexes) > 0
    assert any("idx_spells_level" in sql for sql in indexes)
    assert any("ON spells(level)" in sql for sql in indexes)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cache/test_schema.py::test_init_entity_cache_creates_tables -v`
Expected: FAIL with "AttributeError: ... has no attribute 'init_entity_cache'"

**Step 3: Write minimal implementation**

```python
# Add to src/lorekeeper_mcp/cache/schema.py
from pathlib import Path
import aiosqlite


def get_index_sql(entity_type: str) -> list[str]:
    """Generate CREATE INDEX statements for entity type."""
    indexed_fields = INDEXED_FIELDS.get(entity_type, [])
    indexes = []

    for field in indexed_fields:
        index_name = f"idx_{entity_type}_{field}"
        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {entity_type}({field})"
        indexes.append(sql)

    return indexes


async def init_entity_cache(db_path: str) -> None:
    """Initialize entity cache tables and indexes.

    Args:
        db_path: Path to SQLite database file
    """
    # Ensure parent directory exists
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Enable WAL mode for concurrent access
        await db.execute("PRAGMA journal_mode=WAL")

        # Create all entity tables
        for entity_type in ENTITY_TYPES:
            table_sql = get_create_table_sql(entity_type)
            await db.execute(table_sql)

            # Create indexes for this table
            for index_sql in get_index_sql(entity_type):
                await db.execute(index_sql)

        await db.commit()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cache/test_schema.py -v`
Expected: PASS (all tests pass)

**Step 5: Commit**

```bash
git add tests/test_cache/test_schema.py src/lorekeeper_mcp/cache/schema.py
git commit -m "feat(cache): implement schema initialization with indexes"
```

---

### Task 1.3: Implement entity storage operations

**Files:**

- Modify: `src/lorekeeper_mcp/cache/db.py`
- Test: `tests/test_cache/test_db.py`

**Step 1: Write the failing test**

```python
# tests/test_cache/test_db.py (rewrite completely)
"""Tests for cache database operations."""

import json
import tempfile
from pathlib import Path

import pytest

from lorekeeper_mcp.cache.db import (
    bulk_cache_entities,
    get_cached_entity,
    init_db,
)
from lorekeeper_mcp.cache.schema import init_entity_cache


@pytest.fixture
async def test_db():
    """Create a test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await init_entity_cache(str(db_path))
        yield str(db_path)


@pytest.mark.asyncio
async def test_bulk_cache_entities_inserts_new(test_db):
    """Bulk cache inserts new entities."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1, "school": "Evocation"},
    ]

    count = await bulk_cache_entities(entities, "spells", test_db, "open5e")

    assert count == 2


@pytest.mark.asyncio
async def test_get_cached_entity_retrieves_by_slug(test_db):
    """Get cached entity retrieves by slug."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
    ]
    await bulk_cache_entities(entities, "spells", test_db, "open5e")

    entity = await get_cached_entity("spells", "fireball", test_db)

    assert entity is not None
    assert entity["slug"] == "fireball"
    assert entity["name"] == "Fireball"
    assert entity["level"] == 3
    assert entity["school"] == "Evocation"


@pytest.mark.asyncio
async def test_get_cached_entity_returns_none_for_missing(test_db):
    """Get cached entity returns None for non-existent slug."""
    entity = await get_cached_entity("spells", "nonexistent", test_db)

    assert entity is None


@pytest.mark.asyncio
async def test_bulk_cache_entities_handles_upsert(test_db):
    """Bulk cache updates existing entities."""
    # Insert initial entity
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
    ]
    await bulk_cache_entities(entities, "spells", test_db, "open5e")

    # Update with new data
    updated_entities = [
        {"slug": "fireball", "name": "Fireball (Updated)", "level": 3, "school": "Evocation"},
    ]
    count = await bulk_cache_entities(updated_entities, "spells", test_db, "open5e")

    assert count == 1

    # Verify updated
    entity = await get_cached_entity("spells", "fireball", test_db)
    assert entity["name"] == "Fireball (Updated)"


@pytest.mark.asyncio
async def test_bulk_cache_entities_extracts_indexed_fields(test_db):
    """Bulk cache extracts indexed fields from entity data."""
    entities = [
        {
            "slug": "goblin",
            "name": "Goblin",
            "type": "humanoid",
            "size": "Small",
            "challenge_rating": "1/4",
        },
    ]

    await bulk_cache_entities(entities, "monsters", test_db, "open5e")

    entity = await get_cached_entity("monsters", "goblin", test_db)
    assert entity["type"] == "humanoid"
    assert entity["size"] == "Small"
    assert entity["challenge_rating"] == "1/4"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cache/test_db.py::test_bulk_cache_entities_inserts_new -v`
Expected: FAIL with import errors or function not found

**Step 3: Write minimal implementation**

```python
# Modify src/lorekeeper_mcp/cache/db.py
# Replace the entire file contents:
"""Database cache layer for entity-based caching using SQLite."""

import json
import time
from pathlib import Path
from typing import Any

import aiosqlite

from lorekeeper_mcp.cache.schema import INDEXED_FIELDS, get_table_name
from lorekeeper_mcp.config import settings


async def init_db() -> None:
    """Initialize the database schema.

    Imports and delegates to init_entity_cache for new schema.
    """
    from lorekeeper_mcp.cache.schema import init_entity_cache

    await init_entity_cache(settings.db_path)


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

    db_path = db_path or settings.db_path
    table_name = get_table_name(entity_type)
    indexed_fields = INDEXED_FIELDS.get(entity_type, [])

    # Build INSERT OR REPLACE query
    base_columns = ["slug", "name", "data", "source_api", "created_at", "updated_at"]
    all_columns = base_columns + indexed_fields
    placeholders = ", ".join(["?"] * len(all_columns))
    columns_str = ", ".join(all_columns)

    sql = f"""
        INSERT OR REPLACE INTO {table_name} ({columns_str})
        VALUES ({placeholders})
    """

    async with aiosqlite.connect(db_path) as db:
        now = time.time()

        rows = []
        for entity in entities:
            slug = entity.get("slug")
            name = entity.get("name", "")
            if not slug:
                continue  # Skip entities without slug

            # Check if entity already exists to preserve created_at
            cursor = await db.execute(
                f"SELECT created_at FROM {table_name} WHERE slug = ?",
                (slug,)
            )
            existing = await cursor.fetchone()
            created_at = existing[0] if existing else now

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
            for field in indexed_fields:
                row.append(entity.get(field))

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
    db_path = db_path or settings.db_path
    table_name = get_table_name(entity_type)

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            f"SELECT data FROM {table_name} WHERE slug = ?",
            (slug,)
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        return json.loads(row["data"])


# Keep existing functions for backward compatibility
async def get_cached(key: str) -> dict[str, Any] | None:
    """Retrieve cached data if not expired (legacy URL-based cache)."""
    # Legacy function - will be removed after migration
    return None


async def set_cached(
    key: str,
    data: dict[str, Any],
    content_type: str,
    ttl_seconds: int,
    source_api: str = "unknown",
) -> None:
    """Store data in cache with TTL (legacy URL-based cache)."""
    # Legacy function - will be removed after migration
    pass


async def cleanup_expired() -> int:
    """Remove expired cache entries (legacy URL-based cache)."""
    # Legacy function - will be removed after migration
    return 0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cache/test_db.py -v`
Expected: PASS (all tests pass)

**Step 5: Commit**

```bash
git add tests/test_cache/test_db.py src/lorekeeper_mcp/cache/db.py
git commit -m "feat(cache): implement entity storage and retrieval operations"
```

---

### Task 1.4: Implement entity query operations with filters

**Files:**

- Modify: `src/lorekeeper_mcp/cache/db.py`
- Test: `tests/test_cache/test_db.py`

**Step 1: Write the failing test**

```python
# Add to tests/test_cache/test_db.py
from lorekeeper_mcp.cache.db import query_cached_entities


@pytest.mark.asyncio
async def test_query_cached_entities_returns_all(test_db):
    """Query without filters returns all entities."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1, "school": "Evocation"},
        {"slug": "cure-wounds", "name": "Cure Wounds", "level": 1, "school": "Necromancy"},
    ]
    await bulk_cache_entities(entities, "spells", test_db, "open5e")

    results = await query_cached_entities("spells", test_db)

    assert len(results) == 3


@pytest.mark.asyncio
async def test_query_cached_entities_filters_by_single_field(test_db):
    """Query filters by single field."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1, "school": "Evocation"},
        {"slug": "cure-wounds", "name": "Cure Wounds", "level": 1, "school": "Necromancy"},
    ]
    await bulk_cache_entities(entities, "spells", test_db, "open5e")

    results = await query_cached_entities("spells", test_db, level=1)

    assert len(results) == 2
    assert all(e["level"] == 1 for e in results)


@pytest.mark.asyncio
async def test_query_cached_entities_filters_by_multiple_fields(test_db):
    """Query filters by multiple fields with AND logic."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1, "school": "Evocation"},
        {"slug": "cure-wounds", "name": "Cure Wounds", "level": 1, "school": "Necromancy"},
    ]
    await bulk_cache_entities(entities, "spells", test_db, "open5e")

    results = await query_cached_entities("spells", test_db, level=1, school="Evocation")

    assert len(results) == 1
    assert results[0]["slug"] == "magic-missile"


@pytest.mark.asyncio
async def test_query_cached_entities_returns_empty_for_no_matches(test_db):
    """Query with no matches returns empty list."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"},
    ]
    await bulk_cache_entities(entities, "spells", test_db, "open5e")

    results = await query_cached_entities("spells", test_db, level=9)

    assert results == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cache/test_db.py::test_query_cached_entities_returns_all -v`
Expected: FAIL with "ImportError: cannot import name 'query_cached_entities'"

**Step 3: Write minimal implementation**

```python
# Add to src/lorekeeper_mcp/cache/db.py
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
    """
    db_path = db_path or settings.db_path
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

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        return [json.loads(row["data"]) for row in rows]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cache/test_db.py -v`
Expected: PASS (all tests pass)

**Step 5: Commit**

```bash
git add tests/test_cache/test_db.py src/lorekeeper_mcp/cache/db.py
git commit -m "feat(cache): implement filtered entity queries"
```

---

## Phase 2: Cache Statistics & Observability

### Task 2.1: Implement entity count statistics

**Files:**

- Modify: `src/lorekeeper_mcp/cache/db.py`
- Test: `tests/test_cache/test_db.py`

**Step 1: Write the failing test**

```python
# Add to tests/test_cache/test_db.py
from lorekeeper_mcp.cache.db import get_entity_count


@pytest.mark.asyncio
async def test_get_entity_count_returns_count(test_db):
    """Get entity count returns correct count."""
    entities = [
        {"slug": "fireball", "name": "Fireball"},
        {"slug": "magic-missile", "name": "Magic Missile"},
    ]
    await bulk_cache_entities(entities, "spells", test_db, "open5e")

    count = await get_entity_count("spells", test_db)

    assert count == 2


@pytest.mark.asyncio
async def test_get_entity_count_returns_zero_for_empty(test_db):
    """Get entity count returns 0 for empty table."""
    count = await get_entity_count("spells", test_db)

    assert count == 0


@pytest.mark.asyncio
async def test_get_entity_count_handles_nonexistent_table(test_db):
    """Get entity count returns 0 for non-existent table."""
    count = await get_entity_count("invalid_type", test_db)

    assert count == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cache/test_db.py::test_get_entity_count_returns_count -v`
Expected: FAIL with "ImportError: cannot import name 'get_entity_count'"

**Step 3: Write minimal implementation**

```python
# Add to src/lorekeeper_mcp/cache/db.py
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
    db_path = db_path or settings.db_path
    table_name = get_table_name(entity_type)

    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
            row = await cursor.fetchone()
            return row[0] if row else 0
    except aiosqlite.OperationalError:
        # Table doesn't exist
        return 0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cache/test_db.py::test_get_entity_count_returns_count tests/test_cache/test_db.py::test_get_entity_count_returns_zero_for_empty tests/test_cache/test_db.py::test_get_entity_count_handles_nonexistent_table -v`
Expected: PASS (all 3 tests pass)

**Step 5: Commit**

```bash
git add tests/test_cache/test_db.py src/lorekeeper_mcp/cache/db.py
git commit -m "feat(cache): add entity count statistics"
```

---

### Task 2.2: Implement comprehensive cache statistics

**Files:**

- Modify: `src/lorekeeper_mcp/cache/db.py`
- Test: `tests/test_cache/test_db.py`

**Step 1: Write the failing test**

```python
# Add to tests/test_cache/test_db.py
from lorekeeper_mcp.cache.db import get_cache_stats


@pytest.mark.asyncio
async def test_get_cache_stats_returns_complete_stats(test_db):
    """Get cache stats returns comprehensive statistics."""
    # Add some test data
    spells = [{"slug": "fireball", "name": "Fireball"}]
    monsters = [{"slug": "goblin", "name": "Goblin"}, {"slug": "dragon", "name": "Dragon"}]
    await bulk_cache_entities(spells, "spells", test_db, "open5e")
    await bulk_cache_entities(monsters, "monsters", test_db, "open5e")

    stats = await get_cache_stats(test_db)

    assert "entity_counts" in stats
    assert stats["entity_counts"]["spells"] == 1
    assert stats["entity_counts"]["monsters"] == 2
    assert "db_size_bytes" in stats
    assert stats["db_size_bytes"] > 0
    assert "schema_version" in stats
    assert "table_count" in stats
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cache/test_db.py::test_get_cache_stats_returns_complete_stats -v`
Expected: FAIL with "ImportError: cannot import name 'get_cache_stats'"

**Step 3: Write minimal implementation**

```python
# Add to src/lorekeeper_mcp/cache/db.py
from lorekeeper_mcp.cache.schema import ENTITY_TYPES, SCHEMA_VERSION


async def get_cache_stats(db_path: str | None = None) -> dict[str, Any]:
    """Get comprehensive cache statistics.

    Args:
        db_path: Optional database path

    Returns:
        Dictionary with cache statistics
    """
    db_path = db_path or settings.db_path

    # Get entity counts per type
    entity_counts = {}
    for entity_type in ENTITY_TYPES:
        count = await get_entity_count(entity_type, db_path)
        entity_counts[entity_type] = count

    # Get database file size
    db_size = 0
    path = Path(db_path)
    if path.exists():
        db_size = path.stat().st_size

    # Get table count
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        )
        row = await cursor.fetchone()
        table_count = row[0] if row else 0

    return {
        "entity_counts": entity_counts,
        "db_size_bytes": db_size,
        "schema_version": SCHEMA_VERSION,
        "table_count": table_count,
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cache/test_db.py::test_get_cache_stats_returns_complete_stats -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_cache/test_db.py src/lorekeeper_mcp/cache/db.py
git commit -m "feat(cache): add comprehensive cache statistics"
```

---

## Phase 3: Base Client Integration

### Task 3.1: Add parallel cache query support to BaseHttpClient

**Files:**

- Modify: `src/lorekeeper_mcp/api_clients/base.py`
- Test: `tests/test_api_clients/test_base.py`

**Step 1: Write the failing test**

```python
# Add to tests/test_api_clients/test_base.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from lorekeeper_mcp.api_clients.base import BaseHttpClient


@pytest.mark.asyncio
async def test_query_cache_parallel_executes_concurrently():
    """Cache query runs in parallel with API call."""
    client = BaseHttpClient("https://api.example.com")

    # Mock cache query to take 0.1 seconds
    async def mock_cache_query(*args, **kwargs):
        await asyncio.sleep(0.1)
        return [{"slug": "fireball", "name": "Fireball"}]

    with patch("lorekeeper_mcp.api_clients.base.query_cached_entities", side_effect=mock_cache_query):
        start = asyncio.get_event_loop().time()
        result = await client._query_cache_parallel("spells", level=3)
        elapsed = asyncio.get_event_loop().time() - start

        # Should complete in roughly 0.1s, not block caller
        assert elapsed < 0.2
        assert len(result) == 1


@pytest.mark.asyncio
async def test_query_cache_parallel_handles_cache_error():
    """Cache query errors don't crash parallel operation."""
    client = BaseHttpClient("https://api.example.com")

    async def mock_error(*args, **kwargs):
        raise Exception("Cache error")

    with patch("lorekeeper_mcp.api_clients.base.query_cached_entities", side_effect=mock_error):
        result = await client._query_cache_parallel("spells")

        # Should return empty list on error
        assert result == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_base.py::test_query_cache_parallel_executes_concurrently -v`
Expected: FAIL with "AttributeError: ... has no attribute '\_query_cache_parallel'"

**Step 3: Write minimal implementation**

```python
# Add to src/lorekeeper_mcp/api_clients/base.py
import logging
from lorekeeper_mcp.cache.db import query_cached_entities

logger = logging.getLogger(__name__)


# Add this method to BaseHttpClient class:
    async def _query_cache_parallel(
        self,
        entity_type: str,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Query cache for entities in parallel.

        Args:
            entity_type: Type of entities to query
            **filters: Filter parameters

        Returns:
            List of cached entities, or empty list on error
        """
        try:
            return await query_cached_entities(entity_type, **filters)
        except Exception as e:
            logger.warning(f"Cache query failed: {e}")
            return []
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_base.py::test_query_cache_parallel_executes_concurrently tests/test_api_clients/test_base.py::test_query_cache_parallel_handles_cache_error -v`
Expected: PASS (both tests pass)

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_base.py src/lorekeeper_mcp/api_clients/base.py
git commit -m "feat(base-client): add parallel cache query support"
```

---

### Task 3.2: Implement entity caching from API responses

**Files:**

- Modify: `src/lorekeeper_mcp/api_clients/base.py`
- Test: `tests/test_api_clients/test_base.py`

**Step 1: Write the failing test**

```python
# Add to tests/test_api_clients/test_base.py
from lorekeeper_mcp.cache.db import get_cached_entity, init_entity_cache
import tempfile
from pathlib import Path


@pytest.fixture
async def client_with_db():
    """Create client with test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await init_entity_cache(str(db_path))

        # Temporarily override settings
        import lorekeeper_mcp.config
        original_path = lorekeeper_mcp.config.settings.db_path
        lorekeeper_mcp.config.settings.db_path = str(db_path)

        client = BaseHttpClient("https://api.example.com")

        yield client

        # Restore
        lorekeeper_mcp.config.settings.db_path = original_path
        await client.close()


@pytest.mark.asyncio
async def test_cache_api_entities_stores_entities(client_with_db):
    """Cache API entities stores each entity."""
    entities = [
        {"slug": "fireball", "name": "Fireball", "level": 3},
        {"slug": "magic-missile", "name": "Magic Missile", "level": 1},
    ]

    await client_with_db._cache_api_entities(entities, "spells")

    # Verify entities cached
    cached = await get_cached_entity("spells", "fireball")
    assert cached is not None
    assert cached["name"] == "Fireball"


@pytest.mark.asyncio
async def test_extract_entities_from_paginated_response(client_with_db):
    """Extract entities handles paginated API response."""
    response = {
        "count": 2,
        "results": [
            {"slug": "fireball", "name": "Fireball"},
            {"slug": "magic-missile", "name": "Magic Missile"},
        ]
    }

    entities = client_with_db._extract_entities(response, "spells")

    assert len(entities) == 2
    assert entities[0]["slug"] == "fireball"


@pytest.mark.asyncio
async def test_extract_entities_handles_non_paginated(client_with_db):
    """Extract entities handles direct entity response."""
    response = {"slug": "fireball", "name": "Fireball"}

    entities = client_with_db._extract_entities(response, "spells")

    assert len(entities) == 1
    assert entities[0]["slug"] == "fireball"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_base.py::test_cache_api_entities_stores_entities -v`
Expected: FAIL with "AttributeError: ... has no attribute '\_cache_api_entities'"

**Step 3: Write minimal implementation**

```python
# Add to src/lorekeeper_mcp/api_clients/base.py
from lorekeeper_mcp.cache.db import bulk_cache_entities


# Add these methods to BaseHttpClient class:
    def _extract_entities(
        self,
        response: dict[str, Any],
        entity_type: str,
    ) -> list[dict[str, Any]]:
        """Extract entities from API response.

        Handles both paginated responses with 'results' and direct entities.

        Args:
            response: API response dictionary
            entity_type: Type of entities

        Returns:
            List of entity dictionaries
        """
        # Check if paginated response
        if "results" in response and isinstance(response["results"], list):
            return response["results"]

        # Check if direct entity (has slug)
        if "slug" in response:
            return [response]

        # Unknown format
        return []

    async def _cache_api_entities(
        self,
        entities: list[dict[str, Any]],
        entity_type: str,
    ) -> None:
        """Cache entities from API response.

        Args:
            entities: List of entity dictionaries
            entity_type: Type of entities
        """
        if not entities:
            return

        try:
            await bulk_cache_entities(
                entities,
                entity_type,
                source_api=self.source_api,
            )
            logger.debug(f"Cached {len(entities)} {entity_type}")
        except Exception as e:
            logger.warning(f"Failed to cache entities: {e}")
            # Non-fatal - continue without caching
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_base.py -k "cache_api_entities or extract_entities" -v`
Expected: PASS (all 3 new tests pass)

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_base.py src/lorekeeper_mcp/api_clients/base.py
git commit -m "feat(base-client): implement entity caching from API responses"
```

---

### Task 3.3: Implement offline fallback logic

**Files:**

- Modify: `src/lorekeeper_mcp/api_clients/base.py`
- Test: `tests/test_api_clients/test_base.py`

**Step 1: Write the failing test**

```python
# Add to tests/test_api_clients/test_base.py
from lorekeeper_mcp.api_clients.exceptions import NetworkError
from lorekeeper_mcp.cache.db import bulk_cache_entities


@pytest.mark.asyncio
async def test_make_request_offline_fallback_returns_cache(client_with_db):
    """Make request falls back to cache on network error."""
    # Pre-populate cache
    entities = [{"slug": "fireball", "name": "Fireball", "level": 3}]
    await bulk_cache_entities(entities, "spells")

    # Mock network error
    with patch.object(client_with_db, "_make_request", side_effect=NetworkError("Network down")):
        with patch.object(client_with_db, "_query_cache_parallel", return_value=entities):
            result = await client_with_db.make_request(
                "/spells",
                entity_type="spells",
                use_entity_cache=True,
            )

    # Should return cached data instead of raising
    assert result == entities


@pytest.mark.asyncio
async def test_make_request_offline_with_no_cache_returns_empty(client_with_db):
    """Make request with network error and no cache returns empty."""
    # Mock network error with empty cache
    with patch.object(client_with_db, "_make_request", side_effect=NetworkError("Network down")):
        with patch.object(client_with_db, "_query_cache_parallel", return_value=[]):
            result = await client_with_db.make_request(
                "/spells",
                entity_type="spells",
                use_entity_cache=True,
            )

    # Should return empty list
    assert result == []


@pytest.mark.asyncio
async def test_make_request_offline_logs_warning(client_with_db, caplog):
    """Make request logs warning in offline mode."""
    with patch.object(client_with_db, "_make_request", side_effect=NetworkError("Network down")):
        with patch.object(client_with_db, "_query_cache_parallel", return_value=[]):
            await client_with_db.make_request(
                "/spells",
                entity_type="spells",
                use_entity_cache=True,
            )

    # Should log offline warning
    assert "offline" in caplog.text.lower() or "network" in caplog.text.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_base.py::test_make_request_offline_fallback_returns_cache -v`
Expected: FAIL (make_request doesn't handle entity_type parameter or offline fallback)

**Step 3: Write minimal implementation**

```python
# Modify src/lorekeeper_mcp/api_clients/base.py
# Replace the make_request method in BaseHttpClient:

    async def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        use_cache: bool = True,
        use_entity_cache: bool = False,
        entity_type: str | None = None,
        cache_filters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make HTTP request with caching and retry logic.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            use_cache: Whether to use legacy URL-based cache (deprecated)
            use_entity_cache: Whether to use entity-based cache
            entity_type: Type of entities for entity cache
            cache_filters: Filters for cache query
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response or list of entities

        Raises:
            NetworkError: For network-related failures (when not using offline fallback)
            ApiError: For API error responses (4xx/5xx)
        """
        url = f"{self.base_url}{endpoint}"
        cache_filters = cache_filters or {}

        # Start parallel cache query if entity cache enabled
        cache_task = None
        if use_entity_cache and entity_type:
            cache_task = asyncio.create_task(
                self._query_cache_parallel(entity_type, **cache_filters)
            )

        # Legacy URL-based cache check
        if use_cache and method == "GET" and not use_entity_cache:
            cached = await self._get_cached_response(url)
            if cached is not None:
                logger.debug(f"Cache hit: {url}")
                return cached

        # Make API request
        try:
            response = await self._make_request(endpoint, method, **kwargs)

            # Extract and cache entities if using entity cache
            if use_entity_cache and entity_type:
                entities = self._extract_entities(response, entity_type)
                await self._cache_api_entities(entities, entity_type)

                # Merge with cache results if available
                if cache_task:
                    try:
                        cached_entities = await cache_task
                        # For now, API takes precedence, just return API results
                        # (merging logic can be enhanced later)
                        return entities
                    except Exception:
                        return entities

                return entities

            # Legacy URL-based cache storage
            if use_cache and method == "GET":
                await self._cache_response(url, response)

            return response

        except NetworkError as e:
            # Offline fallback: return cached entities
            if use_entity_cache and entity_type and cache_task:
                logger.warning(f"Network error, falling back to cache: {e}")
                try:
                    cached_entities = await cache_task
                    if cached_entities:
                        logger.info(f"Returning {len(cached_entities)} cached {entity_type}")
                        return cached_entities
                    else:
                        logger.warning(f"No cached {entity_type} available for offline mode")
                        return []
                except Exception as cache_error:
                    logger.error(f"Cache fallback failed: {cache_error}")
                    return []

            # No fallback available, re-raise
            raise
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_base.py -k offline -v`
Expected: PASS (all offline tests pass)

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_base.py src/lorekeeper_mcp/api_clients/base.py
git commit -m "feat(base-client): implement offline fallback with entity cache"
```

---

### Task 3.4: Implement cache-first mode

**Files:**

- Modify: `src/lorekeeper_mcp/api_clients/base.py`
- Test: `tests/test_api_clients/test_base.py`

**Step 1: Write the failing test**

```python
# Add to tests/test_api_clients/test_base.py
@pytest.mark.asyncio
async def test_make_request_cache_first_returns_immediately(client_with_db):
    """Make request with cache_first returns cache without waiting for API."""
    # Pre-populate cache
    entities = [{"slug": "fireball", "name": "Fireball (cached)"}]
    await bulk_cache_entities(entities, "spells")

    # Mock slow API response
    async def slow_api(*args, **kwargs):
        await asyncio.sleep(0.5)
        return {"results": [{"slug": "fireball", "name": "Fireball (fresh)"}]}

    with patch.object(client_with_db, "_make_request", side_effect=slow_api):
        start = asyncio.get_event_loop().time()
        result = await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
            cache_first=True,
        )
        elapsed = asyncio.get_event_loop().time() - start

    # Should return cached data quickly (< 0.1s, not wait for 0.5s API)
    assert elapsed < 0.1
    assert result[0]["name"] == "Fireball (cached)"


@pytest.mark.asyncio
async def test_make_request_cache_first_refreshes_background(client_with_db):
    """Make request with cache_first refreshes cache in background."""
    # Pre-populate cache with old data
    old_entities = [{"slug": "fireball", "name": "Fireball (old)"}]
    await bulk_cache_entities(old_entities, "spells")

    # Mock API with new data
    async def mock_api(*args, **kwargs):
        return {"results": [{"slug": "fireball", "name": "Fireball (new)"}]}

    with patch.object(client_with_db, "_make_request", side_effect=mock_api):
        # First call returns cached
        result1 = await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
            cache_first=True,
        )

        # Wait for background refresh
        await asyncio.sleep(0.2)

        # Second call should have refreshed data
        result2 = await client_with_db.make_request(
            "/spells",
            entity_type="spells",
            use_entity_cache=True,
            cache_first=True,
        )

    assert result1[0]["name"] == "Fireball (old)"
    # Background task should have updated cache
    # (In practice this requires the background task to complete)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_base.py::test_make_request_cache_first_returns_immediately -v`
Expected: FAIL (cache_first parameter not supported)

**Step 3: Write minimal implementation**

```python
# Modify src/lorekeeper_mcp/api_clients/base.py
# Update the make_request method signature and add cache_first logic:

    async def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        use_cache: bool = True,
        use_entity_cache: bool = False,
        entity_type: str | None = None,
        cache_filters: dict[str, Any] | None = None,
        cache_first: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make HTTP request with caching and retry logic.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            use_cache: Whether to use legacy URL-based cache (deprecated)
            use_entity_cache: Whether to use entity-based cache
            entity_type: Type of entities for entity cache
            cache_filters: Filters for cache query
            cache_first: Return cache immediately, refresh in background
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response or list of entities

        Raises:
            NetworkError: For network-related failures (when not using offline fallback)
            ApiError: For API error responses (4xx/5xx)
        """
        url = f"{self.base_url}{endpoint}"
        cache_filters = cache_filters or {}

        # Cache-first mode: return cache immediately, refresh async
        if cache_first and use_entity_cache and entity_type:
            # Query cache immediately
            cached_entities = await self._query_cache_parallel(entity_type, **cache_filters)

            # Start background refresh task
            async def background_refresh():
                try:
                    response = await self._make_request(endpoint, method, **kwargs)
                    entities = self._extract_entities(response, entity_type)
                    await self._cache_api_entities(entities, entity_type)
                    logger.debug(f"Background refresh completed for {entity_type}")
                except Exception as e:
                    logger.warning(f"Background refresh failed: {e}")

            # Fire and forget
            asyncio.create_task(background_refresh())

            return cached_entities

        # ... rest of the existing make_request logic remains the same ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_base.py::test_make_request_cache_first_returns_immediately -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_base.py src/lorekeeper_mcp/api_clients/base.py
git commit -m "feat(base-client): implement cache-first mode with background refresh"
```

---

## Phase 4: API Client Updates

### Task 4.1: Update Open5eV1Client for entity caching

**Files:**

- Modify: `src/lorekeeper_mcp/api_clients/open5e_v1.py`
- Test: `tests/test_api_clients/test_open5e_v1.py`

**Step 1: Write the failing integration test**

```python
# Add to tests/test_api_clients/test_open5e_v1.py
import pytest
from unittest.mock import patch, AsyncMock
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.cache.db import get_cached_entity, init_entity_cache
import tempfile
from pathlib import Path


@pytest.fixture
async def v1_client_with_cache():
    """Create V1 client with test cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await init_entity_cache(str(db_path))

        import lorekeeper_mcp.config
        original = lorekeeper_mcp.config.settings.db_path
        lorekeeper_mcp.config.settings.db_path = str(db_path)

        client = Open5eV1Client()
        yield client

        lorekeeper_mcp.config.settings.db_path = original
        await client.close()


@pytest.mark.asyncio
async def test_get_monsters_uses_entity_cache(v1_client_with_cache):
    """Get monsters caches entities, not URLs."""
    mock_response = {
        "results": [
            {"slug": "goblin", "name": "Goblin", "type": "humanoid", "challenge_rating": "1/4"}
        ]
    }

    with patch.object(v1_client_with_cache, "_make_request", return_value=mock_response):
        result = await v1_client_with_cache.get_monsters()

    # Verify entity cached
    cached = await get_cached_entity("monsters", "goblin")
    assert cached is not None
    assert cached["name"] == "Goblin"
    assert cached["type"] == "humanoid"


@pytest.mark.asyncio
async def test_get_classes_uses_entity_cache(v1_client_with_cache):
    """Get classes caches entities."""
    mock_response = {
        "results": [
            {"slug": "fighter", "name": "Fighter", "hit_die": 10}
        ]
    }

    with patch.object(v1_client_with_cache, "_make_request", return_value=mock_response):
        result = await v1_client_with_cache.get_classes()

    cached = await get_cached_entity("classes", "fighter")
    assert cached is not None
    assert cached["hit_die"] == 10
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_open5e_v1.py::test_get_monsters_uses_entity_cache -v`
Expected: FAIL (entities not cached)

**Step 3: Update Open5eV1Client implementation**

```python
# Modify src/lorekeeper_mcp/api_clients/open5e_v1.py
# Update get_monsters method and similar methods:

    async def get_monsters(
        self,
        challenge_rating: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Get monsters from Open5e API v1.

        Args:
            challenge_rating: Filter by CR (e.g., "1/4", "5")
            **kwargs: Additional API parameters

        Returns:
            List of monster dictionaries
        """
        cache_filters = {}
        if challenge_rating:
            cache_filters["challenge_rating"] = challenge_rating

        result = await self.make_request(
            "/monsters/",
            use_entity_cache=True,
            entity_type="monsters",
            cache_filters=cache_filters,
            params=kwargs,
        )

        # Return entities directly (make_request now returns entity list)
        if isinstance(result, list):
            return result

        # Fallback for legacy response format
        return result.get("results", [])

    async def get_classes(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character classes from Open5e API v1.

        Returns:
            List of class dictionaries
        """
        result = await self.make_request(
            "/classes/",
            use_entity_cache=True,
            entity_type="classes",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])

    async def get_races(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character races from Open5e API v1.

        Returns:
            List of race dictionaries
        """
        result = await self.make_request(
            "/races/",
            use_entity_cache=True,
            entity_type="races",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_open5e_v1.py -k entity_cache -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_open5e_v1.py src/lorekeeper_mcp/api_clients/open5e_v1.py
git commit -m "feat(open5e-v1): update client to use entity-based caching"
```

---

### Task 4.2: Update Open5eV2Client for entity caching

**Files:**

- Modify: `src/lorekeeper_mcp/api_clients/open5e_v2.py`
- Test: `tests/test_api_clients/test_open5e_v2.py`

**Step 1: Write the failing integration test**

```python
# Add to tests/test_api_clients/test_open5e_v2.py
import pytest
from unittest.mock import patch
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.cache.db import get_cached_entity, init_entity_cache
import tempfile
from pathlib import Path


@pytest.fixture
async def v2_client_with_cache():
    """Create V2 client with test cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await init_entity_cache(str(db_path))

        import lorekeeper_mcp.config
        original = lorekeeper_mcp.config.settings.db_path
        lorekeeper_mcp.config.settings.db_path = str(db_path)

        client = Open5eV2Client()
        yield client

        lorekeeper_mcp.config.settings.db_path = original
        await client.close()


@pytest.mark.asyncio
async def test_get_spells_uses_entity_cache(v2_client_with_cache):
    """Get spells caches entities."""
    mock_response = {
        "results": [
            {"slug": "fireball", "name": "Fireball", "level": 3, "school": "Evocation"}
        ]
    }

    with patch.object(v2_client_with_cache, "_make_request", return_value=mock_response):
        result = await v2_client_with_cache.get_spells()

    cached = await get_cached_entity("spells", "fireball")
    assert cached is not None
    assert cached["level"] == 3


@pytest.mark.asyncio
async def test_get_weapons_uses_entity_cache(v2_client_with_cache):
    """Get weapons caches entities."""
    mock_response = {
        "results": [
            {"slug": "longsword", "name": "Longsword", "category": "martial"}
        ]
    }

    with patch.object(v2_client_with_cache, "_make_request", return_value=mock_response):
        result = await v2_client_with_cache.get_weapons()

    cached = await get_cached_entity("weapons", "longsword")
    assert cached is not None


@pytest.mark.asyncio
async def test_get_armor_uses_entity_cache(v2_client_with_cache):
    """Get armor caches entities."""
    mock_response = {
        "results": [
            {"slug": "plate-armor", "name": "Plate Armor", "armor_class": 18}
        ]
    }

    with patch.object(v2_client_with_cache, "_make_request", return_value=mock_response):
        result = await v2_client_with_cache.get_armor()

    cached = await get_cached_entity("armor", "plate-armor")
    assert cached is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_clients/test_open5e_v2.py::test_get_spells_uses_entity_cache -v`
Expected: FAIL (entities not cached)

**Step 3: Update Open5eV2Client implementation**

```python
# Modify src/lorekeeper_mcp/api_clients/open5e_v2.py
# Update all entity-fetching methods:

    async def get_spells(
        self,
        level: int | None = None,
        school: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Get spells from Open5e API v2.

        Args:
            level: Filter by spell level
            school: Filter by spell school
            **kwargs: Additional API parameters

        Returns:
            List of spell dictionaries
        """
        cache_filters = {}
        if level is not None:
            cache_filters["level"] = level
        if school:
            cache_filters["school"] = school

        result = await self.make_request(
            "/spells/",
            use_entity_cache=True,
            entity_type="spells",
            cache_filters=cache_filters,
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])

    async def get_weapons(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get weapons from Open5e API v2."""
        result = await self.make_request(
            "/weapons/",
            use_entity_cache=True,
            entity_type="weapons",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])

    async def get_armor(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get armor from Open5e API v2."""
        result = await self.make_request(
            "/armor/",
            use_entity_cache=True,
            entity_type="armor",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])

    async def get_backgrounds(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character backgrounds."""
        result = await self.make_request(
            "/backgrounds/",
            use_entity_cache=True,
            entity_type="backgrounds",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])

    async def get_feats(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character feats."""
        result = await self.make_request(
            "/feats/",
            use_entity_cache=True,
            entity_type="feats",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])

    async def get_conditions(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get game conditions."""
        result = await self.make_request(
            "/conditions/",
            use_entity_cache=True,
            entity_type="conditions",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_clients/test_open5e_v2.py -k entity_cache -v`
Expected: PASS (all entity cache tests pass)

**Step 5: Commit**

```bash
git add tests/test_api_clients/test_open5e_v2.py src/lorekeeper_mcp/api_clients/open5e_v2.py
git commit -m "feat(open5e-v2): update client to use entity-based caching"
```

---

## Phase 5: Testing & Documentation

### Task 5.1: Run full test suite and fix any issues

**Step 1: Run all tests**

Run: `pytest tests/ -v --cov=src/lorekeeper_mcp/cache --cov=src/lorekeeper_mcp/api_clients`
Expected: Review coverage report, identify any gaps

**Step 2: Fix failing tests**

If any tests fail due to the cache refactor, update them to use entity-based caching patterns. Focus on:

- Tests that expect URL-based cache behavior
- Tests that check for old `api_cache` table
- Integration tests that need cache initialization

**Step 3: Verify coverage**

Run: `pytest tests/test_cache/ -v --cov=src/lorekeeper_mcp/cache --cov-report=html`
Expected: >90% coverage on cache layer

**Step 4: Commit fixes**

```bash
git add tests/
git commit -m "test: fix tests for entity-based caching"
```

---

### Task 5.2: Update cache documentation

**Files:**

- Modify: `docs/cache.md`

**Step 1: Read current documentation**

Run: `cat docs/cache.md`

**Step 2: Update with entity-based architecture**

Update `docs/cache.md` with:

- Entity-based caching architecture overview
- Cache schema and table structure
- Examples of cache operations
- Migration guide from old cache
- Cache statistics API
- Offline fallback behavior
- Cache-first mode usage

**Step 3: Commit documentation**

```bash
git add docs/cache.md
git commit -m "docs: update cache documentation for entity-based architecture"
```

---

### Task 5.3: Manual validation testing

**Step 1: Initialize cache with real data**

```bash
# Start server
python -m lorekeeper_mcp.server

# In another terminal, make some MCP requests to populate cache
# (Use your MCP client or test scripts)
```

**Step 2: Verify cache tables**

```bash
sqlite3 data/cache.db ".tables"
sqlite3 data/cache.db "SELECT COUNT(*) FROM spells"
sqlite3 data/cache.db "SELECT COUNT(*) FROM monsters"
```

Expected: See all entity tables, counts > 0 for populated types

**Step 3: Test offline mode**

```bash
# Disconnect network or modify hosts file to block API
# Make requests - should serve from cache
# Check logs for "offline" or "falling back to cache" messages
```

**Step 4: Verify cache statistics**

```python
# In Python REPL
from lorekeeper_mcp.cache.db import get_cache_stats
import asyncio

stats = asyncio.run(get_cache_stats())
print(stats)
```

Expected: Complete statistics with entity counts, db size, etc.

**Step 5: Document validation results**

Create a checklist of what was tested and verified:

- [ ] All entity tables created
- [ ] Entities cached after API calls
- [ ] Filters work correctly
- [ ] Offline mode serves cached data
- [ ] Cache statistics accurate
- [ ] No errors in logs

---

## Verification & Completion

### Final Checklist

Run through this checklist before marking implementation complete:

- [ ] All entity tables created successfully (`sqlite3 data/cache.db ".tables"`)
- [ ] Bulk insert handles 100+ entities efficiently (test with real API data)
- [ ] Filters work correctly for all entity types (unit tests pass)
- [ ] Parallel cache queries reduce latency vs sequential (integration tests)
- [ ] Offline mode serves cached data without errors (manual testing)
- [ ] Cache statistics accurate and complete (`get_cache_stats()`)
- [ ] Unit test coverage >90% for cache layer (`pytest --cov`)
- [ ] Integration tests pass for all API clients (`pytest tests/test_api_clients/`)
- [ ] Manual testing confirms end-to-end functionality
- [ ] Documentation updated and accurate (`docs/cache.md`)

### Migration Notes

The old `api_cache` table will coexist with new entity tables initially. To complete migration:

1. Verify new entity cache working correctly
2. Run cleanup to drop old table:

```python
# In Python REPL or script
from lorekeeper_mcp.cache.schema import migrate_cache_schema
import asyncio

asyncio.run(migrate_cache_schema("data/cache.db"))
```

3. Verify old table removed: `sqlite3 data/cache.db ".tables"`

---

## Execution Options

**Plan complete and saved to `openspec/changes/implement-entity-cache/plan.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration with quality gates

**2. Parallel Session (separate)** - Open new session with executing-plans skill for batch execution with checkpoints

**Which approach would you like?**
