# cache-builder-orchestration Specification

**Spec ID**: `cache-builder-orchestration`
**Change**: `implement-build-cache-flag`
**Status**: Proposed

## Purpose

Implement cache building orchestration that fetches all D&D entities from multiple API sources and populates the Marqo cache in an efficient, resilient manner.

## ADDED Requirements

### Requirement: Cache builder entry point

The system SHALL provide a main cache building function that orchestrates the entire build process.

**Rationale**: Single entry point simplifies testing, error handling, and progress reporting.

#### Scenario: Build complete cache from all APIs

**Given** Marqo service is running
**And** external APIs are reachable
**When** `build_cache()` is called
**Then** all entity types are fetched from all configured API clients
**And** entities are indexed to Marqo
**And** a build summary is logged
**And** the function returns exit code `0`

#### Scenario: Return non-zero exit code on critical failure

**Given** Marqo service is unavailable
**When** `build_cache()` is called
**Then** an error is logged
**And** the function returns exit code `1`
**And** no API calls are made (fail fast)

---

### Requirement: Multi-client API orchestration

The system SHALL fetch entities from all configured API clients in parallel.

**Rationale**: Parallel fetching reduces total build time by 2-3x compared to sequential processing.

#### Scenario: Initialize all API clients

**Given** cache builder starts
**When** API clients are initialized
**Then** the following clients are created:
- `Open5eV2Client` (spells, weapons, armor, backgrounds, feats, conditions)
- `Open5eV1Client` (monsters, classes, races)
- `DnD5eAPIClient` (rules, rule_sections)
**And** each client is configured with default timeout and retry settings

#### Scenario: Fetch entities from multiple clients in parallel

**Given** all API clients are initialized
**When** entity fetching begins
**Then** each client fetches its entity types concurrently
**And** fetch operations run in parallel using `asyncio.gather()`
**And** total fetch time is approximately max(client_times) not sum(client_times)

#### Scenario: Handle individual client failures gracefully

**Given** `Open5eV1Client` fails to fetch monsters
**And** other clients succeed
**When** cache building continues
**Then** monsters are skipped with a warning logged
**And** other entity types are indexed successfully
**And** the build completes with exit code `0` (partial success)

---

### Requirement: Pagination handling for complete entity lists

The system SHALL fetch all pages from paginated API endpoints to retrieve complete entity lists.

**Rationale**: APIs return paginated responses (e.g., 50 items per page); all pages must be fetched for complete cache.

#### Scenario: Fetch all pages from paginated endpoint

**Given** the spells API endpoint returns paginated responses
**And** page 1 has 50 spells and a "next" URL
**And** page 2 has 30 spells and no "next" URL
**When** `fetch_all_spells()` is called
**Then** page 1 is fetched
**And** page 2 is fetched using the "next" URL
**And** all 80 spells are returned
**And** 2 API requests are made

#### Scenario: Handle non-paginated responses

**Given** an API endpoint returns a direct entity (no "results" field)
**When** entity fetching occurs
**Then** the single entity is returned in a list
**And** no additional pages are requested

#### Scenario: Handle empty pages gracefully

**Given** an API endpoint returns an empty "results" array
**When** entity fetching occurs
**Then** an empty list is returned
**And** a warning is logged
**And** no error is raised

---

### Requirement: Entity aggregation across clients

The system SHALL aggregate entities by type, handling cases where multiple clients provide the same entity type.

**Rationale**: Some entity types may be available from multiple sources (e.g., spells from multiple APIs); aggregation prevents duplicates and ensures completeness.

#### Scenario: Aggregate entities by type

**Given** `Open5eV2Client` returns 520 spells
**And** `Open5eV1Client` returns 0 spells
**When** entities are aggregated
**Then** the "spells" entry contains 520 unique entities
**And** duplicates (same slug) are deduplicated with later entries taking precedence

#### Scenario: Deduplicate entities by slug

**Given** two clients return entities with the same slug "fireball"
**And** client A returns version with `source_api="open5e_v2"`
**And** client B returns version with `source_api="open5e_v1"`
**When** entities are aggregated
**Then** only one "fireball" entity is retained
**And** the retained entity is from the last client processed (deterministic ordering)

---

### Requirement: Batch indexing to Marqo

The system SHALL index entities to Marqo in batches to optimize performance and memory usage.

**Rationale**: Batch indexing (100 docs at a time) is recommended by Marqo for optimal throughput.

#### Scenario: Index entities in batches of 100

**Given** 520 spells are fetched
**When** indexing to Marqo occurs
**Then** spells are batched into groups of 100
**And** 6 batch requests are made (5 full batches + 1 partial batch of 20)
**And** all 520 spells are indexed

#### Scenario: Handle indexing failures for individual batches

**Given** a batch of 100 entities
**And** Marqo rejects the 3rd batch due to a transient error
**When** indexing occurs
**Then** the 1st and 2nd batches succeed
**And** the 3rd batch is retried once
**And** if retry fails, an error is logged
**And** remaining batches are processed
**And** build continues with partial success

---

### Requirement: Marqo index initialization

The system SHALL ensure all Marqo indexes exist before building the cache.

**Rationale**: Indexing documents requires indexes to be created first with proper settings (embedding model, tensor fields, etc.).

#### Scenario: Initialize Marqo indexes before building

**Given** Marqo is running
**And** no indexes exist
**When** cache builder starts
**Then** `init_indexes()` is called
**And** all 11 entity type indexes are created
**And** indexes are configured with proper settings (hf/e5-base-v2 model, tensor fields)

#### Scenario: Skip index creation if indexes already exist

**Given** all Marqo indexes already exist
**When** cache builder starts
**Then** `init_indexes()` is called
**And** existing indexes are detected
**And** no duplicate indexes are created
**And** indexing proceeds immediately

---

### Requirement: Fetch-all API methods for each client

The system SHALL add `fetch_all_*()` methods to each API client for fetching complete entity lists.

**Rationale**: Existing `get_*()` methods are designed for filtered queries, not complete fetching; new methods handle pagination explicitly.

#### Scenario: Open5eV2Client provides fetch_all methods

**Given** `Open5eV2Client` is initialized
**When** cache builder queries available methods
**Then** the following methods exist:
- `fetch_all_spells()`
- `fetch_all_weapons()`
- `fetch_all_armor()`
- `fetch_all_backgrounds()`
- `fetch_all_feats()`
- `fetch_all_conditions()`

#### Scenario: Open5eV1Client provides fetch_all methods

**Given** `Open5eV1Client` is initialized
**When** cache builder queries available methods
**Then** the following methods exist:
- `fetch_all_monsters()`
- `fetch_all_classes()`
- `fetch_all_races()`

#### Scenario: DnD5eAPIClient provides fetch_all methods

**Given** `DnD5eAPIClient` is initialized
**When** cache builder queries available methods
**Then** the following methods exist:
- `fetch_all_rules()`
- `fetch_all_rule_sections()`

---

### Requirement: Error resilience and partial build support

The system SHALL continue building cache even when individual entity types or clients fail.

**Rationale**: Partial cache is better than no cache; transient API failures shouldn't halt entire build.

#### Scenario: Continue build when single entity type fails

**Given** spells fetch succeeds
**And** monsters fetch fails due to API timeout
**And** weapons fetch succeeds
**When** cache building continues
**Then** spells and weapons are indexed
**And** monsters are skipped with an error logged
**And** exit code is `0` (partial success)

#### Scenario: Exit with failure when no entities are indexed

**Given** all API clients fail to fetch entities
**When** cache building completes
**Then** an error is logged: "Critical: No entities indexed"
**And** exit code is `1`

#### Scenario: Exit with failure when Marqo is unavailable

**Given** Marqo service is not running
**When** cache builder attempts to initialize indexes
**Then** an error is logged: "Marqo unavailable"
**And** exit code is `1`
**And** no API calls are made (fail fast)

---

## MODIFIED Requirements

### Requirement: API clients SHALL support pagination for complete fetches

The system SHALL add new `fetch_all_*()` methods to each API client that handle pagination explicitly without filtering.

**Modified From**: Existing API client methods (get_spells, get_monsters, etc.) support filtered queries with optional caching.

**Change**: Add new `fetch_all_*()` methods that handle pagination explicitly without filtering.

**Rationale**: Separation of concerns - existing methods for filtered queries, new methods for complete fetches.

**Impact**: No breaking changes; existing methods unchanged. New methods are additive.

#### Scenario: Fetch all entities with new method

**Given** an API client (Open5eV2Client, Open5eV1Client, or DnD5eAPIClient)
**When** a `fetch_all_*()` method is called (e.g., `fetch_all_spells()`)
**Then** all pages are fetched automatically
**And** a complete list of entities is returned
**And** existing `get_*()` methods continue to work unchanged

---

## REMOVED Requirements

None - no functionality is removed.

---

## Cross-References

- Related Spec: `cache-builder-cli` - CLI interface that invokes this orchestration logic
- Related Spec: `cache-builder-progress` - Progress reporting emitted during orchestration
- Related Spec: `marqo-cache-implementation` (from `replace-sqlite-with-marqo`) - Marqo cache functions used for indexing

---

## Notes

- Entity counts are approximate based on current API data (may change over time)
- Parallel fetching uses `asyncio.gather()` with `return_exceptions=True` for resilience
- Batch size of 100 is configurable via `CACHE_BUILD_BATCH_SIZE` environment variable
- Deduplication uses last-write-wins strategy based on client processing order
- All `fetch_all_*()` methods bypass caching (`use_cache=False`) to ensure fresh data
