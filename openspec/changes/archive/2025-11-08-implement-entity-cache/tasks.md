# Implementation Tasks

## Phase 1: Cache Schema & Core Operations (Foundation)

### Task 1.1: Define entity table schemas
- Create `src/lorekeeper_mcp/cache/schema.py`
- Define table schemas for all entity types (spells, monsters, weapons, armor, classes, races, backgrounds, feats, conditions, rules, rule_sections)
- Define indexed fields per entity type for common filters
- Add schema version constant for future migrations
- **Validation**: Schema file imports without errors, all table definitions are valid SQL

### Task 1.2: Implement schema initialization and migration
- Add `init_entity_cache()` function to create all entity tables
- Add `migrate_cache_schema()` to drop old `api_cache` table and create new tables
- Enable WAL mode for concurrent access
- Create indexes on filtered fields
- **Validation**: Run init against empty DB, verify all tables created with `sqlite3 data/cache.db ".tables"`

### Task 1.3: Implement entity storage operations
- Add `bulk_cache_entities(entities, entity_type)` for bulk insert/update
- Add `get_cached_entity(entity_type, slug)` for single entity retrieval
- Implement upsert logic (INSERT OR REPLACE) to handle duplicates
- Store JSON blob with full entity data
- Extract and store indexed fields from entity models
- **Validation**: Unit tests for bulk insert, single get, upsert behavior

### Task 1.4: Implement entity query operations
- Add `query_cached_entities(entity_type, **filters)` for filtered queries
- Build dynamic WHERE clauses from filter parameters
- Support multiple filter combinations with AND logic
- Return empty list when no matches found
- **Validation**: Unit tests for various filter combinations, empty results

## Phase 2: Cache Statistics & Observability

### Task 2.1: Implement entity count statistics
- Add `get_entity_count(entity_type)` to count entities per table
- Handle non-existent tables gracefully
- **Validation**: Test with empty tables, populated tables, non-existent types

### Task 2.2: Implement comprehensive cache statistics
- Add `get_cache_stats()` to return dict with all statistics
- Include entity counts per type
- Include database file size
- Include table count and schema version
- **Validation**: Test returns complete stats dict with correct structure

## Phase 3: Base Client Integration

### Task 3.1: Add parallel cache query support to BaseHttpClient
- Import entity cache functions in `base.py`
- Add `_query_cache_parallel(entity_type, filters)` method
- Implement asyncio.gather for parallel cache + API queries
- Handle exceptions from either task gracefully
- **Validation**: Unit tests verify parallel execution timing, exception handling

### Task 3.2: Implement entity caching from API responses
- Add `_extract_entities(response, entity_type)` to parse API responses
- Add `_cache_api_entities(entities, entity_type)` to bulk cache after API call
- Modify `make_request()` to cache entities instead of URL responses
- Extract slug from entity for cache key
- **Validation**: Integration test confirms entities cached after API call

### Task 3.3: Implement offline fallback logic
- Modify `make_request()` to catch NetworkError
- On network error, return cached entities exclusively
- Log warnings about offline mode
- Return empty list if no cache data available
- **Validation**: Tests with mocked network failures return cached data

### Task 3.4: Implement cache-first mode
- Add `cache_first` parameter to `make_request()`
- When enabled, return cache immediately and start background API refresh
- Use asyncio.create_task for background refresh
- Update cache asynchronously without blocking caller
- **Validation**: Test verifies immediate cache return, background refresh completes

## Phase 4: API Client Updates

### Task 4.1: Update Open5eV1Client for entity caching
- Modify `get_monsters()` to use entity-based caching
- Modify other methods (classes, races, magic_items) similarly
- Pass entity_type to base client for proper table routing
- **Validation**: Integration tests verify entities cached and retrieved per type

### Task 4.2: Update Open5eV2Client for entity caching
- Update all methods (spells, weapons, armor, backgrounds, feats, conditions)
- Ensure entity_type matches cache table names
- **Validation**: Integration tests for each entity type

### Task 4.3: Update Dnd5eApiClient for entity caching (if implemented)
- Update rules and reference data methods
- Handle entity caching for rules, rule_sections
- **Validation**: Integration tests confirm proper caching

## Phase 5: Testing & Documentation

### Task 5.1: Write comprehensive cache unit tests
- Rewrite `tests/test_cache/test_db.py` for entity-based operations
- Add `tests/test_cache/test_schema.py` for schema and migration tests
- Add `tests/test_cache/test_stats.py` for statistics tests
- Achieve >90% coverage on cache layer
- **Validation**: `pytest tests/test_cache/ -v --cov=src/lorekeeper_mcp/cache`

### Task 5.2: Update API client integration tests
- Update `tests/test_api_clients/test_base.py` for parallel caching
- Update client-specific tests for entity caching behavior
- Add offline fallback test scenarios
- Test cache-first mode
- **Validation**: All integration tests pass with new caching

### Task 5.3: Manual cache validation and testing
- Run server and make real API calls
- Verify entities cached in correct tables
- Test offline mode by disconnecting network
- Verify cache statistics are accurate
- **Validation**: Manual testing checklist completed, cache working as expected

### Task 5.4: Update documentation
- Update `docs/cache.md` with entity-based caching architecture
- Document cache schema and table structure
- Add examples of using cache statistics
- Document migration from old cache
- **Validation**: Documentation review, no broken references

## Dependencies

- **Parallel work**: Tasks 1.1-1.4 must complete before Phase 2
- **Sequential**: Phase 2 can run parallel to Phase 3.1
- **Blocker**: Phase 3 must complete before Phase 4
- **Final**: Phase 5 requires all previous phases complete

## Verification Checklist

- [ ] All entity tables created successfully
- [ ] Bulk insert handles 100+ entities efficiently
- [ ] Filters work correctly for all entity types
- [ ] Parallel cache queries reduce latency vs sequential
- [ ] Offline mode serves cached data without errors
- [ ] Cache statistics accurate and complete
- [ ] Unit test coverage >90% for cache layer
- [ ] Integration tests pass for all API clients
- [ ] Manual testing confirms end-to-end functionality
- [ ] Documentation updated and accurate
