# Entity-Based Cache Architecture Design

## Overview

This design replaces the current URL-based cache with an entity-centric approach where each D&D game entity (spell, monster, weapon, etc.) is stored individually in type-specific tables with the entity's slug as the primary key. This enables efficient parallel cache queries, offline fallback, and infinite TTL for valid data.

## Architectural Decisions

### 1. Entity-Based Storage

**Decision**: Create separate tables for each entity type (spells, monsters, weapons, armor, classes, races, backgrounds, feats, conditions, rules) with slug as primary key.

**Rationale**:
- Enables lookup by entity ID without knowing the URL
- Supports efficient bulk queries (e.g., "get all cached spells with level 3")
- Allows partial cache hits when some entities exist and others don't
- Provides better cache utilization (don't invalidate entire response when one entity changes)

### 2. Infinite TTL for Valid Responses

**Decision**: Valid API responses have no expiration time. Data is only updated when API returns newer content (based on last_modified timestamp or version).

**Rationale**:
- D&D game rules and entities rarely change once published
- Cache becomes a reliable offline knowledge base
- Reduces API calls to near-zero after initial data population
- Still allows updates when APIs provide newer data

### 3. Parallel Cache Queries

**Decision**: When API client makes a request, query cache in parallel with API call. Merge results and cache any new entities.

**Rationale**:
- Maximizes cache utilization without adding latency
- Gracefully handles partial cache hits
- Provides best-effort performance even during API slowdowns
- Enables progressive cache building

### 4. Offline Fallback Strategy

**Decision**: On network errors, serve exclusively from cache. Return partial results if some entities are cached.

**Rationale**:
- Enables offline usage for cached data
- Degrades gracefully during API outages
- Provides better user experience than hard failures
- Cache becomes authoritative source when API unavailable

### 5. Schema Design

**Decision**: Use normalized SQLite schema with one table per entity type, all sharing common structure:

```sql
CREATE TABLE spells (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data TEXT NOT NULL,  -- JSON blob of full entity
    source_api TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    -- Entity-specific indexed fields for filtering
    level INTEGER,
    school TEXT,
    concentration BOOLEAN,
    ritual BOOLEAN
);

CREATE TABLE monsters (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    source_api TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    -- Monster-specific indexed fields
    challenge_rating TEXT,
    type TEXT,
    size TEXT
);

-- Similar tables for: weapons, armor, classes, races,
-- backgrounds, feats, conditions, rules, rule_sections
```

**Rationale**:
- Slug (URL-safe identifier) is stable and unique per entity
- JSON blob stores complete entity for flexibility
- Indexed fields enable efficient filtering queries
- No foreign keys needed (D&D entities are mostly independent)

### 6. Cache Query Flow

**New flow for API client methods:**

```python
async def get_spells(self, **filters) -> list[Spell]:
    # 1. Start parallel operations
    cache_task = asyncio.create_task(query_cached_spells(**filters))
    api_task = asyncio.create_task(fetch_from_api(**filters))

    try:
        # 2. Wait for both with timeout
        cached, api_result = await asyncio.gather(
            cache_task,
            api_task,
            return_exceptions=True
        )
    except NetworkError:
        # 3. Offline fallback: use cache only
        cached = await cache_task
        return cached or []

    # 4. Merge results: API takes precedence, cache fills gaps
    merged = merge_entities(cached, api_result)

    # 5. Update cache with new/updated entities
    await bulk_cache_entities(api_result)

    return merged
```

**Rationale**:
- Concurrent cache+API queries minimize latency
- Network errors don't prevent returning cached data
- API results override stale cache when available
- Progressive cache improvement over time

### 7. Cache Statistics

**Decision**: Add cache statistics tracking for observability:
- Hit rate per entity type
- Total entities cached per type
- Cache size on disk
- Last API sync time per entity type
- Offline fallback usage count

**Rationale**:
- Enables monitoring of cache effectiveness
- Helps identify cache warming opportunities
- Provides insight into offline usage patterns
- Supports operational debugging

## Technology Choices

- **SQLite with WAL mode**: Already in use, supports concurrent reads
- **aiosqlite**: Already in use for async operations
- **JSON blob storage**: Balance between structure and flexibility
- **Indexed query fields**: Common filters materialized for performance
- **asyncio.gather**: Built-in parallel task execution

## Cache Management Operations

### Bulk Operations
```python
async def bulk_cache_entities(entities: list[BaseModel], entity_type: str) -> int
async def query_cached_entities(entity_type: str, **filters) -> list[dict]
async def get_cached_entity(entity_type: str, slug: str) -> dict | None
```

### Statistics & Maintenance
```python
async def get_cache_stats() -> dict[str, Any]
async def get_entity_count(entity_type: str) -> int
async def clear_entity_cache(entity_type: str) -> int
```

### Migration
```python
async def migrate_cache_schema() -> None  # Drop old table, create new tables
```

## Directory Structure

```
src/lorekeeper_mcp/cache/
├── __init__.py          # Public API exports
├── db.py                # Core cache operations (rewritten)
├── schema.py            # Table schemas and migrations
└── stats.py             # Statistics and health checks

tests/test_cache/
├── __init__.py
├── test_db.py           # Core cache operation tests (rewritten)
├── test_schema.py       # Schema creation and migration tests
└── test_stats.py        # Statistics tests
```

## Trade-offs Considered

### Entity Tables vs Single Table
**Trade-off**: Multiple tables increase schema complexity vs better performance and clarity
**Decision**: Multiple tables for type safety and optimized indexes

### JSON Blob vs Normalized Columns
**Trade-off**: JSON adds parsing overhead vs schema flexibility
**Decision**: Hybrid approach - JSON for full data, indexed columns for common filters

### Parallel Query vs Sequential
**Trade-off**: Parallel adds complexity vs better performance
**Decision**: Parallel for user-facing performance gains

### Infinite TTL vs Expiration
**Trade-off**: Infinite TTL means stale data risk vs reduced API calls
**Decision**: Infinite TTL with API-driven updates (D&D data rarely changes)

## Migration Strategy

1. **Create new tables** alongside old `api_cache` table
2. **Run both systems** briefly to validate new cache
3. **Drop old table** after validation period
4. **No data migration** - fresh cache build (acceptable since it's just a cache)

## Future Extensibility

- Easy to add new entity types (just add new table schema)
- Statistics framework supports adding new metrics
- Query API can be extended with advanced filters
- Schema versioning support for future migrations
- Could add cache warming based on usage patterns
