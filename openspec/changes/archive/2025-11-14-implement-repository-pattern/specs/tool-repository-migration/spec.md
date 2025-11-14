# tool-repository-migration Specification

## Purpose
Migrate all MCP tools from direct API client usage to repository pattern, improving testability, separation of concerns, and enabling easy mock-based unit testing.

## ADDED Requirements

### Requirement: Spell Lookup Tool Uses Repository
The system SHALL refactor the `lookup_spell` tool to use SpellRepository instead of directly instantiating Open5eV2Client.

#### Scenario: Lookup spells via repository
When the tool is called, it should use the repository for data access.

**Acceptance Criteria:**
- Remove direct `Open5eV2Client()` instantiation from `lookup_spell()`
- Add optional `repository: SpellRepository | None` parameter for dependency injection
- Use `RepositoryFactory.create_spell_repository()` when repository not provided
- Replace `client.get_spells()` with `repository.get_all()` or `repository.search()`
- Remove in-memory `_spell_cache` (caching now handled by repository)
- Maintain existing function signature and return type for backward compatibility
- Update tool tests to use repository mocks instead of HTTP mocks

### Requirement: Creature Lookup Tool Uses Repository
The system SHALL refactor the `lookup_creature` tool to use MonsterRepository instead of directly instantiating Open5eV1Client.

#### Scenario: Lookup creatures via repository
When the tool is called, it should use the repository for data access.

**Acceptance Criteria:**
- Remove direct `Open5eV1Client()` instantiation from `lookup_creature()`
- Add optional `repository: MonsterRepository | None` parameter
- Use `RepositoryFactory.create_monster_repository()` when repository not provided
- Replace `client.get_monsters()` with `repository.get_all()` or `repository.search()`
- Remove in-memory `_creature_cache` (caching now handled by repository)
- Maintain existing function signature and return type for backward compatibility
- Update tool tests to use repository mocks

### Requirement: Equipment Lookup Tool Uses Repository
The system SHALL refactor the `lookup_equipment` tool to use EquipmentRepository instead of direct client usage.

#### Scenario: Lookup equipment via repository
When the tool is called, it should use the repository for data access.

**Acceptance Criteria:**
- Remove direct client instantiation from `lookup_equipment()`
- Add optional `repository: EquipmentRepository | None` parameter
- Use `RepositoryFactory.create_equipment_repository()` when repository not provided
- Replace client calls with `repository.get_all(item_type=...)` calls
- Remove in-memory caching (handled by repository)
- Maintain existing function signature and return type
- Update tool tests to use repository mocks

### Requirement: Character Option Lookup Tool Uses Repository
The system SHALL refactor the `lookup_character_option` tool to use CharacterOptionRepository.

#### Scenario: Lookup character options via repository
When the tool is called, it should use the repository for data access.

**Acceptance Criteria:**
- Remove direct client instantiation from `lookup_character_option()`
- Add optional `repository: CharacterOptionRepository | None` parameter
- Use `RepositoryFactory.create_character_option_repository()` when repository not provided
- Replace client calls with `repository.get_all(option_type=...)` calls
- Remove in-memory caching (handled by repository)
- Maintain existing function signature and return type
- Update tool tests to use repository mocks

### Requirement: Rule Lookup Tool Uses Repository
The system SHALL refactor the `lookup_rule` tool to use RuleRepository.

#### Scenario: Lookup rules via repository
When the tool is called, it should use the repository for data access.

**Acceptance Criteria:**
- Remove direct client instantiation from `lookup_rule()`
- Add optional `repository: RuleRepository | None` parameter
- Use `RepositoryFactory.create_rule_repository()` when repository not provided
- Replace client calls with `repository.get_all(rule_type=...)` calls
- Remove in-memory caching (handled by repository)
- Maintain existing function signature and return type
- Update tool tests to use repository mocks

## ADDED Requirements

### Requirement: Tool Unit Tests with Repository Mocks
The system SHALL update all tool unit tests to use repository mocks instead of HTTP mocks, improving test speed and clarity.

#### Scenario: Fast unit tests with mocked repositories
When running unit tests for tools, they should mock repositories instead of HTTP clients.

**Acceptance Criteria:**
- Remove `@respx.mock` decorators from unit tests
- Use `unittest.mock.Mock` or `pytest-mock` to create repository mocks
- Mock `get_all()` and `search()` methods with test data
- Tests run without network calls (faster, more reliable)
- Tests focus on tool logic, not HTTP/caching details
- Example pattern: `mock_repo = Mock(spec=SpellRepository); mock_repo.get_all.return_value = [test_spell]; result = await lookup_spell(..., repository=mock_repo)`

### Requirement: Integration Tests with Real Repositories
The system SHALL add integration tests that use real repository implementations with SQLite cache.

#### Scenario: Integration test with real cache
When testing full data flow, use real repositories with test database.

**Acceptance Criteria:**
- New `test_integration.py` test file per tool (may already exist)
- Use temporary SQLite database for integration tests
- Create real repository instances with test clients
- Verify cache-aside pattern works correctly
- Test offline mode (cache fallback when network unavailable)
- Mark as `@pytest.mark.integration` for optional execution

### Requirement: Tool Documentation Updates
The system SHALL update tool docstrings to reflect repository-based implementation.

#### Scenario: Document repository usage in tools
When developers read tool code, they should understand repository pattern is used.

**Acceptance Criteria:**
- Update module docstrings to mention repository pattern
- Document optional `repository` parameter in function docstrings
- Add examples of providing custom repositories
- Update inline comments to reference repositories instead of clients
- Maintain user-facing documentation unchanged (internal refactor)

### Requirement: Backward Compatibility During Migration
The system SHALL ensure backward compatibility by making repository parameters optional with factory defaults.

#### Scenario: Gradual migration without breaking changes
When migrating tools, existing code should continue to work without modifications.

**Acceptance Criteria:**
- All repository parameters default to `None`
- Tools create repositories via factory when not provided
- Existing tool callers require no changes
- Server integration continues to work without modification
- Tests can optionally inject repositories for mocking
- No breaking changes to MCP tool interfaces
