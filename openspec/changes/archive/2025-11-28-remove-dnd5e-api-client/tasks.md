## 1. Preparation and Documentation

- [x] 1.1 Review Open5e v2 API capabilities to verify all D&D 5e API functionality can be replicated
- [x] 1.2 Identify any missing methods in Open5eV2Client that need to be added (rules, reference data)
- [x] 1.3 Document the mapping between D&D 5e API endpoints and Open5e v2 equivalents

## 2. Extend Open5e V2 Client

- [x] 2.1 Add `get_rules()` method to Open5eV2Client (wrapper for existing `get_rules_v2`)
- [x] 2.2 Add `get_conditions()` alias method for consistency with repository protocols
- [x] 2.3 Add missing reference data adapter methods if needed (proficiencies - not available in Open5e v2)
- [x] 2.4 Verify all reference data methods return consistent field names (slug normalization)

## 3. Update Repository Layer

- [x] 3.1 Update `RuleRepository` to use Open5eV2Client
  - [x] 3.1.1 Update protocol methods to match Open5e v2 method names
  - [x] 3.1.2 Update method calls to use v2 endpoints
  - [x] 3.1.3 Handle any field name differences in responses
- [x] 3.2 Update `CharacterOptionRepository` to use Open5eV2Client exclusively
  - [x] 3.2.1 Remove `Dnd5eApiClient` import
  - [x] 3.2.2 Update protocol methods for Open5e v2
  - [x] 3.2.3 Remove conditional client type check in `_search_feats`
- [x] 3.3 Update `EquipmentRepository` to use Open5eV2Client
  - [x] 3.3.1 Update protocol methods to match Open5e v2 API
  - [x] 3.3.2 Add `get_items()` method for magic items
- [x] 3.4 Update `SpellRepository` to remove D&D 5e API client support
  - [x] 3.4.1 Remove `Dnd5eApiClient` import and branch in `_map_to_api_params`
  - [x] 3.4.2 Simplify to Open5e v2 only

## 4. Update Factory Layer

- [x] 4.1 Update `RepositoryFactory` to use Open5eV2Client for all repositories
  - [x] 4.1.1 Update `create_equipment_repository()` default client
  - [x] 4.1.2 Update `create_character_option_repository()` default client
  - [x] 4.1.3 Update `create_rule_repository()` default client
  - [x] 4.1.4 Remove `Dnd5eApiClient` import
- [x] 4.2 Update `ClientFactory` to remove D&D 5e API method
  - [x] 4.2.1 Remove `create_dnd5e_api()` method
  - [x] 4.2.2 Remove `Dnd5eApiClient` import

## 5. Update API Client Package

- [x] 5.1 Remove `dnd5e_api.py` file
- [x] 5.2 Update `api_clients/__init__.py` to remove `Dnd5eApiClient` export

## 6. Update Tools and Utilities

- [x] 6.1 Update `list_documents.py` to remove `dnd5e_api` as valid source
- [x] 6.2 Update `cache/db.py` to remove any `dnd5e_api` source references
- [x] 6.3 Update any docstrings referencing D&D 5e API

## 7. Update Tests

- [x] 7.1 Delete `tests/test_api_clients/test_dnd5e_api.py`
- [x] 7.2 Update `tests/test_api_clients/test_factory.py` to remove D&D 5e API tests
- [x] 7.3 Update `tests/test_tools/conftest.py` to remove D&D 5e API fixtures
- [x] 7.4 Update `tests/test_tools/test_integration.py` to remove D&D 5e API tests
- [x] 7.5 Update `tests/test_tools/test_document_filtering.py` if it references D&D 5e API
- [x] 7.6 Update `tests/test_repositories/test_spell.py` to remove D&D 5e API tests
- [x] 7.7 Update `tests/test_cache/test_db.py` to remove D&D 5e API tests
- [x] 7.8 Update `tests/test_config.py` to remove any D&D 5e API configuration tests

## 8. Update Configuration and Documentation

- [x] 8.1 Update `config.py` if it has D&D 5e API settings
- [x] 8.2 Update `README.md` to remove D&D 5e API references
- [x] 8.3 Update `docs/apis/5e-srd-api.md` - mark as deprecated/removed or delete
- [x] 8.4 Update `openspec/project.md` to reflect single API strategy

## 9. Archive Specs

- [x] 9.1 Mark `dnd5e-api-client` spec as REMOVED
- [x] 9.2 Mark `complete-dnd5e-client` spec as REMOVED

## 10. Validation

- [x] 10.1 Run `just lint` to check for any import errors
- [x] 10.2 Run `just type-check` to verify type consistency
- [x] 10.3 Run `just test` to verify all tests pass (1 pre-existing failure unrelated to this change)
- [x] 10.4 Run live tests to verify functionality with Open5e API (37 passed, 1 skipped)
- [x] 10.5 Verify MCP tools work correctly with the new single-API architecture
