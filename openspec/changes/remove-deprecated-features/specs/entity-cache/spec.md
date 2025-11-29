## REMOVED Requirements

### Requirement: Support both creatures and monsters table names

**Reason**: The deprecation period for the "monsters" table alias has passed. The canonical table name is `creatures`, aligning with Open5e v2 terminology and the Creature model. All code should use "creatures" directly.

**Migration**: Replace all references to "monsters" entity type with "creatures":
- Change `query_cached_entities("monsters", ...)` to `query_cached_entities("creatures", ...)`
- Change `bulk_cache_entities(entities, "monsters")` to `bulk_cache_entities(entities, "creatures")`

#### Scenario: Monsters table name no longer supported
- **GIVEN** code querying for "monsters" entity type
- **WHEN** calling `query_cached_entities("monsters")`
- **THEN** a `ValueError` is raised with message "Unknown entity type 'monsters'. Did you mean 'creatures'?"
- **AND** no deprecation warning is logged (the feature is removed, not deprecated)

---

### Requirement: SQLite cache backend

**Reason**: SQLite cache backend is deprecated. Milvus is the only supported cache backend, providing semantic/vector search capabilities required for the semantic-only search architecture.

**Migration**:
- Remove all `SQLiteCache` usage
- Remove `backend="sqlite"` from `create_cache()` calls
- Remove `LOREKEEPER_CACHE_BACKEND=sqlite` environment variable usage

#### Scenario: SQLite backend no longer available
- **GIVEN** code calling `create_cache(backend="sqlite")`
- **WHEN** the function is executed
- **THEN** a `ValueError` is raised with message "Unknown cache backend: 'sqlite'. Only 'milvus' is supported."
- **AND** no SQLiteCache class exists in the cache module
