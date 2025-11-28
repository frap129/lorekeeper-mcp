# database-setup Specification

## Purpose
Defines the SQLite database configuration for the entity cache layer, including schema design, case-insensitive indexes, async operations via aiosqlite, TTL management, WAL mode for concurrency, migration support, and performance optimization through statistics collection and periodic maintenance.
## Requirements
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

### Requirement: Case-Insensitive Indexes
The system SHALL create case-insensitive indexes on the `name` field for all entity tables to support efficient case-insensitive queries.

**Tables to Index:**
- `spells`
- `creatures`
- `equipment`
- `character_options`
- `rules`

#### Scenario: Create case-insensitive spell index
**Given** the database initialization process
**When** creating the spells table indexes
**Then** the system executes `CREATE INDEX IF NOT EXISTS idx_spells_name_lower ON spells(LOWER(name))`
**And** the index supports efficient `LOWER(name) = LOWER(?)` queries
**And** query performance is sub-100ms for case-insensitive lookups

#### Scenario: Case-insensitive creature index creation
**Given** the database setup script runs
**When** indexing the creatures table
**Then** the system creates `idx_creatures_name_lower` index
**And** the index covers all creature records
**And** supports efficient case-insensitive creature searches

#### Scenario: Index verification
**Given** the database is initialized
**When** checking index existence
**Then** all required case-insensitive indexes exist
**And** `EXPLAIN QUERY PLAN` shows index usage for case-insensitive queries
**And** no full table scans occur for indexed searches

---

### Requirement: Essential Case-Insensitive Indexes Only
The system SHALL create only essential case-insensitive indexes to support the new query patterns.

**Essential Indexes Only:**
- `LOWER(name)` indexes for all entity tables
- No composite indexes unless proven necessary through performance testing

#### Scenario: Create only necessary case-insensitive indexes
**Given** performance testing with real query patterns
**When** measuring query execution times
**Then** only create indexes that provide measurable performance benefits
**And** avoid unnecessary index maintenance overhead
**And** focus on essential `LOWER(name)` indexes for case-insensitive queries

#### Scenario: Validate index necessity
**Given** the database is in production use
**When** analyzing query performance with `EXPLAIN QUERY PLAN`
**Then** ensure all case-insensitive queries use the created indexes
**And** verify no full table scans occur for indexed searches
**And** confirm composite indexes are not needed for current query patterns

---

### Requirement: Optional Performance Index Creation
The system SHALL support optional performance index creation for case-insensitive queries without affecting existing functionality.

#### Scenario: Database migration for new indexes
**Given** an existing database without case-insensitive indexes
**When** running the database migration
**Then** the system adds all required case-insensitive indexes
**And** migration is idempotent (can run multiple times safely)
**And** existing data and functionality remain intact
**And** migration completes within reasonable time for large datasets

#### Scenario: Performance index monitoring
**Given** adding case-insensitive performance indexes to large databases
**When** creating the optional indexes
**Then** the system provides progress feedback for index creation
**And** handles index creation timeouts gracefully
**And** continues normal operation even if index creation fails
**And** provides retry mechanisms for failed index creation

#### Scenario: Performance index verification
**Given** the optional performance indexes have been created
**When** verifying the index creation success
**Then** all new performance indexes exist and are usable
**And** `EXPLAIN QUERY PLAN` shows index usage for `LOWER(name)` queries
**And** performance tests confirm improved query times
**And** no regression in existing functionality

---

### Requirement: Database Statistics and Optimization
The system SHALL maintain database statistics and run periodic optimization to ensure optimal query performance.

#### Scenario: Database statistics collection
**Given** the database is in regular use
**When** data is inserted, updated, or deleted
**Then** the system runs `ANALYZE` command to update statistics
**And** query planner has accurate information for optimal query plans
**And** performance remains consistent as data grows

#### Scenario: Periodic database optimization
**Given** the database has been in use for extended periods
**When** performing maintenance operations
**Then** the system runs `VACUUM` to optimize database file
**And** reorganizes indexes for optimal performance
**And** cleans up unused space and fragmented data
**And** maintains optimal query performance over time

#### Scenario: Performance monitoring
**Given** the database is serving production queries
**When** monitoring query performance
**Then** the system tracks query execution times
**And** identifies slow queries that need optimization
**And** ensures indexes are being used effectively
**And** alerts on performance degradation

---

### Requirement: Transaction Safety and Consistency
The system SHALL ensure all database operations maintain data consistency and support proper transaction handling.

#### Scenario: Index creation within transactions
**Given** database schema modifications are needed
**When** creating new indexes
**Then** all index operations are wrapped in transactions
**And** partial index creation is rolled back on failure
**And** database remains consistent even if operations fail
**And** no orphaned or incomplete indexes remain

#### Scenario: Concurrent access during migrations
**Given** the database is being updated while serving queries
**When** schema changes occur
**Then** read operations continue to work during index creation
**And** write operations are properly handled
**And** database remains available throughout the migration
**And** isolation levels prevent interference between operations

---

### Requirement: Gradual Migration Safety
The system SHALL support gradual migration of tools from client-side to database filtering with feature flags.

#### Scenario: Feature flag for creature tool migration
**Given** the enhanced database layer is implemented
**When** migrating `lookup_creature` tool
**Then** the system supports a feature flag to enable/disable enhanced filtering
**And** can revert to client-side filtering if issues occur
**And** maintains backward compatibility during transition

---

### Requirement: Backup and Recovery Compatibility
The system SHALL ensure database enhancements are compatible with existing backup and recovery procedures.

#### Scenario: Backup with enhanced indexes
**Given** regular database backups are performed
**When** backing up the enhanced database
**Then** all new indexes are included in the backup
**And** backup file contains complete schema definition
**And** restore operation recreates all indexes correctly
**And** no data or functionality is lost in backup/restore cycle

#### Scenario: Recovery testing
**Given** database recovery procedures are tested
**When** restoring from backup
**Then** all enhanced indexes are properly restored
**And** query performance after restore matches pre-backup performance
**And** all filtering capabilities work correctly after restore
**And** database integrity is maintained through recovery process

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
