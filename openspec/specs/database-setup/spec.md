# database-setup Specification

## Purpose
Defines the SQLite database configuration for the entity cache layer, including schema design, case-insensitive indexes, async operations via aiosqlite, TTL management, WAL mode for concurrency, migration support, and performance optimization through statistics collection and periodic maintenance.
## Requirements
### Requirement: SQLite database must be initialized for caching

The project SHALL use SQLite as a legacy caching database option, with Milvus Lite as the new default for semantic search capabilities.

#### Scenario: Database connection can be established
**Given** the `LOREKEEPER_CACHE_BACKEND=sqlite` environment variable is set
**When** the cache module initializes
**Then** a connection to the SQLite database is established via aiosqlite
**And** the database file is created if it doesn't exist
**And** connection supports async context manager pattern
**And** semantic search methods raise NotImplementedError

#### Scenario: Database location is configurable
**Given** SQLite backend is selected
**When** determining the database file path
**Then** the path can be set via environment variable `LOREKEEPER_SQLITE_DB_PATH`
**And** defaults to `~/.lorekeeper/cache.db` for all environments
**And** the parent directory is created if it doesn't exist

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

The system SHALL maintain database statistics and run periodic optimization for the active cache backend.

#### Scenario: Milvus Lite statistics collection
**Given** Milvus Lite is the active cache backend
**When** data is inserted or queried
**Then** collection statistics are available via `get_cache_stats()`
**And** statistics include entity counts per collection
**And** statistics include database file size
**And** statistics include embedding dimension and index type

#### Scenario: SQLite database statistics collection (legacy)
**Given** SQLite is the active cache backend
**When** data is inserted, updated, or deleted
**Then** the system runs `ANALYZE` command to update statistics
**And** query planner has accurate information for optimal query plans
**And** performance remains consistent as data grows

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

The system SHALL ensure database enhancements are compatible with existing backup and recovery procedures for both backends.

#### Scenario: Backup with Milvus Lite database
**Given** regular database backups are performed
**When** backing up the Milvus Lite database file
**Then** the single `.db` file contains all data and indexes
**And** backup can be performed by copying the file
**And** restore operation works by replacing the file
**And** no data or functionality is lost in backup/restore cycle

#### Scenario: Backup with SQLite database (legacy)
**Given** SQLite backend is active and backups are performed
**When** backing up the SQLite database
**Then** all indexes are included in the backup
**And** backup file contains complete schema definition
**And** restore operation recreates all indexes correctly
**And** no data or functionality is lost in backup/restore cycle

### Requirement: Milvus Lite Database Initialization

The project SHALL support Milvus Lite as an alternative database backend with embedded vector storage capabilities.

#### Scenario: Milvus Lite database connection can be established
**Given** the pymilvus library is installed with Milvus Lite support
**When** the MilvusCache module initializes with `MilvusCache(db_path="~/.lorekeeper/milvus.db")`
**Then** a MilvusClient is created with the local file path URI
**And** the database file is created if it doesn't exist
**And** no external services or Docker containers are required
**And** the database operates fully embedded in the Python process
**And** initialization uses `MilvusClient("path/to/milvus.db")` pattern

#### Scenario: Milvus Lite database location is configurable
**Given** the application configuration
**When** determining the database file path
**Then** the path can be set via environment variable `LOREKEEPER_MILVUS_DB_PATH`
**And** defaults to `~/.lorekeeper/milvus.db` for all environments
**And** the parent directory is created if it doesn't exist

### Requirement: Milvus Lite Collection Schema

The Milvus Lite database SHALL have collections with schemas optimized for hybrid search (vector + scalar).

#### Scenario: Collection structure supports entity storage with embeddings
**Given** the Milvus Lite schema initialization
**When** examining the spells collection
**Then** it has fields for:
  - `slug` (VARCHAR, PRIMARY KEY) - unique entity identifier
  - `name` (VARCHAR) - entity name for display
  - `embedding` (FLOAT_VECTOR, dim=384) - semantic embedding vector
  - `document` (VARCHAR) - source document key
  - `source_api` (VARCHAR) - API source identifier
  - Entity-specific indexed scalar fields (level, school, etc.)
**And** dynamic fields are enabled for full entity JSON storage

#### Scenario: Collection indexes support hybrid search
**Given** a Milvus Lite collection
**When** examining the index configuration
**Then** IVF_FLAT index is created on the embedding field
**And** COSINE metric type is configured for semantic similarity
**And** nlist=128 clusters are configured for search efficiency
**And** scalar fields (level, school, etc.) are indexed for filtering

### Requirement: Milvus Lite Async Operations

All Milvus Lite database operations SHALL support efficient concurrent access without blocking.

#### Scenario: Concurrent cache operations don't block
**Given** multiple simultaneous tool invocations
**When** each attempts to read/write to Milvus Lite
**Then** operations complete without blocking each other
**And** no database lock errors occur
**And** server remains responsive

#### Scenario: Connection lifecycle management
**Given** sustained high request volume
**When** multiple database operations execute
**Then** the MilvusClient connection is reused efficiently
**And** connection is properly closed on shutdown
**And** lazy initialization prevents startup delays

### Requirement: Milvus Lite Vector Index Configuration

The system SHALL configure Milvus Lite vector indexes for optimal semantic search performance.

#### Scenario: IVF_FLAT index configuration
**Given** a new collection is created
**When** configuring the vector index
**Then** IVF_FLAT index type is used with nlist=128 clusters
**And** COSINE metric type is configured for normalized embeddings
**And** search uses nprobe=16 for balanced recall/speed tradeoff
**And** index is created automatically on collection creation

#### Scenario: Vector search performance
**Given** a collection with ~10,000 entities
**When** performing semantic search
**Then** query completes in < 100ms
**And** results have reasonable recall (>80% of relevant items in top 20)
**And** memory usage is bounded and predictable

### Requirement: Cache Backend Selection

The system SHALL support runtime selection of cache backend via configuration.

#### Scenario: Select Milvus Lite backend via configuration
**Given** the environment variable `LOREKEEPER_CACHE_BACKEND=milvus`
**When** the cache factory creates a cache instance
**Then** a MilvusCache instance is returned
**And** all cache operations use Milvus Lite storage

#### Scenario: Select SQLite backend for backward compatibility
**Given** the environment variable `LOREKEEPER_CACHE_BACKEND=sqlite`
**When** the cache factory creates a cache instance
**Then** a SQLiteCache instance is returned
**And** all existing SQLite-based functionality works unchanged
**And** semantic search is not available (raises NotImplementedError)

#### Scenario: Default to Milvus Lite backend
**Given** no `LOREKEEPER_CACHE_BACKEND` environment variable is set
**When** the cache factory creates a cache instance
**Then** a MilvusCache instance is returned by default
**And** semantic search capabilities are available

### Requirement: Cache Factory Implementation

The system SHALL provide a cache factory function that creates the appropriate backend.

#### Scenario: Factory function interface
**Given** the cache factory module
**When** calling `create_cache(**kwargs)`
**Then** the factory reads `LOREKEEPER_CACHE_BACKEND` from environment
**And** returns MilvusCache for "milvus" or default
**And** returns SQLiteCache for "sqlite"
**And** passes relevant kwargs to the cache constructor

#### Scenario: Factory error handling
**Given** an invalid backend name in `LOREKEEPER_CACHE_BACKEND`
**When** calling `create_cache()`
**Then** a ValueError is raised with message listing valid backends
**And** valid backends are: "milvus", "sqlite"

#### Scenario: Factory provides sensible defaults
**Given** no environment variables are set
**When** calling `create_cache()`
**Then** MilvusCache is created with:
  - `db_path="~/.lorekeeper/milvus.db"`
  - `embedding_model="all-MiniLM-L6-v2"`
**And** defaults can be overridden via kwargs

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
