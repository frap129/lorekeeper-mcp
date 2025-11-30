## Why

Range filter parameters (`level_min`, `level_max`) are silently ignored by the Milvus cache when combined with semantic search. The `_build_filter_expression()` method only handles exact equality matches, treating `level_min=4` as `level_min == 4` (a non-existent field) instead of `level >= 4`. This causes searches like `search_spell(search="fire", level_min=4)` to return empty results even when matching spells exist.

## What Changes

- Update `MilvusCache._build_filter_expression()` to recognize and convert range filter patterns:
  - `level_min` → `level >= value`
  - `level_max` → `level <= value`
  - Generic `{field}_min` → `{field} >= value`
  - Generic `{field}_max` → `{field} <= value`
- Add corresponding unit tests for range filter behavior

## Impact

- Affected specs: `entity-cache`
- Affected code: `src/lorekeeper_mcp/cache/milvus.py` (`_build_filter_expression` method)
- No breaking changes - this fixes existing documented behavior that wasn't working
