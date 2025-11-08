# Spec: Database Setup

## ADDED Requirements

### Requirement: SQLite database must be initialized for caching

The project SHALL use SQLite as the caching database with async operations via aiosqlite.

#### Scenario: Database connection can be established
```
GIVEN the aiosqlite library is installed
WHEN the cache module initializes
THEN a connection to the SQLite database is established
AND the database file is created if it doesn't exist
AND connection supports async context manager pattern
```

#### Scenario: Database location is configurable
```
GIVEN the application configuration
WHEN determining the database file path
THEN the path can be set via environment variable DB_PATH
AND defaults to ./data/cache.db for local development
AND the parent directory is created if it doesn't exist
```

### Requirement: Cache schema must support API response storage

The database SHALL have a schema optimized for storing and retrieving API responses with TTL support.

#### Scenario: Cache table structure supports required operations
```
GIVEN the database schema
WHEN examining the cache table
THEN it has columns for:
  - cache_key (TEXT PRIMARY KEY) - URL or unique identifier
  - response_data (TEXT) - JSON response from API
  - created_at (REAL) - Unix timestamp of cache entry creation
  - expires_at (REAL) - Unix timestamp when cache entry should be invalidated
  - content_type (TEXT) - Type of cached content (spell, monster, etc.)
AND indexes exist for efficient querying by expires_at and content_type
```

#### Scenario: Cache entries can be stored
```
GIVEN an API response to cache
WHEN storing the response with a key and TTL
THEN the response is serialized to JSON
AND stored with appropriate timestamps
AND content type is recorded for filtering
AND operation completes without blocking
```

#### Scenario: Cache entries can be retrieved
```
GIVEN a cache key
WHEN querying for cached data
THEN the stored response is returned if not expired
AND expired entries return None/null
AND retrieval is async and non-blocking
```

#### Scenario: Expired cache entries are cleaned up
```
GIVEN cache entries with various expiration times
WHEN cleanup operation runs
THEN entries with expires_at < current time are deleted
AND database size is reduced
AND operation can run in background
```

### Requirement: Database operations must be async-safe

All database operations SHALL use async/await patterns to prevent blocking the MCP server.

#### Scenario: Concurrent cache operations don't block
```
GIVEN multiple simultaneous tool invocations
WHEN each attempts to read/write cache
THEN operations are queued properly
AND no database lock errors occur
AND server remains responsive
```

#### Scenario: Connection pooling prevents resource exhaustion
```
GIVEN sustained high request volume
WHEN multiple database operations execute
THEN connections are reused efficiently
AND connection limits are not exceeded
AND old connections are properly closed
```

## Schema Definition

```sql
CREATE TABLE IF NOT EXISTS api_cache (
    cache_key TEXT PRIMARY KEY,
    response_data TEXT NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    content_type TEXT NOT NULL,
    source_api TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_expires_at ON api_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_content_type ON api_cache(content_type);
CREATE INDEX IF NOT EXISTS idx_source_api ON api_cache(source_api);
```

## Cache TTL Configuration

- **Default TTL**: 7 days (604800 seconds) for game content
- **Error TTL**: 5 minutes (300 seconds) for failed API requests
- **Manual invalidation**: Support for clearing cache by content_type or specific keys
