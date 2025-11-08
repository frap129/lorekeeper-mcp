# marqo-cache-implementation Specification

**Spec ID**: `marqo-cache-implementation`
**Change**: `2025-11-08-replace-sqlite-with-marqo`
**Status**: Proposed

## Purpose

Replace SQLite-based entity caching with Marqo to provide unified document storage and enable vector similarity search capabilities.

## ADDED Requirements

### Requirement: Marqo client connection management

The system SHALL provide a singleton Marqo client manager for connection lifecycle management.

**Rationale**: Efficient connection reuse, lazy initialization for testing, simple lifecycle management.

#### Scenario: Get Marqo client singleton

**Given** the Marqo service is running at `http://localhost:8882`
**When** `MarqoClientManager.get_client()` is called multiple times
**Then** the same client instance is returned each time
**And** only one connection to Marqo exists

#### Scenario: Health check detects Marqo availability

**Given** the Marqo service is running
**When** `check_marqo_health()` is called
**Then** the function returns `True`
**And** no exceptions are raised

#### Scenario: Health check handles Marqo unavailable

**Given** the Marqo service is not running
**When** `check_marqo_health()` is called
**Then** the function returns `False`
**And** the function logs a warning
**And** no exceptions propagate to caller

---

### Requirement: Index initialization for entity types

The system SHALL create Marqo indexes for all D&D entity types with appropriate settings.

**Rationale**: Separate indexes per entity type allow independent tuning, clear separation of concerns, and different tensor field configurations.

#### Scenario: Initialize all entity type indexes

**Given** Marqo service is running
**And** no indexes exist
**When** `init_indexes()` is called
**Then** indexes are created for all entity types:
- `lorekeeper-spells`
- `lorekeeper-monsters`
- `lorekeeper-weapons`
- `lorekeeper-armor`
- `lorekeeper-classes`
- `lorekeeper-races`
- `lorekeeper-backgrounds`
- `lorekeeper-feats`
- `lorekeeper-conditions`
- `lorekeeper-rules`
- `lorekeeper-rule-sections`

#### Scenario: Configure index with embedding model

**Given** an entity type "spells"
**When** the index is created
**Then** the index uses model `hf/e5-base-v2`
**And** embedding normalization is enabled
**And** text preprocessing is configured for sentence splitting

#### Scenario: Define tensor fields per entity type

**Given** an entity type "spells"
**When** documents are indexed
**Then** fields `["name", "desc", "higher_level"]` are embedded as vectors
**And** all other fields are stored as metadata

---

### Requirement: Bulk entity indexing

The system SHALL support efficient bulk indexing of D&D entities using Marqo's batch API.

**Rationale**: Batch operations minimize network overhead and improve indexing performance when processing API responses with hundreds of entities.

#### Scenario: Bulk index spell entities

**Given** a list of 50 spell dictionaries with `slug`, `name`, and `desc` fields
**When** `bulk_cache_entities(spells, "spells", source_api="open5e")` is called
**Then** all 50 spells are indexed in Marqo
**And** the function returns `50`
**And** each spell is searchable by slug
**And** the operation completes in a single API request

#### Scenario: Bulk indexing validates entity type

**Given** an invalid entity type "invalid_type"
**When** `bulk_cache_entities([], "invalid_type")` is called
**Then** a `ValueError` is raised
**And** no documents are indexed

#### Scenario: Bulk indexing skips entities without slug

**Given** a list with one entity missing the `slug` field
**And** two valid entities with slugs
**When** `bulk_cache_entities(entities, "spells")` is called
**Then** only the 2 valid entities are indexed
**And** the function returns `2`
**And** a warning is logged for the skipped entity

---

### Requirement: Single entity retrieval by slug

The system SHALL retrieve cached entities from Marqo by slug (primary key).

**Rationale**: Fast O(1) lookups by unique identifier for exact-match queries.

#### Scenario: Retrieve existing entity by slug

**Given** a spell with slug "fireball" is indexed in Marqo
**When** `get_cached_entity("spells", "fireball")` is called
**Then** the complete spell document is returned
**And** the document contains all original fields
**And** the response time is < 50ms

#### Scenario: Handle entity not found

**Given** no entity with slug "nonexistent" exists
**When** `get_cached_entity("spells", "nonexistent")` is called
**Then** `None` is returned
**And** no exception is raised

#### Scenario: Validate entity type on retrieval

**Given** an invalid entity type "invalid"
**When** `get_cached_entity("invalid", "some-slug")` is called
**Then** a `ValueError` is raised with message containing "Invalid entity type"

---

### Requirement: Query entities with metadata filters

The system SHALL support querying cached entities using Marqo's filter syntax for structured field matching.

**Rationale**: Maintain existing filtering capabilities (level, school, CR) while adding semantic search.

#### Scenario: Filter spells by level and school

**Given** 10 spells are indexed with various levels and schools
**And** 3 spells have `level=3` and `school="Evocation"`
**When** `query_cached_entities("spells", level=3, school="Evocation")` is called
**Then** exactly 3 spells are returned
**And** all returned spells match both filter criteria

#### Scenario: Filter monsters by challenge rating

**Given** monsters are indexed with various CRs
**When** `query_cached_entities("monsters", challenge_rating=5.0)` is called
**Then** only monsters with CR=5.0 are returned
**And** the results are sorted by relevance

#### Scenario: Query with no filters returns all entities

**Given** 20 spells are indexed
**When** `query_cached_entities("spells")` is called
**Then** all 20 spells are returned

#### Scenario: Validate filter fields against allowlist

**Given** entity type "spells" with indexed fields `["level", "school"]`
**When** `query_cached_entities("spells", invalid_field="value")` is called
**Then** a `ValueError` is raised
**And** the error message lists allowed filter fields

---

### Requirement: Entity count and statistics

The system SHALL provide cache statistics including entity counts per type and index health metrics.

**Rationale**: Observability for cache population, debugging, and monitoring.

#### Scenario: Get entity count for populated type

**Given** 100 spells are indexed
**When** `get_entity_count("spells")` is called
**Then** the function returns `100`

#### Scenario: Get entity count for empty index

**Given** no monsters are indexed
**When** `get_entity_count("monsters")` is called
**Then** the function returns `0`
**And** no exception is raised

#### Scenario: Get comprehensive cache statistics

**Given** 100 spells, 50 monsters, and 30 weapons are indexed
**When** `get_cache_stats()` is called
**Then** a dictionary is returned containing:
- `entity_counts`: `{"spells": 100, "monsters": 50, "weapons": 30, ...}`
- `total_entities`: `180`
- `index_count`: number of active indexes

---

### Requirement: Graceful degradation when Marqo unavailable

The system SHALL gracefully handle Marqo service unavailability with appropriate fallbacks and error logging.

**Rationale**: System should not crash when Marqo is down; fallback to direct API calls.

#### Scenario: Cache miss falls back to API

**Given** Marqo service is unavailable
**When** `get_cached_entity("spells", "fireball")` is called
**Then** the system attempts to fetch from API
**And** a warning is logged: "Marqo unavailable, fetching from API"
**And** the API result is returned (if available)

#### Scenario: Indexing fails gracefully

**Given** Marqo service is unavailable
**When** `bulk_cache_entities(spells, "spells")` is called
**Then** an error is logged
**And** the function returns `0`
**And** no exception propagates to caller

---

### Requirement: Configuration via environment variables

The system SHALL support Marqo connection configuration through environment variables.

**Rationale**: Deployment flexibility, different environments (dev/staging/prod), easy configuration management.

#### Scenario: Load Marqo URL from environment

**Given** environment variable `MARQO_URL=http://marqo-prod:8882`
**When** settings are loaded
**Then** `settings.marqo_url` equals `"http://marqo-prod:8882"`

#### Scenario: Use default Marqo URL when not configured

**Given** no `MARQO_URL` environment variable is set
**When** settings are loaded
**Then** `settings.marqo_url` equals `"http://localhost:8882"` (default)

#### Scenario: Configure batch size

**Given** environment variable `MARQO_BATCH_SIZE=200`
**When** settings are loaded
**Then** `settings.marqo_batch_size` equals `200`

---

## MODIFIED Requirements

None - This is a new implementation replacing SQLite.

---

## REMOVED Requirements

### Requirement: SQLite database schema initialization

**Removed**: The system no longer uses SQLite for caching. All SQLite-related requirements are removed.

**Impact**:
- `init_db()` function removed
- `aiosqlite` dependency removed
- `cache.db` file no longer created
- All SQLite schema definitions removed

**Migration**: Data will be re-indexed from APIs into Marqo.

---

### Requirement: TTL-based cache expiration

**Removed**: Marqo indexes do not use TTL; entities persist indefinitely until explicitly deleted or updated.

**Rationale**: D&D content is relatively static; no need for expiration. Marqo handles storage efficiently.

**Migration**: No equivalent - entities cached permanently. Clean up indexes manually if needed.

---

## Cross-References

- Related Spec: `marqo-semantic-search` - Builds on this caching layer for vector search
- Related Spec: `marqo-infrastructure` - Deployment and operational requirements

---

## Notes

- Marqo service must be running before cache operations
- Initial index creation may take time depending on entity count
- Indexes can be rebuilt without data loss (re-fetch from APIs)
- Performance targets: <50ms for get_cached_entity, <100ms for filtered queries
