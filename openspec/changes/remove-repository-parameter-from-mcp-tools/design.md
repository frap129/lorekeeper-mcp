# Design Document: Remove Repository Parameter from MCP Tools

## Problem Statement

The repository pattern implementation added a `repository` parameter to all MCP tool function signatures:

```python
async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    # ... other parameters
    repository: Any = None,  # ← This shouldn't be exposed!
) -> list[dict[str, Any]]:
    ...
```

When FastMCP registers these functions as MCP tools, it exposes ALL parameters in the tool schema. This means external MCP clients (AI assistants) see:

```json
{
  "name": "lookup_spell",
  "parameters": {
    "name": {"type": "string"},
    "level": {"type": "integer"},
    ...
    "repository": {"type": "any"}  // ← External clients see this!
  }
}
```

This violates several design principles:
- **Leaky Abstraction**: Internal implementation details leak into public API
- **Confusing UX**: Users see parameters they can't and shouldn't use
- **Spec Violation**: `mcp-tools` spec doesn't define a `repository` parameter
- **Poor Encapsulation**: Testing concerns pollute production interface

## Solution Design

### Approach: Module-Level Context for Dependency Injection

Use module-level context dictionaries to support test injection without exposing parameters:

```python
# In each tool module (e.g., spell_lookup.py)

# Private context for test injection
_repository_context: dict[str, Any] = {}

def _get_repository() -> SpellRepository:
    """Get repository, respecting test context.

    This internal function checks if a test has injected a mock repository.
    If so, use it. Otherwise, create a real repository via factory.
    """
    if "repository" in _repository_context:
        return _repository_context["repository"]
    return RepositoryFactory.create_spell_repository()

async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    # ... other domain parameters only!
    limit: int = 20,
    # NO repository parameter!
) -> list[dict[str, Any]]:
    """Search and retrieve D&D 5e spells.

    Args:
        name: Spell name filter
        level: Spell level (0-9)
        ...
        limit: Maximum results

    Returns:
        List of spell dictionaries
    """
    # Get repository internally
    repository = _get_repository()

    # Rest of implementation unchanged
    ...
```

### Testing Pattern

Tests inject mock repositories before calling tools:

```python
import pytest
from unittest.mock import AsyncMock
from lorekeeper_mcp.tools import spell_lookup

@pytest.fixture
def mock_spell_repo():
    """Create mock spell repository."""
    repo = AsyncMock()
    repo.search = AsyncMock(return_value=[
        # Test data...
    ])
    return repo

@pytest.fixture(autouse=True)
def cleanup_context():
    """Clear context after each test."""
    yield
    spell_lookup._repository_context.clear()

async def test_lookup_spell_by_name(mock_spell_repo):
    """Test spell lookup with mock repository."""
    # Inject mock via context
    spell_lookup._repository_context["repository"] = mock_spell_repo

    # Call tool normally
    results = await spell_lookup.lookup_spell(name="Fireball")

    # Verify
    assert len(results) > 0
    mock_spell_repo.search.assert_awaited_once()
```

## Implementation Details

### File Changes Required

All 5 tool files need identical refactoring:

1. **`src/lorekeeper_mcp/tools/spell_lookup.py`**:
   - Add `_repository_context: dict[str, Any] = {}`
   - Add `_get_repository() -> SpellRepository`
   - Remove `repository: Any = None` parameter from `lookup_spell()`
   - Change `if repository is None: repository = Factory...` to `repository = _get_repository()`
   - Update docstring to remove repository parameter

2. **`src/lorekeeper_mcp/tools/creature_lookup.py`**:
   - Same pattern for MonsterRepository

3. **`src/lorekeeper_mcp/tools/equipment_lookup.py`**:
   - Same pattern for EquipmentRepository

4. **`src/lorekeeper_mcp/tools/character_option_lookup.py`**:
   - Same pattern for CharacterOptionRepository

5. **`src/lorekeeper_mcp/tools/rule_lookup.py`**:
   - Same pattern for RuleRepository

### Test Changes Required

All tool test files need updates:

1. **Add cleanup fixture** (can be in `conftest.py`):
```python
@pytest.fixture(autouse=True)
def cleanup_tool_contexts():
    """Clear all tool repository contexts after each test."""
    yield
    from lorekeeper_mcp.tools import (
        spell_lookup, creature_lookup, equipment_lookup,
        character_option_lookup, rule_lookup
    )
    spell_lookup._repository_context.clear()
    creature_lookup._repository_context.clear()
    equipment_lookup._repository_context.clear()
    character_option_lookup._repository_context.clear()
    rule_lookup._repository_context.clear()
```

2. **Update test injection pattern**:
```python
# OLD (passing as parameter)
results = await lookup_spell(name="Fireball", repository=mock_repo)

# NEW (injecting via context)
spell_lookup._repository_context["repository"] = mock_repo
results = await lookup_spell(name="Fireball")
```

3. **Files to update**:
   - `tests/test_tools/test_spell_lookup.py` (8 tests)
   - `tests/test_tools/test_creature_lookup.py` (10 tests)
   - `tests/test_tools/test_equipment_lookup.py` (10 tests)
   - `tests/test_tools/test_character_option_lookup.py` (14 tests)
   - `tests/test_tools/test_rule_lookup.py` (12 tests)
   - `tests/test_tools/conftest.py` (add cleanup fixture)

Total: ~54 test updates + 1 new fixture

### Spec Changes Required

Update `implement-repository-pattern` specs to remove repository parameter requirements:

1. **`openspec/changes/implement-repository-pattern/specs/tool-repository-migration/spec.md`**:
   - **REMOVE** all acceptance criteria mentioning "Add optional `repository` parameter"
   - **UPDATE** scenarios to describe internal repository usage without parameter
   - **ADD** requirement about using module-level context for testing

Example diff:
```diff
#### Scenario: Lookup spells via repository
When the tool is called, it should use the repository for data access.

**Acceptance Criteria:**
- Remove direct `Open5eV2Client()` instantiation from `lookup_spell()`
-- Add optional `repository: SpellRepository | None` parameter for dependency injection
-- Use `RepositoryFactory.create_spell_repository()` when repository not provided
+- Use internal `_get_repository()` function to obtain repository
+- Repository obtained respects module-level test context
+- Tool function signature contains NO repository parameter
- Replace `client.get_spells()` with `repository.get_all()` or `repository.search()`
- Remove in-memory `_spell_cache` (caching now handled by repository)
- Maintain existing function signature and return type for backward compatibility
-- Update tool tests to use repository mocks instead of HTTP mocks
+- Update tool tests to inject mocks via `_repository_context` dictionary
```

Apply similar changes to all 5 tool requirements in the spec.

## Migration Plan

### Phase 1: Update Tool Implementations (Parallel)
Can be done in parallel per tool:
1. Add `_repository_context` and `_get_repository()` to tool module
2. Remove `repository` parameter from function signature
3. Update docstring
4. Change repository acquisition to use `_get_repository()`

### Phase 2: Update Tool Tests (Parallel)
Can be done in parallel per tool:
1. Add context cleanup fixture to `conftest.py`
2. Update each test to inject via `_repository_context`
3. Remove `repository=...` parameter from all test calls
4. Verify tests still pass

### Phase 3: Update Specs
1. Update `tool-repository-migration/spec.md`
2. Update related documentation in proposal and tasks

### Phase 4: Validation
1. Run all tool tests: `uv run pytest tests/test_tools/ -v`
2. Run integration tests: `uv run pytest tests/test_tools/test_integration.py -v`
3. Run full test suite: `uv run pytest -v`
4. Validate MCP tool schema doesn't expose `repository` field
5. Manual MCP server testing

## Validation Strategy

### Automated Validation

1. **Test Suite**: All 54 tool unit tests must pass
2. **Type Checking**: `uv run mypy src/` must pass (no `Any` parameter)
3. **Integration Tests**: End-to-end tests must work with new pattern
4. **Code Quality**: `uv run ruff check src/ tests/` must pass

### Manual Validation

1. **MCP Schema Inspection**:
   Start server and inspect tool schemas:
   ```bash
   uv run python -m lorekeeper_mcp
   # Use MCP client to inspect tool schemas
   # Verify "repository" field is absent from all 5 tools
   ```

2. **Functional Testing**:
   Test each tool via MCP client:
   - `lookup_spell(name="Fireball")`
   - `lookup_creature(name="Dragon")`
   - `lookup_equipment(type="weapon")`
   - `lookup_character_option(type="class")`
   - `lookup_rule(type="condition")`

## Benefits

1. **Clean MCP Interface**: External clients see only domain parameters
2. **Spec Compliance**: Tools match `mcp-tools` specification
3. **Better Encapsulation**: Implementation details stay internal
4. **Maintained Testability**: Tests can still inject mocks easily
5. **Improved Documentation**: Docstrings focus on actual usage
6. **Type Safety**: Remove `Any` type parameter

## Risks & Mitigation

### Risk: Breaking Existing Tests
**Likelihood**: High (54 tests need updates)
**Impact**: Medium (tests fail but functionality unchanged)
**Mitigation**:
- Update tests systematically per tool
- Run test suite after each tool migration
- Use Git branches for safe rollback

### Risk: Accidental Production Use of Test Context
**Likelihood**: Low (context is module-private, empty by default)
**Impact**: Low (would just use wrong repository)
**Mitigation**:
- Name clearly with `_` prefix (private)
- Document as test-only
- Add `assert not _repository_context or os.getenv("TESTING")` in production?

### Risk: Test Isolation Issues
**Likelihood**: Medium (if cleanup forgotten)
**Impact**: Medium (test pollution)
**Mitigation**:
- Use `autouse=True` fixture for cleanup
- Document pattern in test guide
- Code review checks

## Alternative Considered: Global Override Function

Instead of module-level dictionary, use a function:

```python
_repository_override: SpellRepository | None = None

def set_repository_for_testing(repo: SpellRepository | None) -> None:
    """Set repository override for testing. DO NOT USE IN PRODUCTION."""
    global _repository_override
    _repository_override = repo

def _get_repository() -> SpellRepository:
    if _repository_override is not None:
        return _repository_override
    return RepositoryFactory.create_spell_repository()
```

**Pros**: More explicit, slightly cleaner
**Cons**: More boilerplate, still global state

**Decision**: Use dictionary approach for simplicity and consistency

## Success Metrics

- [ ] All 5 tools have `repository` parameter removed
- [ ] All 54 tool unit tests pass with new injection pattern
- [ ] MCP tool schemas validated (no `repository` field)
- [ ] Type checking passes (`mypy src/`)
- [ ] No `Any` types in tool signatures
- [ ] Integration tests pass
- [ ] Manual MCP testing confirms clean interface
