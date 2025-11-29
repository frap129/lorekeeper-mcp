# database-setup Specification Delta

## MODIFIED Requirements

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
