# Build API Clients

## Why

The LoreKeeper MCP server needs API clients to fetch D&D 5e game data from external APIs, but currently has no client implementations, preventing the tools from accessing any game data.

## What Changes

- Add async `BaseHttpClient` class with retry logic, rate limiting, and cache integration
- Add `Open5eV1Client` for monsters, classes, races, and magic items (3,207+ monsters, 12+ classes, 20+ races, 1,618+ items)
- Add `Open5eV2Client` for spells, weapons, armor, backgrounds, feats, and conditions (1,774+ spells, 75 weapons, 25 armor, 54 backgrounds, 91 feats, 21 conditions)
- Add `Dnd5eApiClient` for rules and reference data (6 rule categories, 33 rule sections, 8 reference endpoint types)
- Add Pydantic response models for data normalization across API versions
- Add `ClientFactory` for dependency injection and client instantiation
- Add comprehensive error handling with custom exception hierarchy
- Add unit and integration tests achieving >90% coverage

## Impact

**Affected specs:**
- `base-client` (new capability)
- `open5e-v1-client` (new capability)
- `open5e-v2-client` (new capability)
- `dnd5e-api-client` (new capability)

**Affected code:**
- `src/lorekeeper_mcp/api_clients/` - New directory with base.py, factory.py, open5e_v1.py, open5e_v2.py, dnd5e_api.py
- `src/lorekeeper_mcp/api_clients/models/` - New directory with Pydantic response models
- `src/lorekeeper_mcp/api_clients/exceptions.py` - New file with custom exceptions
- `src/lorekeeper_mcp/cache/db.py` - Integration with existing async cache (no changes needed)
- `tests/test_api_clients/` - New test directory with comprehensive test coverage
