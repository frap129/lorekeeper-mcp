## MODIFIED Requirements

### Requirement: Cache Backend Configuration

The cache system SHALL use Milvus as the only supported backend. SQLite backend is removed.

#### Scenario: Create default cache
- **WHEN** calling `create_cache()` with no arguments
- **THEN** a MilvusCache instance is created
- **AND** uses default path `~/.lorekeeper/milvus.db`

#### Scenario: Create cache with explicit path
- **WHEN** calling `create_cache(db_path="/custom/path.db")`
- **THEN** a MilvusCache instance is created at the specified path
- **AND** no backend parameter exists (Milvus is the only backend)

#### Scenario: Backend parameter removed
- **WHEN** calling `create_cache(backend="sqlite")` or `create_cache(backend="milvus")`
- **THEN** a `TypeError` is raised for unexpected keyword argument
- **AND** callers must remove the `backend` parameter from their code

---

## REMOVED Requirements

### Requirement: SQLite Cache Backend

**Reason**: SQLite cache backend is deprecated. Milvus provides semantic/vector search capabilities required for the semantic-only search architecture. Maintaining two backends adds complexity without benefit.

**Migration**:
- Remove all `SQLiteCache` usage
- Remove `backend="sqlite"` from `create_cache()` calls
- Remove `LOREKEEPER_CACHE_BACKEND=sqlite` environment variable usage
- Milvus is now the only and default backend

#### Scenario: SQLite configuration no longer supported
- **GIVEN** environment variable `LOREKEEPER_CACHE_BACKEND=sqlite`
- **WHEN** `get_cache_from_config()` is called
- **THEN** the environment variable is ignored
- **AND** MilvusCache is created (the only backend)

---

### Requirement: SQLite Database Initialization (REMOVED)

**Reason**: All SQLite-specific database initialization is removed. This includes:
- SQLite connection establishment via aiosqlite
- SQLite database file creation
- `LOREKEEPER_SQLITE_DB_PATH` environment variable
- Default path `~/.lorekeeper/cache.db`

#### Scenario: Database connection can be established (REMOVED)
- This scenario is removed - SQLite connections are no longer supported

#### Scenario: Database location is configurable (REMOVED)
- `LOREKEEPER_SQLITE_DB_PATH` environment variable is removed
- Default path `~/.lorekeeper/cache.db` is removed

---

### Requirement: SQLite Cache Schema (REMOVED)

**Reason**: SQLite schema for API response storage is removed. The cache table structure, indexes, and TTL management are no longer applicable.

#### Scenario: Cache table structure supports required operations (REMOVED)
- SQLite cache table with cache_key, response_data, created_at, expires_at, content_type columns is removed

#### Scenario: Cache entries can be stored (REMOVED)
- SQLite storage operations are removed

#### Scenario: Cache entries can be retrieved (REMOVED)
- SQLite retrieval operations are removed

#### Scenario: Expired cache entries are cleaned up (REMOVED)
- SQLite cleanup operations are removed

---

### Requirement: SQLite Async Operations (REMOVED)

**Reason**: aiosqlite-based async operations are removed.

#### Scenario: Concurrent cache operations don't block (REMOVED for SQLite)
- SQLite-specific concurrent operation handling is removed

#### Scenario: Connection pooling prevents resource exhaustion (REMOVED for SQLite)
- SQLite connection pooling is removed

---

### Requirement: SQLite Case-Insensitive Indexes (REMOVED)

**Reason**: SQLite indexes on spells, creatures, equipment, character_options, and rules tables are removed.

#### Scenario: Create case-insensitive spell index (REMOVED)
- `idx_spells_name_lower` index creation is removed

#### Scenario: Case-insensitive creature index creation (REMOVED)
- `idx_creatures_name_lower` index creation is removed

#### Scenario: Index verification (REMOVED)
- SQLite index verification is removed

---

### Requirement: SQLite Essential Case-Insensitive Indexes Only (REMOVED)

**Reason**: All SQLite performance index creation is removed.

#### Scenario: Create only necessary case-insensitive indexes (REMOVED)
- SQLite index creation is removed

#### Scenario: Validate index necessity (REMOVED)
- SQLite index validation is removed

---

### Requirement: SQLite Optional Performance Index Creation (REMOVED)

**Reason**: SQLite migration and performance index creation is removed.

#### Scenario: Database migration for new indexes (REMOVED)
- SQLite migration operations are removed

#### Scenario: Performance index monitoring (REMOVED)
- SQLite index monitoring is removed

#### Scenario: Performance index verification (REMOVED)
- SQLite index verification is removed

---

### Requirement: SQLite Database Statistics (REMOVED)

**Reason**: SQLite ANALYZE command and statistics collection is removed.

#### Scenario: SQLite database statistics collection (legacy) (REMOVED)
- `ANALYZE` command execution is removed

---

### Requirement: SQLite Transaction Safety (REMOVED)

**Reason**: SQLite-specific transaction handling is removed.

#### Scenario: Index creation within transactions (REMOVED for SQLite)
- SQLite transaction-wrapped index operations are removed

#### Scenario: Concurrent access during migrations (REMOVED for SQLite)
- SQLite migration concurrency handling is removed

---

### Requirement: SQLite Gradual Migration Safety (REMOVED)

**Reason**: Feature flags for SQLite migration are removed.

#### Scenario: Feature flag for creature tool migration (REMOVED)
- SQLite migration feature flags are removed

---

### Requirement: SQLite Backup and Recovery (REMOVED)

**Reason**: SQLite backup procedures are removed. Only Milvus Lite backup is supported.

#### Scenario: Backup with SQLite database (legacy) (REMOVED)
- SQLite backup operations are removed

---

### Requirement: SQLite Cache Backend Selection (REMOVED)

**Reason**: Runtime selection of SQLite backend is removed.

#### Scenario: Select SQLite backend for backward compatibility (REMOVED)
- `LOREKEEPER_CACHE_BACKEND=sqlite` is no longer valid
- SQLiteCache instance creation is removed

---

### Requirement: SQLite Cache Factory Support (REMOVED)

**Reason**: Factory support for SQLite backend is removed.

#### Scenario: Factory function interface (MODIFIED)
- Factory no longer returns SQLiteCache for "sqlite"
- Only "milvus" is valid, "sqlite" raises ValueError

#### Scenario: Factory error handling (MODIFIED)
- Invalid backend error message updated: only "milvus" is supported
- "sqlite" is now treated as invalid
