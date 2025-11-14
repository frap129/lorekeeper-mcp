# tool-repository-migration Specification

## Purpose
TBD - created by archiving change implement-repository-pattern. Update Purpose after archive.
## Requirements
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
