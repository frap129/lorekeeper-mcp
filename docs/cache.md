# Database Cache Documentation

This document provides detailed information about the SQLite-based caching system used in LoreKeeper MCP.

## Table of Contents

- [Overview](#overview)
- [Database Schema](#database-schema)
- [Cache Operations](#cache-operations)
- [Performance Optimizations](#performance-optimizations)
- [Configuration](#configuration)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Overview

The cache layer provides persistent storage for API responses, reducing external API calls and improving response times. It uses SQLite with WAL mode for efficient concurrent access.

### Key Features

- **TTL Support**: Automatic expiration of cached data
- **Content Type Organization**: Separate caching for different data types
- **Source Tracking**: Records which API provided cached data
- **Performance Optimized**: WAL mode, indexes, and connection pooling
- **Maintenance Free**: Automatic cleanup of expired entries

### Cache Strategy

The system uses a **cache-first** strategy:

1. **Check Cache**: Always check cache first for any request
2. **Cache Hit**: Return cached data if valid and not expired
3. **Cache Miss**: Fetch from API, store in cache, return data
4. **Error Caching**: Cache errors briefly to avoid repeated failed requests

## Database Schema

### Main Table: `api_cache`

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

#### Column Descriptions

| Column | Type | Description |
|--------|------|-------------|
| `cache_key` | TEXT | Unique identifier for cached data |
| `response_data` | TEXT | JSON-encoded API response data |
| `created_at` | REAL | Unix timestamp when entry was created |
| `expires_at` | REAL | Unix timestamp when entry expires |
| `content_type` | TEXT | Type of content (spell, monster, etc.) |
| `source_api` | TEXT | API that provided the data (open5e, dnd5e) |

### Indexes

```sql
-- For efficient cleanup of expired entries
CREATE INDEX idx_expires_at ON api_cache(expires_at);

-- For content-type based queries
CREATE INDEX idx_content_type ON api_cache(content_type);

-- Composite index for common queries
CREATE INDEX idx_content_expires ON api_cache(content_type, expires_at);
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

### Cache Key Generation

Cache keys follow the pattern: `{api}:{endpoint}:{params_hash}`

#### Examples

```python
# Spell lookup
"open5e:v2/spells:name=fireball,level=3"

# Monster lookup
"open5e:v1/monsters:cr=5,type=undead"

# Equipment lookup
"open5e:v2/weapons:damage_dice=1d8,is_simple=true"

# Rule lookup
"dnd5e:rules:section=combat,name=opportunity attack"
```

#### Key Generation Logic

```python
def build_cache_key(api: str, endpoint: str, **params) -> str:
    """Build a consistent cache key from parameters."""
    # Sort parameters for consistent ordering
    sorted_params = sorted(params.items())
    param_string = ",".join(f"{k}={v}" for k, v in sorted_params if v is not None)

    # Create hash for long parameter strings
    if len(param_string) > 100:
        param_hash = hashlib.md5(param_string.encode()).hexdigest()[:8]
        param_string = f"hash:{param_hash}"

    return f"{api}:{endpoint}:{param_string}"
```

### Core Operations

#### Get Cached Data

```python
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

        return cast(dict[str, Any], json.loads(row["response_data"]))
```

#### Set Cached Data

```python
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
        source_api: Source API that provided the data
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
```

#### Cleanup Expired Entries

```python
async def cleanup_expired() -> int:
    """Remove expired cache entries from the database.

    Returns:
        Number of entries that were deleted
    """
    async with aiosqlite.connect(settings.db_path) as db:
        current_time = time.time()
        cursor = await db.execute(
            "DELETE FROM api_cache WHERE expires_at < ?",
            (current_time,)
        )
        deleted_count = cursor.rowcount
        await db.commit()
        return deleted_count
```

### Cache Statistics

```python
async def get_cache_stats() -> dict[str, Any]:
    """Get cache statistics for monitoring."""
    async with aiosqlite.connect(settings.db_path) as db:
        stats = {}

        # Total entries
        cursor = await db.execute("SELECT COUNT(*) FROM api_cache")
        stats["total_entries"] = (await cursor.fetchone())[0]

        # Expired entries
        current_time = time.time()
        cursor = await db.execute(
            "SELECT COUNT(*) FROM api_cache WHERE expires_at < ?",
            (current_time,)
        )
        stats["expired_entries"] = (await cursor.fetchone())[0]

        # Entries by content type
        cursor = await db.execute(
            """SELECT content_type, COUNT(*)
               FROM api_cache
               GROUP BY content_type"""
        )
        stats["by_content_type"] = dict(await cursor.fetchall())

        # Entries by source API
        cursor = await db.execute(
            """SELECT source_api, COUNT(*)
               FROM api_cache
               GROUP BY source_api"""
        )
        stats["by_source_api"] = dict(await cursor.fetchall())

        # Database size
        cursor = await db.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        stats["database_size_bytes"] = (await cursor.fetchone())[0]

        return stats
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
| `CACHE_TTL_DAYS` | Default cache TTL in days | `7` | `14` |
| `ERROR_CACHE_TTL_SECONDS` | Error cache TTL in seconds | `300` | `600` |

### TTL Configuration

Different content types use different TTL values:

```python
TTL_CONFIG = {
    "spell": 7 * 24 * 3600,      # 7 days
    "monster": 7 * 24 * 3600,    # 7 days
    "equipment": 7 * 24 * 3600,  # 7 days
    "rule": 14 * 24 * 3600,      # 14 days (rules change less often)
    "background": 30 * 24 * 3600, # 30 days (rarely changes)
    "error": 300,                # 5 minutes
}

def get_ttl_for_content_type(content_type: str) -> int:
    """Get TTL for a specific content type."""
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

## Monitoring and Maintenance

### Cache Health Monitoring

```python
async def check_cache_health() -> dict[str, Any]:
    """Check cache health and performance."""
    stats = await get_cache_stats()

    health = {
        "status": "healthy",
        "issues": [],
        "recommendations": []
    }

    # Check for too many expired entries
    expired_ratio = stats["expired_entries"] / max(stats["total_entries"], 1)
    if expired_ratio > 0.2:
        health["issues"].append("High ratio of expired entries")
        health["recommendations"].append("Run cleanup operation")

    # Check database size
    size_mb = stats["database_size_bytes"] / (1024 * 1024)
    if size_mb > 1000:  # > 1GB
        health["issues"].append("Large database size")
        health["recommendations"].append("Consider reducing TTL or running cleanup")

    # Check cache hit ratio (if tracked)
    # This would require additional tracking in the cache layer

    return health
```

### Automated Maintenance

```python
async def maintenance_task() -> None:
    """Run regular cache maintenance tasks."""
    logger.info("Starting cache maintenance")

    # Cleanup expired entries
    deleted_count = await cleanup_expired()
    logger.info(f"Cleaned up {deleted_count} expired entries")

    # Vacuum database to reclaim space
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute("VACUUM")
        logger.info("Database vacuumed")

    # Analyze query plans
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute("ANALYZE")
        logger.info("Database analyzed")

    # Check health
    health = await check_cache_health()
    if health["issues"]:
        logger.warning(f"Cache health issues: {health['issues']}")

    logger.info("Cache maintenance completed")
```

### Performance Metrics

Track these metrics for cache performance:

- **Cache Hit Ratio**: Percentage of requests served from cache
- **Average Response Time**: Cache vs API response times
- **Database Size**: Growth over time
- **Cleanup Performance**: Time taken for maintenance operations

```python
class CacheMetrics:
    """Track cache performance metrics."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.total_response_time = 0.0
        self.cache_response_time = 0.0
        self.api_response_time = 0.0

    def record_hit(self, response_time: float) -> None:
        """Record a cache hit."""
        self.hits += 1
        self.cache_response_time += response_time
        self.total_response_time += response_time

    def record_miss(self, api_time: float, cache_time: float) -> None:
        """Record a cache miss."""
        self.misses += 1
        self.api_response_time += api_time
        self.cache_response_time += cache_time
        self.total_response_time += api_time + cache_time

    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        total_requests = self.hits + self.misses + self.errors
        return self.total_response_time / total_requests if total_requests > 0 else 0.0
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
# Ensure WAL mode is enabled
await db.execute("PRAGMA journal_mode=WAL")

# Use shorter transactions
async with db.transaction():
    # Quick operations

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

#### Slow Query Performance

**Symptoms**: Slow cache lookups or insertions

**Causes**:
- Missing indexes
- Large database file
- Fragmentation

**Solutions**:
```sql
-- Check query plan
EXPLAIN QUERY PLAN SELECT * FROM api_cache WHERE cache_key = ?;

-- Rebuild indexes
REINDEX;

-- Vacuum database
VACUUM;

-- Analyze statistics
ANALYZE;
```

#### Memory Usage

**Symptoms**: High memory consumption

**Causes**:
- Large cached responses
- Connection leaks
- Inefficient data structures

**Solutions**:
```python
# Limit response size
MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10MB

async def set_cached_with_size_limit(key: str, data: dict, **kwargs) -> None:
    """Set cached data with size limit."""
    json_data = json.dumps(data)
    if len(json_data) > MAX_RESPONSE_SIZE:
        logger.warning(f"Response too large for cache: {len(json_data)} bytes")
        return

    await set_cached(key, data, **kwargs)

# Use connection pooling
class ConnectionPool:
    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self.pool = asyncio.Queue(maxsize=max_connections)
        self._initialize_pool()

    async def _initialize_pool(self) -> None:
        for _ in range(self.max_connections):
            conn = await aiosqlite.connect(self.db_path)
            await self.pool.put(conn)
```

### Debugging Tools

#### Cache Inspection

```python
async def inspect_cache(key_pattern: str = None) -> list[dict]:
    """Inspect cache entries for debugging."""
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row

        if key_pattern:
            cursor = await db.execute(
                """SELECT * FROM api_cache
                   WHERE cache_key LIKE ?
                   ORDER BY created_at DESC
                   LIMIT 50""",
                (f"%{key_pattern}%",)
            )
        else:
            cursor = await db.execute(
                """SELECT * FROM api_cache
                   ORDER BY created_at DESC
                   LIMIT 50"""
            )

        return [dict(row) for row in await cursor.fetchall()]
```

#### Performance Profiling

```python
import time
from functools import wraps

def profile_cache_operation(func):
    """Decorator to profile cache operations."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            success = True
        except Exception as e:
            result = e
            success = False

        duration = time.time() - start_time
        logger.info(f"{func.__name__}: {duration:.3f}s, success={success}")

        if not success:
            raise result

        return result

    return wrapper

# Usage
@profile_cache_operation
async def get_cached(key: str) -> dict[str, Any] | None:
    # Original implementation
    pass
```

This cache system provides a robust foundation for the LoreKeeper MCP project, ensuring fast response times and reliable data persistence.
