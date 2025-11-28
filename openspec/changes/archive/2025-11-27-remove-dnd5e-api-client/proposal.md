## Why

The D&D 5e API (dnd5eapi.co) exclusively serves SRD content, which is already available through Open5e API as the "System Reference Document 5.1" document. Maintaining a separate API client for identical data creates unnecessary code complexity, duplicate tests, and potential inconsistencies. Open5e API provides a superset of this content with additional third-party sources.

## What Changes

- **BREAKING**: Remove `Dnd5eApiClient` class and all related factory methods
- **BREAKING**: Remove D&D 5e API specs (`dnd5e-api-client`, `complete-dnd5e-client`)
- Migrate `RuleRepository` to use Open5e v2 API for rules, conditions, and reference data
- Migrate `CharacterOptionRepository` to use Open5e v2 API exclusively
- Migrate `EquipmentRepository` to use Open5e v2 API exclusively
- Update `RepositoryFactory` to use Open5e v2 clients by default
- Update `ClientFactory` to remove D&D 5e API factory method
- Remove `dnd5e_api` as a valid source filter in `list_documents` tool
- Remove associated test files for D&D 5e API client

## Impact

- Affected specs:
  - `dnd5e-api-client` (REMOVED)
  - `complete-dnd5e-client` (REMOVED)
  - `repository-infrastructure` (MODIFIED - update factory defaults)
  - `open5e-v2-client` (MODIFIED - add missing reference data methods if needed)
- Affected code:
  - `src/lorekeeper_mcp/api_clients/dnd5e_api.py` (DELETE)
  - `src/lorekeeper_mcp/api_clients/__init__.py` (MODIFY)
  - `src/lorekeeper_mcp/api_clients/factory.py` (MODIFY)
  - `src/lorekeeper_mcp/repositories/factory.py` (MODIFY)
  - `src/lorekeeper_mcp/repositories/rule.py` (MODIFY)
  - `src/lorekeeper_mcp/repositories/character_option.py` (MODIFY)
  - `src/lorekeeper_mcp/repositories/equipment.py` (MODIFY)
  - `src/lorekeeper_mcp/repositories/spell.py` (MODIFY)
  - `src/lorekeeper_mcp/tools/list_documents.py` (MODIFY)
  - `src/lorekeeper_mcp/cache/db.py` (MODIFY - remove dnd5e_api source references)
  - `tests/test_api_clients/test_dnd5e_api.py` (DELETE)
  - Various test files referencing Dnd5eApiClient (MODIFY)
