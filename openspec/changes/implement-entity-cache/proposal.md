# Implement Entity-Based Cache

## Why

The current caching implementation uses URLs as cache keys and stores entire API responses, which prevents efficient parallel cache lookups, offline fallback, and individual entity retrieval. This approach doesn't support the primary use case of looking up individual D&D entities (spells, monsters, items) by ID or querying subsets from cache when APIs are unavailable.

## What Changes

- Replace URL-based cache with entity-based cache using normalized tables (one per content type)
- Use entity slugs as primary keys instead of URLs
- Store each entity individually in type-specific tables (spells, monsters, weapons, armor, etc.)
- Implement parallel cache querying: check cache while making API calls, merge results
- Add offline fallback: serve from cache when APIs are unreachable
- Change TTL strategy: infinite TTL for valid responses, only update when API returns newer data
- Refactor BaseHttpClient to query cache in parallel and merge cache+API results
- Add cache statistics and health check capabilities
- Update all API client methods to leverage entity-based caching

## Impact

**Affected specs:**
- `entity-cache` (new capability) - entity-based storage with per-type tables
- `base-client` (modified) - parallel cache querying and offline fallback

**Affected code:**
- `src/lorekeeper_mcp/cache/db.py` - Complete rewrite for entity-based schema
- `src/lorekeeper_mcp/cache/schema.py` - New file defining entity table schemas
- `src/lorekeeper_mcp/api_clients/base.py` - Refactor to use parallel cache queries
- `src/lorekeeper_mcp/api_clients/open5e_v1.py` - Update to cache individual entities
- `src/lorekeeper_mcp/api_clients/open5e_v2.py` - Update to cache individual entities
- `tests/test_cache/` - Comprehensive rewrite for new entity-based tests
- `tests/test_api_clients/` - Update integration tests for parallel caching

**Breaking changes:**
- Existing cache database will be incompatible (migration needed or fresh DB)
- Cache function signatures will change (breaking API for cache layer)
