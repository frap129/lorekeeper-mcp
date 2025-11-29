## Why

The current MCP search tools have two overlapping text search parameters (`name` and `semantic_query`) which creates confusion for users who don't know when to use which. Since semantic search provides more powerful conceptual matching, we should consolidate to a single `search` parameter with semantic-only behavior.

## What Changes

- **BREAKING**: Remove `name` parameter from all 5 search tools (`search_spell`, `search_creature`, `search_equipment`, `search_character_option`, `search_rule`)
- **BREAKING**: Rename `semantic_query` parameter to `search` across all 5 search tools
- Update tool docstrings and examples to use the new `search` parameter
- Update repository layer to accept `search` instead of `semantic_query`

## Impact

- Affected specs: `mcp-tools`
- Affected code:
  - `src/lorekeeper_mcp/tools/search_*.py` (all 5 search tools)
  - `src/lorekeeper_mcp/repositories/*.py` (all repositories)
  - `tests/test_tools/*.py` (tool tests)
  - `tests/test_repositories/*.py` (repository tests)
- Breaking change: Existing callers using `name` or `semantic_query` parameters will need to migrate to `search`
