# database-setup Specification Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
