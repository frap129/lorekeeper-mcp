# Database Cache Documentation

This document provides detailed information about the SQLite-based caching system used in LoreKeeper MCP. The system now uses an **entity-based architecture** for storing D&D content with infinite TTL, replacing the previous URL-based cache approach.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Database Schema](#database-schema)
- [Cache Operations](#cache-operations)
- [Entity-Based Caching](#entity-based-caching)
- [Performance Optimizations](#performance-optimizations)
- [Configuration](#configuration)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Migration from Legacy Cache](#migration-from-legacy-cache)
- [Troubleshooting](#troubleshooting)

## Overview

The cache layer provides persistent storage for API responses and entity data, reducing external API calls and improving response times. It uses SQLite with WAL mode for efficient concurrent access.

### Key Features

- **Entity-Based Storage**: Separate type-specific tables for spells, monsters, weapons, armor, classes, races, backgrounds, feats, conditions, and rules
- **Infinite TTL for Entities**: Valid entity data is never expired; only explicitly updated or deleted
- **Indexed Filtering**: Support for filtering entities by type-specific indexed fields (level, school, CR, type, etc.)
- **Bulk Operations**: Efficient batch insert/update operations for processing API responses
- **Legacy Compatibility**: Maintains old URL-based cache for backward compatibility
- **Source Tracking**: Records which API provided cached data
- **Performance Optimized**: WAL mode, strategic indexes, and efficient query patterns
- **Observability**: Comprehensive cache statistics and entity counts per type

### Cache Strategy

The system uses a **multi-layered caching strategy**:

1. **Entity Cache First**: Check entity-based cache for D&D content (spells, monsters, etc.)
2. **Entity Hit**: Return cached entity data (no expiration)
3. **Entity Miss**: Fetch from API, bulk cache with related entities, return data
4. **Legacy Cache**: URL-based cache for other API responses with TTL support
5. **Offline Fallback**: Serve cached entities when API is unavailable

## Architecture

The caching system is organized into two complementary layers:

### Entity Cache Layer (Primary)
- **Purpose**: Store immutable D&D entities with permanent lifetime
- **Scope**: Spells, monsters, weapons, armor, classes, races, backgrounds, feats, conditions, rules
- **Strategy**: Cache-and-keep; no expiration for valid data
- **Updates**: Preserve creation time, update modification time on new API calls

### Legacy API Cache Layer (Compatibility)
- **Purpose**: Store generic API responses with expiration
- **Scope**: Any other API responses or frequently-changing data
- **Strategy**: TTL-based expiration with automatic cleanup
- **Updates**: Each request overwrites previous entry with new TTL

## Database Schema

### Entity-Based Tables

Each entity type has its own dedicated table with the following structure:

```sql
CREATE TABLE {entity_type} (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    source_api TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    -- Type-specific indexed fields vary by entity type
    [field1] [TYPE],
    [field2] [TYPE],
    ...
);
```

#### Supported Entity Types

| Entity Type | Indexed Fields | Purpose |
|------------|---|---------|
| `spells` | `level`, `school`, `concentration`, `ritual` | D&D spells indexed by level and school |
| `monsters` | `challenge_rating`, `type`, `size` | Creatures indexed by CR and type |
| `weapons` | `category`, `damage_type` | Equipment indexed by category |
| `armor` | `category`, `armor_class` | Armor indexed by type and AC |
| `classes` | `hit_die` | Character classes |
| `races` | `size` | Player races |
| `backgrounds` | (none) | Character backgrounds |
| `feats` | (none) | Character feats |
| `conditions` | (none) | Game conditions |
| `rules` | `parent` | Rule sections and text |
| `rule_sections` | `parent` | Rule section hierarchy |

#### Column Descriptions

| Column | Type | Description |
|--------|------|-------------|
| `slug` | TEXT | Unique identifier/primary key for the entity |
| `name` | TEXT | Human-readable entity name |
| `data` | TEXT | Complete entity data as JSON blob |
| `source_api` | TEXT | Source API identifier (open5e, dnd5e) |
| `created_at` | REAL | Unix timestamp when entity was first cached (never changes) |
| `updated_at` | REAL | Unix timestamp of last cache update |
| `{indexed_field}` | VARIES | Type-specific indexed field for filtering |

#### Example: Spells Table

```sql
CREATE TABLE spells (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    source_api TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    level INTEGER,
    school TEXT,
    concentration BOOLEAN,
    ritual BOOLEAN
);
```

#### Example: Monsters Table

```sql
CREATE TABLE monsters (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    source_api TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    challenge_rating REAL,
    type TEXT,
    size TEXT
);
```

### Legacy Table: `api_cache`

For backward compatibility, the system maintains a legacy URL-based cache table:

```sql
CREATE TABLE api_cache (
    cache_key TEXT PRIMARY KEY,
    response_data TEXT NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    content_type TEXT NOT NULL,
    source_api TEXT NOT NULL
);
```

| Column | Type | Description |
|--------|------|-------------|
| `cache_key` | TEXT | Unique identifier for cached data |
| `response_data` | TEXT | JSON-encoded API response data |
| `created_at` | REAL | Unix timestamp when entry was created |
| `expires_at` | REAL | Unix timestamp when entry expires |
| `content_type` | TEXT | Type of content (spell, monster, etc.) |
| `source_api` | TEXT | API that provided the data (open5e, dnd5e) |

### Indexes

#### Entity Table Indexes

```sql
-- Spell indexes for filtering by level and school
CREATE INDEX idx_spells_level ON spells(level);
CREATE INDEX idx_spells_school ON spells(school);
CREATE INDEX idx_spells_concentration ON spells(concentration);
CREATE INDEX idx_spells_ritual ON spells(ritual);

-- Monster indexes for filtering by CR and type
CREATE INDEX idx_monsters_challenge_rating ON monsters(challenge_rating);
CREATE INDEX idx_monsters_type ON monsters(type);
CREATE INDEX idx_monsters_size ON monsters(size);

-- Weapon and armor indexes
CREATE INDEX idx_weapons_category ON weapons(category);
CREATE INDEX idx_weapons_damage_type ON weapons(damage_type);
CREATE INDEX idx_armor_category ON armor(category);
CREATE INDEX idx_armor_armor_class ON armor(armor_class);
```

#### Legacy Indexes

```sql
-- For efficient cleanup of expired entries
CREATE INDEX idx_expires_at ON api_cache(expires_at);

-- For content-type based queries
CREATE INDEX idx_content_type ON api_cache(content_type);
```

### Database Configuration

```sql
-- Enable WAL mode for better concurrent access
PRAGMA journal_mode=WAL;

-- Optimize for cache workload
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=memory;
```

## Cache Operations

### Entity-Based Cache Operations

#### Bulk Cache Entities

The most efficient way to populate the cache is through bulk operations, typically done after fetching a batch of entities from an API:

```python
async def bulk_cache_entities(
    entities: list[dict[str, Any]],
    entity_type: str,
    source_api: str = "unknown",
) -> int:
    """Bulk insert or update entities in cache.

    Args:
        entities: List of entity dictionaries with 'slug' and 'name' fields
        entity_type: Type of entities (spells, monsters, weapons, etc.)
        source_api: Source API identifier (open5e, dnd5e, etc.)

    Returns:
        Number of entities processed

    Raises:
        ValueError: If entity_type is invalid
    """
    # Example: Cache 50 spells from open5e API
    from lorekeeper_mcp.cache.db import bulk_cache_entities

    spells = [
        {
            "slug": "fireball",
            "name": "Fireball",
            "level": 3,
            "school": "Evocation",
            "concentration": False,
            "ritual": False,
            # ... other spell data
        },
        # ... more spells
    ]

    count = await bulk_cache_entities(spells, "spells", source_api="open5e")
    print(f"Cached {count} spells")
```

**Key Features:**
- Inserts all entities in a single transaction for efficiency
- Preserves `created_at` timestamp for existing entities
- Updates `updated_at` to current time for new or modified entities
- Extracts indexed fields for each entity type automatically
- Handles duplicate slugs gracefully (updates existing entries)

#### Get Single Cached Entity

```python
async def get_cached_entity(
    entity_type: str,
    slug: str,
) -> dict[str, Any] | None:
    """Retrieve a single cached entity by slug.

    Args:
        entity_type: Type of entity (spells, monsters, etc.)
        slug: Entity slug (unique identifier)

    Returns:
        Complete entity data dictionary or None if not found

    Raises:
        ValueError: If entity_type is invalid
    """
    from lorekeeper_mcp.cache.db import get_cached_entity

    # Example: Get the fireball spell
    spell = await get_cached_entity("spells", "fireball")
    if spell:
        print(f"Found {spell['name']} at level {spell['level']}")
    else:
        print("Spell not cached - fetch from API")
```

**Key Features:**
- O(1) lookup using slug as primary key
- Returns complete entity data (slug + name + indexed fields + full JSON)
- No expiration checking; valid entities last forever
- Returns None if not found (no error thrown)

#### Query Cached Entities with Filters

```python
async def query_cached_entities(
    entity_type: str,
    **filters: Any,
) -> list[dict[str, Any]]:
    """Query cached entities with optional filters.

    Args:
        entity_type: Type of entities to query
        **filters: Field filters using indexed fields
            - For spells: level, school, concentration, ritual
            - For monsters: challenge_rating, type, size
            - For weapons: category, damage_type
            - For armor: category, armor_class

    Returns:
        List of matching entity dictionaries (empty list if no matches)

    Raises:
        ValueError: If entity_type or filter fields are invalid
    """
    from lorekeeper_mcp.cache.db import query_cached_entities

    # Example 1: Find all 3rd level evocation spells
    spells = await query_cached_entities("spells", level=3, school="Evocation")
    print(f"Found {len(spells)} matching spells")

    # Example 2: Find all CR 5 undead monsters
    monsters = await query_cached_entities("monsters",
                                          challenge_rating=5.0,
                                          type="undead")
    print(f"Found {len(monsters)} matching monsters")

    # Example 3: Find all simple weapons
    weapons = await query_cached_entities("weapons", category="simple")
    print(f"Found {len(weapons)} simple weapons")

    # Example 4: No filters - get all cached entities of a type
    all_spells = await query_cached_entities("spells")
    print(f"Total cached spells: {len(all_spells)}")
```

**Key Features:**
- Uses database indexes on filtered fields for performance
- Supports multiple filters (AND logic)
- Returns empty list (not None) for no matches
- Validates filter fields to prevent SQL injection
- Efficient for filtering entity libraries

#### Get Entity Count

```python
async def get_entity_count(entity_type: str) -> int:
    """Get count of cached entities for a type.

    Args:
        entity_type: Type of entities to count

    Returns:
        Number of cached entities, or 0 if table doesn't exist
    """
    from lorekeeper_mcp.cache.db import get_entity_count

    spell_count = await get_entity_count("spells")
    monster_count = await get_entity_count("monsters")

    print(f"Cached: {spell_count} spells, {monster_count} monsters")
```

### Legacy API Cache Operations

For backward compatibility and non-entity API responses:

#### Get Cached Data (Legacy)

```python
async def get_cached(key: str) -> dict[str, Any] | None:
    """Retrieve cached data if not expired (URL-based cache).

    Args:
        key: Cache key to look up

    Returns:
        Cached data as dict if found and not expired, None otherwise
    """
    from lorekeeper_mcp.cache.db import get_cached

    key = "open5e:v2/spells:name=fireball"
    data = await get_cached(key)
    if data:
        print(f"Cache hit for {key}")
    else:
        print(f"Cache miss or expired for {key}")
```

#### Set Cached Data (Legacy)

```python
async def set_cached(
    key: str,
    data: dict[str, Any],
    content_type: str,
    ttl_seconds: int,
    source_api: str = "unknown",
) -> None:
    """Store data in cache with TTL (URL-based cache).

    Args:
        key: Cache key for the data
        data: Data to cache as dictionary
        content_type: Type of content (e.g., "spell", "monster")
        ttl_seconds: Time to live in seconds
        source_api: Source API identifier
    """
    from lorekeeper_mcp.cache.db import set_cached

    # Cache a response for 7 days
    await set_cached(
        key="open5e:v2/equipment",
        data=equipment_data,
        content_type="equipment",
        ttl_seconds=7 * 24 * 3600,
        source_api="open5e"
    )
```

#### Cleanup Expired Entries (Legacy)

```python
async def cleanup_expired() -> int:
    """Remove expired cache entries from the database.

    Returns:
        Number of entries that were deleted
    """
    from lorekeeper_mcp.cache.db import cleanup_expired

    deleted = await cleanup_expired()
    print(f"Cleaned up {deleted} expired entries")
```

### Cache Statistics

```python
async def get_cache_stats() -> dict[str, Any]:
    """Get comprehensive cache statistics.

    Returns:
        Dictionary with:
        - entity_counts: Count per entity type
        - db_size_bytes: Total database file size
        - schema_version: Cache schema version
        - table_count: Number of tables in database
    """
    from lorekeeper_mcp.cache.db import get_cache_stats

    stats = await get_cache_stats()
    print(f"Database size: {stats['db_size_bytes'] / 1024 / 1024:.1f} MB")
    print(f"Schema version: {stats['schema_version']}")

    for entity_type, count in stats["entity_counts"].items():
        if count > 0:
            print(f"  {entity_type}: {count} cached")
```

## Entity-Based Caching

### Core Concepts

**Entity**: A complete D&D object (spell, monster, weapon, etc.) with a unique `slug` identifier.

**TTL Strategy**: Entities use **infinite TTL**. Once cached, an entity remains valid until explicitly updated or deleted. This contrasts with the legacy API cache which expires based on TTL.

**Indexed Fields**: Each entity type has a set of indexed fields for efficient filtering (e.g., spells have `level` and `school` indexed).

**Atomic Updates**: When an entity is re-cached, its `created_at` timestamp is preserved while `updated_at` is refreshed.

### Common Patterns

#### Pattern 1: Fetch and Cache Spell List

```python
async def cache_spells_from_api():
    """Fetch spells from API and cache them."""
    from lorekeeper_mcp.cache.db import bulk_cache_entities

    # Fetch spells from open5e API
    spells = await api_client.get_spells()

    # Bulk cache all spells
    count = await bulk_cache_entities(spells, "spells", source_api="open5e")
    print(f"Cached {count} spells")

    return spells
```

#### Pattern 2: Retrieve Cached Spell with Fallback

```python
async def get_spell(slug: str):
    """Get spell from cache or fetch from API."""
    from lorekeeper_mcp.cache.db import get_cached_entity, bulk_cache_entities

    # Try cache first
    spell = await get_cached_entity("spells", slug)
    if spell:
        return spell

    # Cache miss - fetch from API
    spell = await api_client.get_spell(slug)
    await bulk_cache_entities([spell], "spells", source_api="open5e")

    return spell
```

#### Pattern 3: Filter Spells by Level and School

```python
async def find_spells_for_wizard(level: int, school: str):
    """Find spells suitable for a wizard."""
    from lorekeeper_mcp.cache.db import query_cached_entities

    spells = await query_cached_entities(
        "spells",
        level=level,
        school=school
    )

    print(f"Found {len(spells)} {school} spells at level {level}")
    return spells
```

#### Pattern 4: Get Cache Statistics

```python
async def print_cache_health():
    """Print cache statistics."""
    from lorekeeper_mcp.cache.db import get_cache_stats

    stats = await get_cache_stats()

    print("Cache Statistics:")
    print(f"  Database size: {stats['db_size_bytes'] / 1024 / 1024:.1f} MB")
    print(f"  Schema version: {stats['schema_version']}")
    print("\n  Entity counts:")

    for entity_type, count in stats["entity_counts"].items():
        if count > 0:
            print(f"    {entity_type}: {count}")
```

### Schema Initialization

The cache system automatically initializes all entity tables on startup:

```python
from lorekeeper_mcp.cache.db import init_db

# Call during application startup
await init_db()

# This creates:
# - All entity type tables (spells, monsters, weapons, etc.)
# - Indexes on filtered fields per entity type
# - Legacy api_cache table for backward compatibility
# - WAL mode for concurrent access
```

## Performance Optimizations

### WAL Mode

SQLite WAL (Write-Ahead Logging) mode provides:

- **Concurrent reads and writes**: Multiple readers can access data while writes occur
- **Better performance**: Reduced contention for database locks
- **Crash recovery**: Better durability in case of crashes

```python
async def init_db() -> None:
    """Initialize database with WAL mode."""
    async with aiosqlite.connect(db_path) as db:
        # Enable WAL mode
        await db.execute("PRAGMA journal_mode=WAL")

        # Additional optimizations
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.execute("PRAGMA cache_size=10000")
        await db.execute("PRAGMA temp_store=memory")
```

### Connection Management

```python
class DatabaseManager:
    """Manages database connections with pooling."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = None

    async def get_connection(self) -> aiosqlite.Connection:
        """Get a database connection, creating if needed."""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            await self._connection.execute("PRAGMA journal_mode=WAL")
        return self._connection

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
```

### Batch Operations

For bulk operations, use transactions:

```python
async def batch_cache_insert(
    entries: list[tuple[str, dict, str, int, str]]
) -> None:
    """Insert multiple cache entries in a single transaction."""
    async with aiosqlite.connect(settings.db_path) as db:
        now = time.time()

        # Prepare batch data
        batch_data = []
        for key, data, content_type, ttl, source_api in entries:
            expires_at = now + ttl
            batch_data.append((
                key, json.dumps(data), now, expires_at, content_type, source_api
            ))

        # Execute batch insert
        await db.executemany(
            """INSERT OR REPLACE INTO api_cache
               (cache_key, response_data, created_at, expires_at, content_type, source_api)
               VALUES (?, ?, ?, ?, ?, ?)""",
            batch_data
        )
        await db.commit()
```

## Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DB_PATH` | SQLite database file path | `./data/cache.db` | `/var/cache/lorekeeper/cache.db` |
| `CACHE_TTL_DAYS` | Default cache TTL for legacy cache in days | `7` | `14` |
| `ERROR_CACHE_TTL_SECONDS` | Error cache TTL in seconds | `300` | `600` |

### Entity Cache Configuration

Entity cache requires no TTL configuration - entities are cached indefinitely. The system automatically manages schema initialization and table creation.

```python
# Entity cache is configured during init_db()
from lorekeeper_mcp.cache.db import init_db

await init_db()
# This sets up all entity tables with no TTL
```

### Legacy Cache TTL Configuration

For the legacy URL-based cache, different content types can use different TTL values:

```python
TTL_CONFIG = {
    "spell": 7 * 24 * 3600,      # 7 days (legacy only)
    "monster": 7 * 24 * 3600,    # 7 days (legacy only)
    "equipment": 7 * 24 * 3600,  # 7 days (legacy only)
    "rule": 14 * 24 * 3600,      # 14 days (rules change less often)
    "background": 30 * 24 * 3600, # 30 days (rarely changes)
    "error": 300,                # 5 minutes
}

def get_ttl_for_content_type(content_type: str) -> int:
    """Get TTL for a specific content type in legacy cache."""
    return TTL_CONFIG.get(content_type, settings.cache_ttl_days * 24 * 3600)
```

### Database Location

The database path is configurable and supports:

- **Relative paths**: `./data/cache.db`
- **Absolute paths**: `/var/cache/lorekeeper/cache.db`
- **Environment variables**: `$HOME/.cache/lorekeeper/cache.db`

```python
def resolve_db_path(path: str) -> Path:
    """Resolve database path with environment variable expansion."""
    resolved = os.path.expandvars(path)
    return Path(resolved).expanduser().resolve()
```

## Migration from Legacy Cache

### Overview

The system is designed to support both entity-based caching (new) and URL-based caching (legacy). New code should use entity-based operations, but existing code using the legacy cache continues to work.

### Migration Strategy

**Phase 1: Coexistence**
- Entity cache and legacy cache run in the same database
- New code uses entity operations
- Old code continues using legacy operations
- Both are available during transition

**Phase 2: Gradual Adoption**
- Replace legacy cache calls with entity operations where applicable
- Entity-typed data should use entity operations
- Non-entity API responses continue using legacy cache

**Phase 3: Legacy Cleanup (Future)**
- Once all entity data uses entity cache, legacy table can be dropped
- Run: `DROP TABLE api_cache;`

### Migration Example

**Before (Legacy Cache):**
```python
# Fetch from API
spell = await api_client.get_spell("fireball")

# Cache with TTL
await set_cached(
    "open5e:v2/spells:slug=fireball",
    spell,
    content_type="spell",
    ttl_seconds=7*24*3600,
    source_api="open5e"
)

# Retrieve from cache (checks expiration)
cached = await get_cached("open5e:v2/spells:slug=fireball")
```

**After (Entity Cache):**
```python
# Fetch from API
spell = await api_client.get_spell("fireball")

# Cache without TTL (infinite lifetime)
await bulk_cache_entities([spell], "spells", source_api="open5e")

# Retrieve from cache (no expiration checks)
cached = await get_cached_entity("spells", "fireball")
```

### Benefits of Migration

| Aspect | Legacy | Entity |
|--------|--------|--------|
| **TTL Management** | Manual per-call | Automatic (infinite) |
| **Key Generation** | Complex and error-prone | Slug-based (simple) |
| **Filtering** | Not supported | Full support with indexes |
| **Bulk Operations** | Not optimized | Designed for efficiency |
| **Database Size** | Grows unbounded | Grows proportional to data |

## Monitoring and Maintenance

### Cache Health Monitoring

```python
async def check_cache_health() -> dict[str, Any]:
    """Check cache health and performance for entity cache."""
    from lorekeeper_mcp.cache.db import get_cache_stats

    stats = await get_cache_stats()

    health = {
        "status": "healthy",
        "issues": [],
        "recommendations": [],
        "stats": stats
    }

    # Check database size
    size_mb = stats["database_size_bytes"] / (1024 * 1024)
    if size_mb > 1000:  # > 1GB
        health["issues"].append("Large database size (>1GB)")
        health["recommendations"].append("Consider VACUUM to reclaim space")

    # Check if cache has data
    total_entities = sum(stats["entity_counts"].values())
    if total_entities == 0:
        health["status"] = "empty"
        health["recommendations"].append("No entities cached yet - populate with API data")

    # Check for balance across entity types
    populated_types = [k for k, v in stats["entity_counts"].items() if v > 0]
    if len(populated_types) < 3:
        health["recommendations"].append(
            f"Only {len(populated_types)} entity types cached - consider fetching more types"
        )

    return health
```

#### Entity-Specific Monitoring

```python
async def get_entity_cache_report() -> dict[str, Any]:
    """Get detailed entity cache monitoring report."""
    from lorekeeper_mcp.cache.db import get_cache_stats, get_entity_count

    stats = await get_cache_stats()

    report = {
        "timestamp": time.time(),
        "total_entities": sum(stats["entity_counts"].values()),
        "db_size_mb": stats["database_size_bytes"] / 1024 / 1024,
        "entities": {}
    }

    # Detail per entity type
    for entity_type, count in stats["entity_counts"].items():
        if count > 0:
            report["entities"][entity_type] = {
                "count": count,
                "example_query": f"query_cached_entities('{entity_type}')"
            }

    return report
```

### Automated Maintenance

```python
async def maintenance_task() -> None:
    """Run regular cache maintenance tasks."""
    import asyncio
    import logging
    import aiosqlite
    from lorekeeper_mcp.cache.db import cleanup_expired, get_cache_stats
    from lorekeeper_mcp.config import settings

    logger = logging.getLogger(__name__)
    logger.info("Starting cache maintenance")

    # Cleanup expired entries (legacy cache only - entities never expire)
    deleted_count = await cleanup_expired()
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired legacy cache entries")

    # Vacuum database to reclaim space
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute("VACUUM")
        logger.info("Database vacuumed")

    # Analyze query plans for better performance
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute("ANALYZE")
        logger.info("Database analyzed for query optimization")

    # Check health
    stats = await get_cache_stats()
    logger.info(f"Cache stats: {sum(stats['entity_counts'].values())} total entities")
    logger.info(f"Database size: {stats['database_size_bytes'] / 1024 / 1024:.1f} MB")

    logger.info("Cache maintenance completed")

# Schedule this task to run daily or weekly:
# asyncio.create_task(maintenance_task())
```

#### Maintenance Schedule

Recommended maintenance schedule:

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def setup_cache_maintenance():
    """Schedule cache maintenance tasks."""
    scheduler = AsyncIOScheduler()

    # Run vacuum and analyze daily at midnight
    scheduler.add_job(
        maintenance_task,
        "cron",
        hour=0,
        minute=0,
        id="cache_maintenance"
    )

    scheduler.start()
```

Or with simpler timing:

```python
async def periodic_maintenance():
    """Run maintenance every 24 hours."""
    while True:
        await asyncio.sleep(24 * 3600)  # 24 hours
        try:
            await maintenance_task()
        except Exception as e:
            logger.error(f"Maintenance failed: {e}")

# Start in application startup:
# asyncio.create_task(periodic_maintenance())
```

### Performance Metrics

Track these metrics for cache performance:

**Entity Cache Metrics:**
- **Entity Density**: Count of entities per type to verify cache population
- **Query Performance**: Response time for cached queries vs API calls
- **Database Size**: Growth over time as entities accumulate
- **Indexed Field Selectivity**: Effectiveness of filters for reducing result sets

**Legacy Cache Metrics (if still in use):**
- **Cache Hit Ratio**: Percentage of requests served from cache
- **Average Response Time**: Cache vs API response times
- **Expiration Rate**: How often entries expire vs being re-used
- **Cleanup Performance**: Time taken for maintenance operations

```python
class CacheMetrics:
    """Track cache performance metrics for entity cache."""

    def __init__(self):
        self.entity_hits = 0
        self.entity_misses = 0
        self.query_count = 0
        self.total_response_time = 0.0
        self.entity_response_time = 0.0
        self.api_response_time = 0.0

    def record_entity_hit(self, response_time: float) -> None:
        """Record a cache hit for entity retrieval."""
        self.entity_hits += 1
        self.entity_response_time += response_time
        self.total_response_time += response_time

    def record_entity_miss(self, api_time: float, cache_time: float) -> None:
        """Record a cache miss (entity not cached, fetched from API)."""
        self.entity_misses += 1
        self.api_response_time += api_time
        self.entity_response_time += cache_time
        self.total_response_time += api_time + cache_time

    def record_query(self, response_time: float) -> None:
        """Record a filtered query operation."""
        self.query_count += 1
        self.entity_response_time += response_time
        self.total_response_time += response_time

    @property
    def entity_hit_ratio(self) -> float:
        """Calculate entity cache hit ratio."""
        total = self.entity_hits + self.entity_misses
        return self.entity_hits / total if total > 0 else 0.0

    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        total_ops = self.entity_hits + self.entity_misses + self.query_count
        return self.total_response_time / total_ops if total_ops > 0 else 0.0

    @property
    def avg_entity_response_time(self) -> float:
        """Average time for entity cache operations."""
        total_ops = self.entity_hits + self.query_count
        return self.entity_response_time / total_ops if total_ops > 0 else 0.0

    @property
    def speedup_ratio(self) -> float:
        """How much faster entity cache is vs API."""
        if self.api_response_time == 0:
            return 1.0
        avg_entity = self.entity_response_time / max(self.entity_hits + self.query_count, 1)
        avg_api = self.api_response_time / max(self.entity_misses, 1)
        return avg_api / avg_entity if avg_entity > 0 else 1.0
```

#### Monitoring Usage Pattern

```python
# Create global metrics tracker
cache_metrics = CacheMetrics()

async def get_spell_with_metrics(slug: str):
    """Get spell with performance tracking."""
    from lorekeeper_mcp.cache.db import get_cached_entity
    import time

    start = time.perf_counter()
    spell = await get_cached_entity("spells", slug)
    elapsed = time.perf_counter() - start

    if spell:
        cache_metrics.record_entity_hit(elapsed)
    else:
        # Would fetch from API
        cache_metrics.record_entity_miss(0.1, elapsed)  # Example times

    return spell

# Periodically report metrics
async def print_metrics():
    """Report cache performance metrics."""
    print(f"Entity hit ratio: {cache_metrics.entity_hit_ratio:.1%}")
    print(f"Avg response time: {cache_metrics.avg_response_time*1000:.1f}ms")
    print(f"Cache speedup: {cache_metrics.speedup_ratio:.1f}x faster than API")
```

## Troubleshooting

### Common Issues

#### Database Lock Errors

**Symptoms**: `sqlite3.OperationalError: database is locked`

**Causes**:
- Multiple processes trying to write simultaneously
- Long-running transactions
- WAL mode not enabled

**Solutions**:
```python
# Ensure WAL mode is enabled (init_db() does this automatically)
await db.execute("PRAGMA journal_mode=WAL")

# Use shorter transactions
async with aiosqlite.connect(db_path) as db:
    # Execute quickly, then exit context to commit

# Add retry logic for transient locks
async def execute_with_retry(db, query, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await db.execute(query, params)
        except aiosqlite.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                continue
            raise
```

#### Entity Not Found After Caching

**Symptoms**: `get_cached_entity()` returns None after `bulk_cache_entities()` succeeded

**Causes**:
- Entity missing required `slug` field
- Entity type mismatch (cached as "spells" but queried as "monsters")
- Database transaction not committed before query

**Solutions**:
```python
# Ensure entity has required fields
def validate_entity(entity: dict, entity_type: str) -> bool:
    """Validate entity before caching."""
    required_fields = ["slug", "name"]
    return all(field in entity and entity[field] for field in required_fields)

# Cache with validation
for entity in entities:
    if not validate_entity(entity, entity_type):
        logger.warning(f"Skipping invalid entity: {entity}")
        continue

# Verify after caching
count = await bulk_cache_entities(valid_entities, "spells")
cached = await get_cached_entity("spells", "fireball")
assert cached is not None, "Entity should be cached after bulk_cache_entities"
```

#### Filter Query Returns No Results

**Symptoms**: `query_cached_entities("spells", level=3)` returns empty list but entities exist

**Causes**:
- Indexed field value mismatch (e.g., storing as integer "3" but querying as string)
- Field not indexed for this entity type
- Entities cached with NULL values in filter field

**Solutions**:
```python
# Check what fields are indexed for entity type
from lorekeeper_mcp.cache.schema import INDEXED_FIELDS
print(INDEXED_FIELDS["spells"])

# Verify field values before caching
for spell in spells:
    if "level" not in spell:
        spell["level"] = 0  # Default value
    if not isinstance(spell["level"], int):
        spell["level"] = int(spell["level"])

# Debug: Query all entities and inspect values
all_spells = await query_cached_entities("spells")
print(f"Total spells: {len(all_spells)}")
print("Sample levels:", [s.get("level") for s in all_spells[:5]])

# Check query plan
async with aiosqlite.connect(db_path) as db:
    cursor = await db.execute(
        "EXPLAIN QUERY PLAN SELECT data FROM spells WHERE level = ?",
        (3,)
    )
    plan = await cursor.fetchall()
    print("Query plan:", plan)
```

#### Slow Query Performance

**Symptoms**: Slow cache lookups or filtered queries

**Causes**:
- Missing indexes
- Large database file with fragmentation
- Inefficient filter selectivity

**Solutions**:
```python
import time
import logging

async def check_query_performance(entity_type: str, **filters):
    """Profile a query operation."""
    start = time.perf_counter()

    results = await query_cached_entities(entity_type, **filters)

    elapsed = (time.perf_counter() - start) * 1000
    logging.info(f"Query {entity_type} with {filters}: {elapsed:.1f}ms returned {len(results)} results")

    # If > 100ms, consider ANALYZE or VACUUM
    if elapsed > 100:
        logging.warning("Query slow - run VACUUM and ANALYZE")

# Manually optimize database
async def optimize_database():
    """Rebuild indexes and reclaim space."""
    async with aiosqlite.connect(settings.db_path) as db:
        logger.info("Rebuilding indexes...")
        await db.execute("REINDEX")

        logger.info("Vacuuming database...")
        await db.execute("VACUUM")

        logger.info("Analyzing query statistics...")
        await db.execute("ANALYZE")

        await db.commit()

    logger.info("Database optimization complete")
```

#### Memory Usage

**Symptoms**: High memory consumption during bulk operations

**Causes**:
- Large entities stored as JSON
- Many entities loaded in memory simultaneously
- Inefficient batch sizes

**Solutions**:
```python
# Process large result sets in batches
async def query_entities_in_batches(
    entity_type: str,
    batch_size: int = 1000,
    **filters
):
    """Query entities in batches to control memory."""
    offset = 0
    while True:
        # SQLite doesn't have LIMIT in our query_cached_entities,
        # so retrieve all and process
        results = await query_cached_entities(entity_type, **filters)

        for i in range(0, len(results), batch_size):
            batch = results[i:i+batch_size]
            yield batch

        if len(results) < batch_size:
            break

# Limit bulk cache operation sizes
MAX_BULK_SIZE = 1000

async def cache_entities_in_chunks(entities: list, entity_type: str):
    """Cache large entity lists in smaller chunks."""
    for i in range(0, len(entities), MAX_BULK_SIZE):
        chunk = entities[i:i+MAX_BULK_SIZE]
        count = await bulk_cache_entities(chunk, entity_type)
        logger.info(f"Cached {count} {entity_type}")
```

#### Database File Grows Too Large

**Symptoms**: `data/cache.db` becomes very large (>1GB)

**Causes**:
- Old deleted records not reclaimed
- Database fragmentation
- Too many old versions in WAL

**Solutions**:
```python
# Run these operations regularly
async def reclaim_space():
    """Reclaim disk space from cache database."""
    import os
    from pathlib import Path

    db_path = Path(settings.db_path)
    before_size = db_path.stat().st_size / 1024 / 1024

    async with aiosqlite.connect(settings.db_path) as db:
        # Checkpoint WAL to compact it
        await db.execute("PRAGMA wal_checkpoint(RESTART)")

        # Vacuum to reclaim deleted space
        await db.execute("VACUUM")

        await db.commit()

    after_size = db_path.stat().st_size / 1024 / 1024
    reclaimed = before_size - after_size

    logger.info(f"Reclaimed {reclaimed:.1f} MB (was {before_size:.1f} MB, now {after_size:.1f} MB)")
```

### Debugging Tools

#### Cache Inspection

```python
async def inspect_cached_entities(entity_type: str, limit: int = 10) -> list[dict]:
    """Inspect entity cache for debugging."""
    import aiosqlite
    from lorekeeper_mcp.cache.schema import get_table_name
    from lorekeeper_mcp.config import settings

    table_name = get_table_name(entity_type)

    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            f"""SELECT slug, name, source_api, updated_at
               FROM {table_name}
               ORDER BY updated_at DESC
               LIMIT ?""",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

# Usage
entities = await inspect_cached_entities("spells", limit=5)
for entity in entities:
    print(f"  {entity['slug']}: {entity['name']} (from {entity['source_api']})")
```

#### Verify Entity Cache Population

```python
async def verify_cache_populated():
    """Verify cache has entities and show summary."""
    from lorekeeper_mcp.cache.db import get_cache_stats

    stats = await get_cache_stats()

    print("Cache Population Summary:")
    print(f"Database: {stats['db_size_bytes'] / 1024 / 1024:.1f} MB")
    print(f"Schema version: {stats['schema_version']}")
    print("\nEntity counts:")

    for entity_type, count in sorted(stats["entity_counts"].items()):
        if count > 0:
            print(f"  ✓ {entity_type:20s} {count:5d} cached")
        else:
            print(f"  · {entity_type:20s}     - (empty)")
```

#### Performance Profiling

```python
import time
import logging
from functools import wraps
from typing import Any, Callable

def profile_cache_operation(func: Callable) -> Callable:
    """Decorator to profile and log cache operations."""
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger(func.__module__)
        start_time = time.perf_counter()
        operation_name = func.__name__

        try:
            result = await func(*args, **kwargs)
            success = True
            error_msg = None
        except Exception as e:
            result = None
            success = False
            error_msg = str(e)

        duration_ms = (time.perf_counter() - start_time) * 1000

        if success:
            logger.debug(f"{operation_name}: {duration_ms:.1f}ms")
        else:
            logger.error(f"{operation_name}: {duration_ms:.1f}ms, error={error_msg}")

        if not success:
            raise Exception(error_msg)

        return result

    return wrapper

# Usage
@profile_cache_operation
async def get_spell_cached(slug: str):
    from lorekeeper_mcp.cache.db import get_cached_entity
    return await get_cached_entity("spells", slug)

# Example output in logs:
# DEBUG: get_spell_cached: 0.5ms
```

#### SQL Debug Queries

```python
async def debug_query_plan(entity_type: str, **filters):
    """Show query plan for debugging performance."""
    import aiosqlite
    from lorekeeper_mcp.cache.schema import get_table_name
    from lorekeeper_mcp.config import settings

    table_name = get_table_name(entity_type)

    # Build WHERE clause
    where_clauses = [f"{k} = ?" for k in filters.keys()]
    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query = f"SELECT data FROM {table_name}{where_sql}"
    params = list(filters.values())

    async with aiosqlite.connect(settings.db_path) as db:
        # Show the query plan
        cursor = await db.execute(f"EXPLAIN QUERY PLAN {query}", params)
        plan = await cursor.fetchall()

        print(f"Query: {query}")
        print(f"Params: {params}")
        print("Query plan:")
        for row in plan:
            print(f"  {row}")
```

## Summary

The entity-based cache system provides efficient, structured caching for D&D entities with the following benefits:

- **Immutable Entities**: Once cached, entities remain available indefinitely (no TTL management overhead)
- **Efficient Queries**: Indexed fields enable fast filtering by level, school, CR, type, etc.
- **Bulk Operations**: Batch caching operations optimize API response processing
- **Observability**: Built-in statistics and health monitoring
- **Backward Compatibility**: Legacy URL-based cache still available for non-entity data

This architecture balances simplicity with performance, making it easy to cache large D&D entity libraries while maintaining fast query performance.
