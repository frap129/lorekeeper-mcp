# Implementation Tasks: Repository Pattern

This task list outlines the concrete work items needed to implement the repository pattern change. Tasks are organized by phase and include validation criteria.

## Phase 1: Complete API Client Coverage
**Goal**: Implement all missing API endpoints before introducing repository pattern.

### Open5e v1 Client Completion (Can parallelize with other API clients)
- [x] **Task 1.1**: Implement `get_magic_items()` method
  - Add method to `Open5eV1Client`
  - Support name, type, rarity, requires_attunement filtering
  - Use entity cache with 7-day TTL
  - Add unit tests with mock HTTP responses
  - **Validation**: `uv run pytest tests/test_api_clients/test_open5e_v1.py::test_get_magic_items -v`

- [x] **Task 1.2**: Implement `get_planes()` method
   - Add method to `Open5eV1Client`
   - Support name filtering
   - Use entity cache with 7-day TTL
   - Add unit tests
   - **Validation**: `uv run pytest tests/test_api_clients/test_open5e_v1.py::test_get_planes -v`

- [ ] **Task 1.3**: Implement `get_sections()` method
  - Add method to `Open5eV1Client`
  - Support name and parent filtering
  - Handle hierarchical sections
  - Use entity cache with 7-day TTL
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_open5e_v1.py::test_get_sections -v`

- [ ] **Task 1.4**: Implement `get_spell_list()` method
  - Add method to `Open5eV1Client`
  - Support class filtering
  - Use entity cache with 30-day TTL (reference data)
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_open5e_v1.py::test_get_spell_list -v`

- [ ] **Task 1.5**: Implement `get_manifest()` method
  - Add method to `Open5eV1Client`
  - Use extended cache TTL (30 days)
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_open5e_v1.py::test_get_manifest -v`

### Open5e v2 Client Completion (Can parallelize)
- [ ] **Task 1.6**: Implement item-related methods (`get_items()`, `get_item_sets()`, `get_item_categories()`)
  - Add three methods to `Open5eV2Client`
  - Proper TTL configuration (7 days for items, 30 days for categories)
  - Add unit tests for all three methods
  - **Validation**: `uv run pytest tests/test_api_clients/test_open5e_v2.py::test_items -v`

- [ ] **Task 1.7**: Implement creature methods (`get_creatures()`, `get_creature_types()`, `get_creature_sets()`)
  - Add three methods to `Open5eV2Client`
  - Return Monster models compatible with v1
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_open5e_v2.py::test_creatures -v`

- [ ] **Task 1.8**: Implement reference data methods (10 methods total)
  - `get_damage_types_v2()`, `get_languages_v2()`, `get_alignments_v2()`, `get_spell_schools_v2()`
  - `get_sizes()`, `get_item_rarities()`, `get_environments()`, `get_abilities()`, `get_skills_v2()`
  - All use 30-day TTL
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_open5e_v2.py::test_reference_data -v`

- [ ] **Task 1.9**: Implement character option methods (`get_species()`, `get_classes_v2()`)
  - Add two methods to `Open5eV2Client`
  - 7-day TTL for both
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_open5e_v2.py::test_character_options -v`

- [ ] **Task 1.10**: Implement rules and metadata methods (7 methods)
  - `get_rules_v2()`, `get_rulesets()`, `get_documents()`, `get_licenses()`, `get_publishers()`, `get_game_systems()`
  - Proper TTL configuration (7 days for rules, 30 days for metadata)
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_open5e_v2.py::test_rules_metadata -v`

- [ ] **Task 1.11**: Implement additional content methods (`get_images()`, `get_weapon_properties_v2()`, `get_services()`)
  - Add three methods to `Open5eV2Client`
  - Proper TTL configuration
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_open5e_v2.py::test_additional_content -v`

### D&D 5e API Client Completion (Can parallelize)
- [ ] **Task 1.12**: Implement character option methods (7 methods)
  - `get_backgrounds_dnd5e()`, `get_classes_dnd5e()`, `get_subclasses()`, `get_races_dnd5e()`, `get_subraces()`, `get_feats_dnd5e()`, `get_traits()`
  - All use 7-day TTL
  - Handle index-to-slug normalization
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_dnd5e_api.py::test_character_options -v`

- [ ] **Task 1.13**: Implement equipment methods (3 methods)
  - `get_equipment()`, `get_equipment_categories()`, `get_magic_items_dnd5e()`
  - Proper TTL configuration (30 days for categories)
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_dnd5e_api.py::test_equipment -v`

- [ ] **Task 1.14**: Implement spell and monster methods
  - `get_spells_dnd5e()`, `get_monsters_dnd5e()`
  - Return appropriate model types (Monster model)
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_dnd5e_api.py::test_spells_monsters -v`

- [ ] **Task 1.15**: Implement conditions and features methods
  - `get_conditions_dnd5e()`, `get_features()`
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_api_clients/test_dnd5e_api.py::test_conditions_features -v`

### Phase 1 Validation
- [ ] **Task 1.16**: Run all API client tests
  - **Validation**: `uv run pytest tests/test_api_clients/ -v`
  - **Validation**: All tests pass (>90% coverage)

## Phase 2: Repository Infrastructure
**Goal**: Create repository layer with cache abstraction.
**Dependencies**: Phase 1 complete

### Cache Abstraction
- [ ] **Task 2.1**: Create cache protocol
  - Create `src/lorekeeper_mcp/cache/protocol.py`
  - Define `CacheProtocol` with `get_entities()` and `store_entities()` methods
  - Add type hints and docstrings
  - **Validation**: `uv run mypy src/lorekeeper_mcp/cache/protocol.py`

- [ ] **Task 2.2**: Implement SQLite cache wrapper
  - Create `src/lorekeeper_mcp/cache/sqlite.py`
  - Implement `SQLiteCache` class conforming to `CacheProtocol`
  - Wrap existing `query_cached_entities()` and `bulk_cache_entities()`
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_cache/test_sqlite.py -v`

### Repository Base
- [ ] **Task 2.3**: Create repository base protocol
  - Create `src/lorekeeper_mcp/repositories/__init__.py`
  - Create `src/lorekeeper_mcp/repositories/base.py`
  - Define `Repository[T]` protocol with `get_all()` and `search()` methods
  - Add type hints with generics
  - **Validation**: `uv run mypy src/lorekeeper_mcp/repositories/base.py`

### Concrete Repositories
- [ ] **Task 2.4**: Implement SpellRepository
  - Create `src/lorekeeper_mcp/repositories/spell.py`
  - Implement cache-aside pattern
  - Support all spell filters
  - Add unit tests with mocked client and cache
  - **Validation**: `uv run pytest tests/test_repositories/test_spell.py -v`

- [ ] **Task 2.5**: Implement MonsterRepository
  - Create `src/lorekeeper_mcp/repositories/monster.py`
  - Support multi-source fetching (v1 primary)
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_repositories/test_monster.py -v`

- [ ] **Task 2.6**: Implement EquipmentRepository
  - Create `src/lorekeeper_mcp/repositories/equipment.py`
  - Handle item type routing (weapon/armor/item)
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_repositories/test_equipment.py -v`

- [ ] **Task 2.7**: Implement CharacterOptionRepository
  - Create `src/lorekeeper_mcp/repositories/character_option.py`
  - Handle option type routing
  - Support multi-source fetching
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_repositories/test_character_option.py -v`

- [ ] **Task 2.8**: Implement RuleRepository
  - Create `src/lorekeeper_mcp/repositories/rule.py`
  - Handle rule type routing
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_repositories/test_rule.py -v`

### Repository Factory
- [ ] **Task 2.9**: Implement repository factory
  - Create `src/lorekeeper_mcp/repositories/factory.py`
  - Add factory methods for all 5 repositories
  - Support dependency injection
  - Add unit tests
  - **Validation**: `uv run pytest tests/test_repositories/test_factory.py -v`

### Refactor BaseHttpClient
- [ ] **Task 2.10**: Extract cache logic from BaseHttpClient
  - Remove entity cache parameters from `make_request()`
  - Remove cache-related private methods
  - Update all client subclasses to remove entity cache calls
  - Add migration notes for breaking changes
  - **Validation**: `uv run pytest tests/test_api_clients/ -v`
  - **Validation**: No mypy errors

### Phase 2 Validation
- [ ] **Task 2.11**: Run all repository tests
  - **Validation**: `uv run pytest tests/test_repositories/ -v`
  - **Validation**: All repository tests pass (>90% coverage)

## Phase 3: Migrate Tools to Repositories
**Goal**: Refactor all MCP tools to use repositories.
**Dependencies**: Phase 2 complete

### Tool Migration (Can parallelize per tool)
- [ ] **Task 3.1**: Migrate spell_lookup tool
  - Add optional `repository` parameter to `lookup_spell()`
  - Use `RepositoryFactory.create_spell_repository()` as default
  - Remove direct client instantiation
  - Remove `_spell_cache` in-memory cache
  - Update unit tests to use repository mocks
  - **Validation**: `uv run pytest tests/test_tools/test_spell_lookup.py -v`

- [ ] **Task 3.2**: Migrate creature_lookup tool
  - Add optional `repository` parameter to `lookup_creature()`
  - Use `RepositoryFactory.create_monster_repository()` as default
  - Remove direct client instantiation
  - Remove `_creature_cache` in-memory cache
  - Update unit tests to use repository mocks
  - **Validation**: `uv run pytest tests/test_tools/test_creature_lookup.py -v`

- [ ] **Task 3.3**: Migrate equipment_lookup tool
  - Add optional `repository` parameter to `lookup_equipment()`
  - Use `RepositoryFactory.create_equipment_repository()` as default
  - Remove direct client instantiation
  - Remove in-memory caching
  - Update unit tests to use repository mocks
  - **Validation**: `uv run pytest tests/test_tools/test_equipment_lookup.py -v`

- [ ] **Task 3.4**: Migrate character_option_lookup tool
  - Add optional `repository` parameter to `lookup_character_option()`
  - Use `RepositoryFactory.create_character_option_repository()` as default
  - Remove direct client instantiation
  - Remove in-memory caching
  - Update unit tests to use repository mocks
  - **Validation**: `uv run pytest tests/test_tools/test_character_option_lookup.py -v`

- [ ] **Task 3.5**: Migrate rule_lookup tool
  - Add optional `repository` parameter to `lookup_rule()`
  - Use `RepositoryFactory.create_rule_repository()` as default
  - Remove direct client instantiation
  - Remove in-memory caching
  - Update unit tests to use repository mocks
  - **Validation**: `uv run pytest tests/test_tools/test_rule_lookup.py -v`

### Integration Testing
- [ ] **Task 3.6**: Add integration tests for tools
  - Create/update `tests/test_tools/test_integration.py`
  - Test tools with real repositories and test database
  - Test cache-aside pattern end-to-end
  - Test offline mode (cache fallback)
  - Mark as `@pytest.mark.integration`
  - **Validation**: `uv run pytest tests/test_tools/test_integration.py -v -m integration`

### Documentation
- [ ] **Task 3.7**: Update tool docstrings
  - Update module docstrings to mention repository pattern
  - Document optional `repository` parameters
  - Add code examples
  - **Validation**: Manual review of docstrings

### Phase 3 Validation
- [ ] **Task 3.8**: Run all tool tests
  - **Validation**: `uv run pytest tests/test_tools/ -v`
  - **Validation**: All tool tests pass

## Phase 4: Final Validation and Cleanup
**Goal**: Ensure everything works together and clean up.
**Dependencies**: Phase 3 complete

- [ ] **Task 4.1**: Run full test suite
  - **Validation**: `uv run pytest -v`
  - **Validation**: All tests pass (>90% total coverage)

- [ ] **Task 4.2**: Run code quality checks
  - **Validation**: `uv run ruff check src/ tests/`
  - **Validation**: `uv run ruff format src/ tests/ --check`
  - **Validation**: `uv run mypy src/`
  - **Validation**: No errors

- [ ] **Task 4.3**: Run pre-commit hooks
  - **Validation**: `uv run pre-commit run --all-files`
  - **Validation**: All hooks pass

- [ ] **Task 4.4**: Test MCP server end-to-end
  - Start server: `uv run python -m lorekeeper_mcp`
  - Test all 5 tools via MCP client
  - Verify caching works
  - Verify performance is acceptable
  - **Validation**: Manual testing or live MCP tests

- [ ] **Task 4.5**: Update project documentation
  - Update README.md if needed
  - Update docs/architecture.md with repository pattern diagram
  - Add repository usage examples
  - **Validation**: Manual review

- [ ] **Task 4.6**: Create migration notes
  - Document breaking changes (BaseHttpClient API)
  - Document new repository pattern
  - Provide migration guide for external users (if any)
  - **Validation**: Manual review

## Summary
- **Total Tasks**: 46 tasks across 4 phases
- **Estimated Effort**: Large (2-3 weeks for one developer)
- **Parallelization**: Phases 1 and 3 have significant parallelization opportunities
- **Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4
- **Key Validation**: All tests pass, code quality checks pass, MCP server works end-to-end
