# database-setup Specification

## Purpose
Defines the Milvus Lite database configuration for the entity cache layer, including collection schema design, vector indexes for semantic search, async operations, and performance optimization through IVF_FLAT indexing.
## Requirements
### Requirement: Milvus Lite Database Initialization

The project SHALL use Milvus Lite as the embedded vector database for caching with semantic search capabilities.

#### Scenario: Database connection can be established
**Given** the cache module initializes
**When** MilvusCache is created with default configuration
**Then** a MilvusClient is created with the local file path URI
**And** the database file is created if it doesn't exist
**And** no external services or Docker containers are required
**And** the database operates fully embedded in the Python process

#### Scenario: Database location follows XDG Base Directory Specification
**Given** the application configuration with no overrides
**When** determining the database file path
**Then** the path defaults to `$XDG_DATA_HOME/lorekeeper/milvus.db` when XDG_DATA_HOME is set
**And** falls back to `~/.local/share/lorekeeper/milvus.db` when XDG_DATA_HOME is not set
**And** the path can be overridden via environment variable `LOREKEEPER_MILVUS_DB_PATH`
**And** the path can be overridden via CLI flag `--db-path`
**And** the parent directory is created if it doesn't exist

#### Scenario: Backward compatibility with legacy database location
**Given** an existing database at `~/.lorekeeper/milvus.db`
**And** no database exists at the new XDG location
**And** no override is specified (no env var or CLI flag)
**When** the application starts
**Then** the existing database at `~/.lorekeeper/milvus.db` is used
**And** an informational log message indicates using legacy location
**And** the application functions normally without requiring user migration

#### Scenario: Database exists at both legacy and XDG locations
**Given** an existing database at `~/.lorekeeper/milvus.db`
**And** an existing database at the XDG location
**And** no override is specified (no env var or CLI flag)
**When** the application starts
**Then** the XDG location database is used (new location takes precedence)
**And** a warning log message indicates an orphaned database exists at the legacy location
**And** the warning suggests the user may want to delete or migrate the legacy database

### Requirement: Collection Schema for Entity Storage

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

### Requirement: Database Operations Must Be Async-Safe

All database operations SHALL support efficient concurrent access without blocking.

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

### Requirement: Vector Index Configuration for Search Quality

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

### Requirement: Database Statistics and Optimization

The system SHALL maintain database statistics for the Milvus cache.

#### Scenario: Statistics collection
**Given** Milvus Lite is the active cache backend
**When** data is inserted or queried
**Then** collection statistics are available via `get_cache_stats()`
**And** statistics include entity counts per collection
**And** statistics include database file size
**And** statistics include embedding dimension and index type

### Requirement: Transaction Safety and Consistency

The system SHALL ensure all database operations maintain data consistency.

#### Scenario: Batch operations are atomic
**Given** a batch insert of multiple entities
**When** inserting entities into a collection
**Then** all entities are inserted or none (atomic operation)
**And** partial failures roll back completely
**And** database remains consistent

#### Scenario: Concurrent access during operations
**Given** the database is being queried while writes occur
**When** read and write operations overlap
**Then** read operations continue to work during writes
**And** isolation prevents data corruption
**And** database remains available throughout

### Requirement: Backup and Recovery Compatibility

The system SHALL ensure database is compatible with backup and recovery procedures.

#### Scenario: Backup with Milvus Lite database
**Given** regular database backups are performed
**When** backing up the Milvus Lite database file
**Then** the single `.db` file contains all data and indexes
**And** backup can be performed by copying the file
**And** restore operation works by replacing the file
**And** no data or functionality is lost in backup/restore cycle

### Requirement: Cache Factory Implementation

The system SHALL provide a cache factory function that creates MilvusCache instances.

#### Scenario: Factory function interface
**Given** the cache factory module
**When** calling `create_cache(**kwargs)`
**Then** a MilvusCache instance is returned
**And** passes relevant kwargs to the cache constructor

#### Scenario: Factory provides sensible defaults
**Given** no environment variables are set
**When** calling `create_cache()`
**Then** MilvusCache is created with:
  - `db_path` following XDG Base Directory Specification (`$XDG_DATA_HOME/lorekeeper/milvus.db` or `~/.local/share/lorekeeper/milvus.db`)
  - `embedding_model="all-MiniLM-L6-v2"`
**And** defaults can be overridden via kwargs
