## 1. Preparation and Documentation

- [ ] 1.1 Review Open5e v2 API capabilities to verify all D&D 5e API functionality can be replicated
- [ ] 1.2 Identify any missing methods in Open5eV2Client that need to be added (rules, reference data)
- [ ] 1.3 Document the mapping between D&D 5e API endpoints and Open5e v2 equivalents

## 2. Extend Open5e V2 Client

- [ ] 2.1 Add `get_rules()` method to Open5eV2Client (wrapper for existing `get_rules_v2`)
- [ ] 2.2 Add `get_conditions()` alias method for consistency with repository protocols
- [ ] 2.3 Add missing reference data adapter methods if needed (proficiencies, etc.)
- [ ] 2.4 Verify all reference data methods return consistent field names (slug normalization)

## 3. Update Repository Layer

- [ ] 3.1 Update `RuleRepository` to use Open5eV2Client
  - [ ] 3.1.1 Update protocol methods to match Open5e v2 method names
  - [ ] 3.1.2 Update method calls to use v2 endpoints
  - [ ] 3.1.3 Handle any field name differences in responses
- [ ] 3.2 Update `CharacterOptionRepository` to use Open5eV2Client exclusively
  - [ ] 3.2.1 Remove `Dnd5eApiClient` import
  - [ ] 3.2.2 Update protocol methods for Open5e v2
  - [ ] 3.2.3 Remove conditional client type check in `_search_feats`
- [ ] 3.3 Update `EquipmentRepository` to use Open5eV2Client
  - [ ] 3.3.1 Update protocol methods to match Open5e v2 API
  - [ ] 3.3.2 Add `get_items()` method for magic items
- [ ] 3.4 Update `SpellRepository` to remove D&D 5e API client support
  - [ ] 3.4.1 Remove `Dnd5eApiClient` import and branch in `_map_to_api_params`
  - [ ] 3.4.2 Simplify to Open5e v2 only

## 4. Update Factory Layer

- [ ] 4.1 Update `RepositoryFactory` to use Open5eV2Client for all repositories
  - [ ] 4.1.1 Update `create_equipment_repository()` default client
  - [ ] 4.1.2 Update `create_character_option_repository()` default client
  - [ ] 4.1.3 Update `create_rule_repository()` default client
  - [ ] 4.1.4 Remove `Dnd5eApiClient` import
- [ ] 4.2 Update `ClientFactory` to remove D&D 5e API method
  - [ ] 4.2.1 Remove `create_dnd5e_api()` method
  - [ ] 4.2.2 Remove `Dnd5eApiClient` import

## 5. Update API Client Package

- [ ] 5.1 Remove `dnd5e_api.py` file
- [ ] 5.2 Update `api_clients/__init__.py` to remove `Dnd5eApiClient` export

## 6. Update Tools and Utilities

- [ ] 6.1 Update `list_documents.py` to remove `dnd5e_api` as valid source
- [ ] 6.2 Update `cache/db.py` to remove any `dnd5e_api` source references
- [ ] 6.3 Update any docstrings referencing D&D 5e API

## 7. Update Tests

- [ ] 7.1 Delete `tests/test_api_clients/test_dnd5e_api.py`
- [ ] 7.2 Update `tests/test_api_clients/test_factory.py` to remove D&D 5e API tests
- [ ] 7.3 Update `tests/test_tools/conftest.py` to remove D&D 5e API fixtures
- [ ] 7.4 Update `tests/test_tools/test_integration.py` to remove D&D 5e API tests
- [ ] 7.5 Update `tests/test_tools/test_document_filtering.py` if it references D&D 5e API
- [ ] 7.6 Update `tests/test_repositories/test_spell.py` to remove D&D 5e API tests
- [ ] 7.7 Update `tests/test_cache/test_db.py` to remove D&D 5e API tests
- [ ] 7.8 Update `tests/test_config.py` to remove any D&D 5e API configuration tests

## 8. Update Configuration and Documentation

- [ ] 8.1 Update `config.py` if it has D&D 5e API settings
- [ ] 8.2 Update `README.md` to remove D&D 5e API references
- [ ] 8.3 Update `docs/apis/5e-srd-api.md` - mark as deprecated/removed or delete
- [ ] 8.4 Update `openspec/project.md` to reflect single API strategy

## 9. Archive Specs

- [ ] 9.1 Mark `dnd5e-api-client` spec as REMOVED
- [ ] 9.2 Mark `complete-dnd5e-client` spec as REMOVED

## 10. Validation

- [ ] 10.1 Run `just lint` to check for any import errors
- [ ] 10.2 Run `just type-check` to verify type consistency
- [ ] 10.3 Run `just test` to verify all tests pass
- [ ] 10.4 Run live tests to verify functionality with Open5e API
- [ ] 10.5 Verify MCP tools work correctly with the new single-API architecture
