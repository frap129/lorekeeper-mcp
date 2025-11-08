# Design Document: --build-cache Flag Implementation

## Overview

This document details the design for adding a `--build-cache` CLI flag that fetches all D&D entities from configured APIs and populates the Marqo cache before starting the server.

## Architecture

### Current Architecture (Post-Marqo Migration)

```
┌──────────────┐
│ MCP Server   │
│ (__main__.py)│
└──────┬───────┘
       │
       │ mcp.run()
       v
┌──────────────┐      ┌─────────────┐
│ FastMCP      │─────>│ Marqo Cache │
│ (server.py)  │      │ (lazy load) │
└──────────────┘      └─────────────┘
```

### New Architecture (With --build-cache)

```
┌──────────────────┐
│ MCP Server       │
│ (__main__.py)    │
└──────┬───────────┘
       │
       │ argparse
       │
       ├─ --build-cache? ─ YES ─┐
       │                         │
       │                         v
       │                  ┌──────────────────┐
       │                  │ Cache Builder    │
       │                  │ (cache_builder.py)│
       │                  └──────┬───────────┘
       │                         │
       │                         v
       │                  ┌──────────────────┐      ┌─────────────┐
       │                  │ API Clients      │─────>│ External    │
       │                  │ - Open5eV1       │      │ APIs        │
       │                  │ - Open5eV2       │      └─────────────┘
       │                  │ - DnD5eAPI       │
       │                  └──────┬───────────┘
       │                         │
       │                         v
       │                  ┌─────────────┐
       │                  │ Marqo Cache │
       │                  │ (populated) │
       │                  └─────────────┘
       │                         │
       │                         │ exit(0)
       │                         v
       │
       └─ NO ───> mcp.run()
```

## Design Decisions

### 1. CLI Interface

**Decision**: Use argparse with `--build-cache` flag

**Interface**:
```bash
# Normal server mode
uv run lorekeeper-mcp

# Cache build mode
uv run lorekeeper-mcp --build-cache

# Help
uv run lorekeeper-mcp --help
```

**Rationale**:
- Standard Python CLI approach
- Self-documenting with `--help`
- Easy to extend with future flags
- No breaking changes to existing usage

### 2. Cache Builder Architecture

**Decision**: Separate `cache_builder.py` module with orchestration logic

**Module Structure**:
```python
# cache_builder.py

async def build_cache() -> int:
    """Build complete cache from all APIs.

    Returns:
        Exit code (0 = success, non-zero = failure)
    """
    pass

async def fetch_all_entities(client, entity_types: list[str]) -> dict[str, list[dict]]:
    """Fetch all entities from a single API client."""
    pass

async def index_entities_to_marqo(entities_by_type: dict[str, list[dict]]) -> None:
    """Index all entities into Marqo."""
    pass
```

**Rationale**:
- Clean separation from server code
- Testable in isolation
- Reusable for future CLI commands
- Clear responsibilities

### 3. API Client Orchestration

**Decision**: Fetch from all clients in parallel, aggregate results

**Clients to Query**:
```python
ENTITY_SOURCES = {
    "open5e_v2": {
        "client": Open5eV2Client,
        "entity_types": ["spells", "weapons", "armor", "backgrounds", "feats", "conditions"],
    },
    "open5e_v1": {
        "client": Open5eV1Client,
        "entity_types": ["monsters", "classes", "races"],
    },
    "dnd5e_api": {
        "client": DnD5eAPIClient,
        "entity_types": ["rules", "rule_sections"],
    },
}
```

**Fetch Strategy**:
1. Initialize all API clients
2. For each client:
   - Fetch all entity types in parallel
   - Handle pagination automatically
3. Aggregate entities by type across clients
4. Index to Marqo in batches

**Rationale**:
- Parallel fetching reduces total build time
- Clients already handle pagination and caching
- Aggregation handles overlapping entity types (e.g., spells from multiple sources)

### 4. Pagination Handling

**Decision**: Each client implements `fetch_all()` method for complete entity lists

**New Client Methods**:
```python
class Open5eV2Client:
    async def fetch_all_spells(self) -> list[Spell]:
        """Fetch ALL spells from API (handles pagination internally)."""
        all_spells = []
        next_url = "/spells/"
        while next_url:
            response = await self.make_request(next_url)
            all_spells.extend(response["results"])
            next_url = response.get("next")
        return all_spells
```

**Rationale**:
- Clients know their own pagination patterns
- Hides complexity from cache builder
- Reusable for other use cases

### 5. Progress Reporting

**Decision**: Log entity counts as they're indexed

**Progress Output**:
```
[INFO] Building cache from all APIs...
[INFO] Fetching spells from Open5e v2...
[INFO] Fetched 520 spells
[INFO] Indexing 520 spells to Marqo...
[INFO] ✓ Indexed 520 spells
[INFO] Fetching monsters from Open5e v1...
[INFO] Fetched 1043 monsters
[INFO] Indexing 1043 monsters to Marqo...
[INFO] ✓ Indexed 1043 monsters
...
[INFO] Cache build complete: 3427 total entities across 11 types
[INFO] Build time: 147.3s
```

**Rationale**:
- Simple logging, no dependencies
- Clear progress visibility
- Timestamped logs for debugging
- Easy to parse for automation

### 6. Error Handling

**Decision**: Continue on partial failures, exit non-zero if critical failure

**Error Types**:

| Error | Severity | Behavior |
|-------|----------|----------|
| Single entity fetch fails | Low | Log warning, continue |
| Single entity type fails | Medium | Log error, continue with other types |
| API client unavailable | Medium | Log error, skip client, continue |
| Marqo unavailable | Critical | Log error, exit with code 1 |
| Network completely down | Critical | Log error, exit with code 1 |

**Implementation**:
```python
failed_types = []

for entity_type in entity_types:
    try:
        entities = await fetch_entities(entity_type)
        await index_entities(entities, entity_type)
    except Exception as e:
        logger.error(f"Failed to build cache for {entity_type}: {e}")
        failed_types.append(entity_type)
        # Continue with next type

if failed_types:
    logger.warning(f"Partial build: {len(failed_types)} types failed")
    return 0  # Still exit success if some data indexed

if no_entities_indexed:
    logger.error("Critical: No entities indexed")
    return 1  # Exit failure
```

**Rationale**:
- Resilient to transient API failures
- Partial cache better than no cache
- Critical failures properly signaled to CI/CD
- Clear error reporting for debugging

### 7. Marqo Index Initialization

**Decision**: Automatically create indexes during cache build

**Initialization Flow**:
```python
async def init_marqo_indexes() -> None:
    """Ensure all Marqo indexes exist before building cache."""
    from lorekeeper_mcp.cache.marqo import init_indexes

    logger.info("Initializing Marqo indexes...")
    await init_indexes()
    logger.info("✓ Indexes ready")
```

**Rationale**:
- Indexes must exist before documents can be added
- Matches existing `init_db()` pattern from SQLite
- Idempotent (safe to call multiple times)

### 8. Exit Behavior

**Decision**: Exit after cache build completes (don't start server)

**Exit Codes**:
- `0`: Cache build successful (all or partial success)
- `1`: Critical failure (Marqo unavailable, no entities indexed)
- `2`: Invalid arguments

**Rationale**:
- Explicit separation of build vs run modes
- Easier to script (build, then start)
- Prevents unexpected server startup
- Clear success/failure for CI/CD

### 9. Testing Strategy

**Test Levels**:

1. **Unit Tests** (`test_cache_builder.py`):
   - Mock API clients
   - Test pagination logic
   - Test error handling
   - Test progress reporting

2. **Integration Tests** (existing `test_integration.py`):
   - Use real Marqo container
   - Mock external APIs
   - Validate entities in cache post-build

3. **Live Tests** (optional):
   - Real APIs + real Marqo
   - Validate full end-to-end flow
   - Measure build time/performance

**Mock Strategy**:
```python
@pytest.fixture
def mock_open5e_v2(respx_mock):
    """Mock Open5e v2 API with paginated responses."""
    respx_mock.get("https://api.open5e.com/v2/spells/").mock(
        return_value=httpx.Response(200, json={
            "results": [{"slug": "fireball", ...}],
            "next": None,
        })
    )
```

### 10. Configuration

**Decision**: Use existing environment variables, add build-specific overrides

**New Environment Variables**:
```bash
# Build-specific settings (optional)
CACHE_BUILD_TIMEOUT=600        # Timeout for entire build (seconds)
CACHE_BUILD_BATCH_SIZE=100     # Batch size for Marqo indexing
CACHE_BUILD_PARALLEL_FETCHES=3 # Max parallel API fetches per client
```

**Defaults**:
- Timeout: 600s (10 minutes)
- Batch size: 100 (Marqo recommended)
- Parallel fetches: 3 (conservative to avoid rate limits)

**Rationale**:
- Reuse existing config where possible
- Allow tuning for different environments
- Sensible defaults for most use cases

## Data Flow

### Cache Build Flow

```
1. Parse CLI args
   ├─ --build-cache? ─ NO ──> Start MCP server (existing flow)
   └─ --build-cache? ─ YES ──> Continue
                              │
2. Initialize Marqo           │
   └─ init_indexes() ─────────┤
                              │
3. Initialize API clients     │
   ├─ Open5eV2Client          │
   ├─ Open5eV1Client          │
   └─ DnD5eAPIClient ─────────┤
                              │
4. Fetch entities (parallel)  │
   ├─ open5e_v2:              │
   │  ├─ fetch_all_spells()   │
   │  ├─ fetch_all_weapons()  │
   │  └─ ... (6 types)        │
   ├─ open5e_v1:              │
   │  ├─ fetch_all_monsters() │
   │  ├─ fetch_all_classes()  │
   │  └─ fetch_all_races()    │
   └─ dnd5e_api:              │
      ├─ fetch_all_rules()    │
      └─ fetch_all_sections() │
                              │
5. Aggregate entities         │
   └─ Group by entity_type ───┤
                              │
6. Index to Marqo             │
   ├─ For each entity_type:   │
   │  ├─ Batch into groups    │
   │  └─ bulk_cache_entities()│
   └─ Log progress ───────────┤
                              │
7. Report summary             │
   ├─ Total entities: 3427    │
   ├─ Build time: 147.3s      │
   └─ Failed types: 0 ────────┤
                              │
8. Exit with status code      │
   └─ exit(0 or 1) ───────────●
```

## API Client Extensions

### New Methods Required

Each API client needs `fetch_all_*()` methods:

**Open5eV2Client**:
```python
async def fetch_all_spells(self) -> list[dict[str, Any]]:
async def fetch_all_weapons(self) -> list[dict[str, Any]]:
async def fetch_all_armor(self) -> list[dict[str, Any]]:
async def fetch_all_backgrounds(self) -> list[dict[str, Any]]:
async def fetch_all_feats(self) -> list[dict[str, Any]]:
async def fetch_all_conditions(self) -> list[dict[str, Any]]:
```

**Open5eV1Client**:
```python
async def fetch_all_monsters(self) -> list[dict[str, Any]]:
async def fetch_all_classes(self) -> list[dict[str, Any]]:
async def fetch_all_races(self) -> list[dict[str, Any]]:
```

**DnD5eAPIClient**:
```python
async def fetch_all_rules(self) -> list[dict[str, Any]]:
async def fetch_all_rule_sections(self) -> list[dict[str, Any]]:
```

**Generic Pagination Helper**:
```python
async def _fetch_all_paginated(
    self,
    endpoint: str,
    entity_type: str,
) -> list[dict[str, Any]]:
    """Generic helper to fetch all pages from a paginated endpoint."""
    all_entities = []
    next_url = endpoint

    while next_url:
        response = await self.make_request(
            next_url,
            use_cache=False,  # Always fetch fresh during build
        )

        if "results" in response:
            all_entities.extend(response["results"])
            next_url = response.get("next")
        else:
            # Direct entity response
            all_entities.append(response)
            break

    logger.info(f"Fetched {len(all_entities)} {entity_type}")
    return all_entities
```

## Performance Estimates

### Expected Build Times

| Entity Type | Count | Fetch Time | Index Time | Total |
|-------------|-------|------------|------------|-------|
| Spells | ~520 | 8s | 3s | 11s |
| Monsters | ~1043 | 20s | 6s | 26s |
| Weapons | ~50 | 2s | 1s | 3s |
| Armor | ~30 | 2s | 1s | 3s |
| Classes | ~13 | 2s | 1s | 3s |
| Races | ~9 | 1s | 1s | 2s |
| Backgrounds | ~13 | 2s | 1s | 3s |
| Feats | ~50 | 3s | 1s | 4s |
| Conditions | ~15 | 1s | 1s | 2s |
| Rules | ~20 | 2s | 1s | 3s |
| Rule Sections | ~100 | 5s | 2s | 7s |

**Total (Sequential)**: ~67s
**Total (Parallel, 3 clients)**: ~30-40s

### Optimization Opportunities

1. **Parallel client fetching**: 2-3x speedup (already in design)
2. **Larger batch sizes**: 10-20% speedup (careful with memory)
3. **Connection pooling**: 5-10% speedup (httpx already does this)
4. **Caching DNS lookups**: 2-3% speedup (minimal gain)

## Security Considerations

### Input Validation
- No user input during cache build
- Entity types validated against allowlist
- URLs validated by httpx

### Network Security
- HTTPS for all external API calls
- Marqo on localhost or private network
- No secrets in logs

### Resource Limits
- Max build timeout prevents runaway processes
- Memory bounded by batch processing
- Disk space checked before starting (future enhancement)

## Monitoring

### Metrics to Track
```python
# Build metrics
cache_build_duration_seconds
cache_build_entity_count{entity_type}
cache_build_failures{entity_type, error_type}
cache_build_success_total
```

### Logs to Emit
- Start/end timestamps
- Entity counts per type
- API response times
- Error details with tracebacks
- Final summary with exit code

## Rollback Plan

If `--build-cache` causes issues:
1. Flag is optional - existing usage unaffected
2. Revert commit if needed
3. Fallback to manual cache population (existing lazy-load)
4. No data loss (cache can be rebuilt anytime)

## Future Enhancements

1. **Incremental builds**: `--build-cache --incremental` (only fetch missing)
2. **Selective builds**: `--build-cache --types spells,monsters`
3. **Progress bar**: Rich terminal UI with progress bars
4. **Background building**: `--build-cache --background` (build in separate process)
5. **Scheduled refreshes**: Cron job support with `--build-cache --cron`
6. **Cache versioning**: Track API versions and rebuild when APIs update

## Conclusion

The `--build-cache` flag provides a simple, robust way to pre-populate the Marqo cache for offline usage, testing, and production deployments. The design prioritizes simplicity, error resilience, and clear progress reporting while maintaining separation from normal server operation.
