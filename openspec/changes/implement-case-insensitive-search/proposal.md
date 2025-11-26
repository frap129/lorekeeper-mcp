## Why

The enhanced search specification requires case-insensitive name matching via `LOWER(name) = LOWER(?)` SQL queries, wildcard partial matching (`fire*`), and automatic slug fallback. However, the current implementation uses exact equality matching (`field = ?`) in the cache layer, making case-insensitive searches impossible at the database level. This is a critical gap (P0) that prevents the documented search features from working.

## What Changes

- **BREAKING**: Modify cache query layer to support case-insensitive matching using `LOWER()` SQL function
- Add `LOWER(name)` indexes to all entity tables for query performance
- Implement wildcard detection and LIKE query generation in cache layer
- Implement automatic slug fallback when name search returns no results
- Add filter operators beyond simple equality (LIKE, case-insensitive)

## Impact

- Affected specs: `database-setup`, `enhanced-search`
- Affected code:
  - `src/lorekeeper_mcp/cache/db.py` - query_cached_entities() needs operator support
  - `src/lorekeeper_mcp/cache/schema.py` - add LOWER(name) index creation
  - `src/lorekeeper_mcp/repositories/base.py` - may need wildcard/fallback logic
