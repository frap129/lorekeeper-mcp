# Remove Repository Parameter from MCP Tools Implementation Plan

**Goal:** Remove the erroneous `repository` parameter from all 5 MCP tool function signatures and implement module-level context injection for testing, resulting in clean MCP tool interfaces that don't expose internal implementation details to external clients.

**Architecture:** Use module-level `_repository_context` dictionaries with private `_get_repository()` functions to handle dependency injection for testing while keeping tool signatures clean for external MCP clients.

**Tech Stack:** Python 3.13+, FastMCP, pytest, mypy, ruff

---

## Phase 1: Update Tool Implementations

### Task 1: Update spell_lookup.py

**Files:**
- Modify: `src/lorekeeper_mcp/tools/spell_lookup.py`
- Test: `tests/test_tools/test_spell_lookup.py`

**Step 1: Write the failing test**

```python
def test_spell_lookup_signature_clean():
    """Test that lookup_spell has no repository parameter."""
    import inspect
    sig = inspect.signature(spell_lookup.lookup_spell)
    params = list(sig.parameters.keys())
    assert "repository" not in params, f"Found repository parameter in {params}"
    assert "name" in params
    assert "level" in params
    assert "limit" in params
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_spell_lookup_signature_clean -v`
Expected: FAIL with "repository parameter found"

**Step 3: Implement the changes**

```python
# Add at module level
_repository_context: dict[str, Any] = {}

def _get_repository() -> SpellRepository:
    """Get spell repository, respecting test context."""
    if "repository" in _repository_context:
        return _repository_context["repository"]
    return RepositoryFactory.create_spell_repository()

async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    school: str | None = None,
    concentration: bool | None = None,
    ritual: bool | None = None,
    limit: int = 20,
    # NO repository parameter!
) -> list[dict[str, Any]]:
    """Search and retrieve D&D 5e spells.

    Args:
        name: Spell name filter
        level: Spell level (0-9)
        school: Magic school filter
        concentration: Concentration requirement filter
        ritual: Ritual casting filter
        limit: Maximum results to return

    Returns:
        List of spell dictionaries matching the criteria
    """
    repository = _get_repository()
    # ... rest of implementation unchanged
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_spell_lookup_signature_clean -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/tools/spell_lookup.py tests/test_tools/test_spell_lookup.py
git commit -m "feat: remove repository parameter from lookup_spell"
```

### Task 2: Update creature_lookup.py

**Files:**
- Modify: `src/lorekeeper_mcp/tools/creature_lookup.py`
- Test: `tests/test_tools/test_creature_lookup.py`

**Step 1: Write the failing test**

```python
def test_creature_lookup_signature_clean():
    """Test that lookup_creature has no repository parameter."""
    import inspect
    sig = inspect.signature(creature_lookup.lookup_creature)
    params = list(sig.parameters.keys())
    assert "repository" not in params, f"Found repository parameter in {params}"
    assert "name" in params
    assert "challenge_rating" in params
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_creature_lookup.py::test_creature_lookup_signature_clean -v`
Expected: FAIL

**Step 3: Implement the changes**

```python
# Add at module level
_repository_context: dict[str, Any] = {}

def _get_repository() -> MonsterRepository:
    """Get monster repository, respecting test context."""
    if "repository" in _repository_context:
        return _repository_context["repository"]
    return RepositoryFactory.create_monster_repository()

async def lookup_creature(
    name: str | None = None,
    challenge_rating: float | None = None,
    size: str | None = None,
    type: str | None = None,
    alignment: str | None = None,
    limit: int = 20,
    # NO repository parameter!
) -> list[dict[str, Any]]:
    """Search and retrieve D&D 5e creatures.

    Args:
        name: Creature name filter
        challenge_rating: CR filter (e.g., 0.25, 2.0)
        size: Creature size filter
        type: Creature type filter
        alignment: Alignment filter
        limit: Maximum results to return

    Returns:
        List of creature dictionaries
    """
    repository = _get_repository()
    # ... rest of implementation unchanged
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_creature_lookup.py::test_creature_lookup_signature_clean -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/tools/creature_lookup.py tests/test_tools/test_creature_lookup.py
git commit -m "feat: remove repository parameter from lookup_creature"
```

### Task 3: Update equipment_lookup.py

**Files:**
- Modify: `src/lorekeeper_mcp/tools/equipment_lookup.py`
- Test: `tests/test_tools/test_equipment_lookup.py`

**Step 1: Write the failing test**

```python
def test_equipment_lookup_signature_clean():
    """Test that lookup_equipment has no repository parameter."""
    import inspect
    sig = inspect.signature(equipment_lookup.lookup_equipment)
    params = list(sig.parameters.keys())
    assert "repository" not in params, f"Found repository parameter in {params}"
    assert "name" in params
    assert "type" in params
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_equipment_lookup.py::test_equipment_lookup_signature_clean -v`
Expected: FAIL

**Step 3: Implement the changes**

```python
# Add at module level
_repository_context: dict[str, Any] = {}

def _get_repository() -> EquipmentRepository:
    """Get equipment repository, respecting test context."""
    if "repository" in _repository_context:
        return _repository_context["repository"]
    return RepositoryFactory.create_equipment_repository()

async def lookup_equipment(
    name: str | None = None,
    type: str | None = None,
    rarity: str | None = None,
    requires_attunement: bool | None = None,
    limit: int = 20,
    # NO repository parameter!
) -> list[dict[str, Any]]:
    """Search and retrieve D&D 5e equipment.

    Args:
        name: Equipment name filter
        type: Equipment type filter
        rarity: Equipment rarity filter
        requires_attunement: Attunement requirement filter
        limit: Maximum results to return

    Returns:
        List of equipment dictionaries
    """
    repository = _get_repository()
    # ... rest of implementation unchanged
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_equipment_lookup.py::test_equipment_lookup_signature_clean -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/tools/equipment_lookup.py tests/test_tools/test_equipment_lookup.py
git commit -m "feat: remove repository parameter from lookup_equipment"
```

### Task 4: Update character_option_lookup.py

**Files:**
- Modify: `src/lorekeeper_mcp/tools/character_option_lookup.py`
- Test: `tests/test_tools/test_character_option_lookup.py`

**Step 1: Write the failing test**

```python
def test_character_option_lookup_signature_clean():
    """Test that lookup_character_option has no repository parameter."""
    import inspect
    sig = inspect.signature(character_option_lookup.lookup_character_option)
    params = list(sig.parameters.keys())
    assert "repository" not in params, f"Found repository parameter in {params}"
    assert "type" in params
    assert "name" in params
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_character_option_lookup.py::test_character_option_lookup_signature_clean -v`
Expected: FAIL

**Step 3: Implement the changes**

```python
# Add at module level
_repository_context: dict[str, Any] = {}

def _get_repository() -> CharacterOptionRepository:
    """Get character option repository, respecting test context."""
    if "repository" in _repository_context:
        return _repository_context["repository"]
    return RepositoryFactory.create_character_option_repository()

async def lookup_character_option(
    type: str | None = None,
    name: str | None = None,
    class_restriction: str | None = None,
    race_restriction: str | None = None,
    limit: int = 20,
    # NO repository parameter!
) -> list[dict[str, Any]]:
    """Search and retrieve D&D 5e character options.

    Args:
        type: Option type filter (class, race, background, feat)
        name: Option name filter
        class_restriction: Class requirement filter
        race_restriction: Race requirement filter
        limit: Maximum results to return

    Returns:
        List of character option dictionaries
    """
    repository = _get_repository()
    # ... rest of implementation unchanged
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_character_option_lookup.py::test_character_option_lookup_signature_clean -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/tools/character_option_lookup.py tests/test_tools/test_character_option_lookup.py
git commit -m "feat: remove repository parameter from lookup_character_option"
```

### Task 5: Update rule_lookup.py

**Files:**
- Modify: `src/lorekeeper_mcp/tools/rule_lookup.py`
- Test: `tests/test_tools/test_rule_lookup.py`

**Step 1: Write the failing test**

```python
def test_rule_lookup_signature_clean():
    """Test that lookup_rule has no repository parameter."""
    import inspect
    sig = inspect.signature(rule_lookup.lookup_rule)
    params = list(sig.parameters.keys())
    assert "repository" not in params, f"Found repository parameter in {params}"
    assert "type" in params
    assert "name" in params
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_rule_lookup.py::test_rule_lookup_signature_clean -v`
Expected: FAIL

**Step 3: Implement the changes**

```python
# Add at module level
_repository_context: dict[str, Any] = {}

def _get_repository() -> RuleRepository:
    """Get rule repository, respecting test context."""
    if "repository" in _repository_context:
        return _repository_context["repository"]
    return RepositoryFactory.create_rule_repository()

async def lookup_rule(
    type: str | None = None,
    name: str | None = None,
    source: str | None = None,
    limit: int = 20,
    # NO repository parameter!
) -> list[dict[str, Any]]:
    """Search and retrieve D&D 5e rules.

    Args:
        type: Rule type filter (condition, spell, magic_item)
        name: Rule name filter
        source: Source book filter
        limit: Maximum results to return

    Returns:
        List of rule dictionaries
    """
    repository = _get_repository()
    # ... rest of implementation unchanged
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_rule_lookup.py::test_rule_lookup_signature_clean -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/tools/rule_lookup.py tests/test_tools/test_rule_lookup.py
git commit -m "feat: remove repository parameter from lookup_rule"
```

### Task 6: Validate all tool signatures

**Files:**
- Test: All tool test files
- Validate: `uv run mypy src/lorekeeper_mcp/tools/`

**Step 1: Run type checking**

Run: `uv run mypy src/lorekeeper_mcp/tools/`
Expected: No errors, no warnings about `Any` parameters

**Step 2: Verify all signature tests pass**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_spell_lookup_signature_clean tests/test_tools/test_creature_lookup.py::test_creature_lookup_signature_clean tests/test_tools/test_equipment_lookup.py::test_equipment_lookup_signature_clean tests/test_tools/test_character_option_lookup.py::test_character_option_lookup_signature_clean tests/test_tools/test_rule_lookup.py::test_rule_lookup_signature_clean -v`
Expected: PASS

**Step 3: Commit**

```bash
git commit -m "feat: validate all tool signatures are clean"
```

## Phase 2: Update Tool Tests

### Task 7: Add context cleanup fixture

**Files:**
- Modify: `tests/test_tools/conftest.py`
- Test: `tests/test_tools/`

**Step 1: Write the failing test**

```python
def test_cleanup_fixture_exists():
    """Test that cleanup fixture is available."""
    import tests.test_tools.conftest as conftest
    assert hasattr(conftest, 'cleanup_tool_contexts')
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/conftest.py::test_cleanup_fixture_exists -v`
Expected: FAIL

**Step 3: Implement the fixture**

```python
import pytest
from typing import Any

@pytest.fixture(autouse=True)
def cleanup_tool_contexts() -> None:
    """Clear all tool repository contexts after each test."""
    yield
    from lorekeeper_mcp.tools import (
        spell_lookup,
        creature_lookup,
        equipment_lookup,
        character_option_lookup,
        rule_lookup,
    )

    spell_lookup._repository_context.clear()
    creature_lookup._repository_context.clear()
    equipment_lookup._repository_context.clear()
    character_option_lookup._repository_context.clear()
    rule_lookup._repository_context.clear()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/conftest.py::test_cleanup_fixture_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_tools/conftest.py
git commit -m "feat: add cleanup fixture for tool repository contexts"
```

### Task 8: Update spell lookup tests

**Files:**
- Modify: `tests/test_tools/test_spell_lookup.py`
- Test: `tests/test_tools/test_spell_lookup.py`

**Step 1: Write failing test for context injection**

```python
@pytest.mark.asyncio
async def test_spell_lookup_with_context_injection():
    """Test that spell lookup works with context injection."""
    from unittest.mock import AsyncMock
    from lorekeeper_mcp.tools import spell_lookup

    mock_repo = AsyncMock()
    mock_repo.search = AsyncMock(return_value=[{"name": "Fireball"}])

    # Inject via context
    spell_lookup._repository_context["repository"] = mock_repo

    results = await spell_lookup.lookup_spell(name="Fireball")
    assert len(results) == 1
    assert results[0]["name"] == "Fireball"
    mock_repo.search.assert_awaited_once()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_spell_lookup_with_context_injection -v`
Expected: FAIL (no context injection yet)

**Step 3: Update test file**

Replace all instances of:
```python
results = await lookup_spell(name="Fireball", repository=mock_repo)
```

With:
```python
spell_lookup._repository_context["repository"] = mock_repo
results = await lookup_spell(name="Fireball")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_spell_lookup_with_context_injection -v`
Expected: PASS

**Step 5: Run all spell lookup tests**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add tests/test_tools/test_spell_lookup.py
git commit -m "feat: update spell lookup tests to use context injection"
```

### Task 9: Update creature lookup tests

**Files:**
- Modify: `tests/test_tools/test_creature_lookup.py`
- Test: `tests/test_tools/test_creature_lookup.py`

**Step 1: Update test file with context injection**

Replace all instances of:
```python
results = await lookup_creature(name="Dragon", repository=mock_repo)
```

With:
```python
creature_lookup._repository_context["repository"] = mock_repo
results = await lookup_creature(name="Dragon")
```

**Step 2: Run all creature lookup tests**

Run: `uv run pytest tests/test_tools/test_creature_lookup.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_tools/test_creature_lookup.py
git commit -m "feat: update creature lookup tests to use context injection"
```

### Task 10: Update equipment lookup tests

**Files:**
- Modify: `tests/test_tools/test_equipment_lookup.py`
- Test: `tests/test_tools/test_equipment_lookup.py`

**Step 1: Update test file with context injection**

Replace all instances of:
```python
results = await lookup_equipment(type="weapon", repository=mock_repo)
```

With:
```python
equipment_lookup._repository_context["repository"] = mock_repo
results = await lookup_equipment(type="weapon")
```

**Step 2: Run all equipment lookup tests**

Run: `uv run pytest tests/test_tools/test_equipment_lookup.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_tools/test_equipment_lookup.py
git commit -m "feat: update equipment lookup tests to use context injection"
```

### Task 11: Update character option lookup tests

**Files:**
- Modify: `tests/test_tools/test_character_option_lookup.py`
- Test: `tests/test_tools/test_character_option_lookup.py`

**Step 1: Update test file with context injection**

Replace all instances of:
```python
results = await lookup_character_option(type="class", repository=mock_repo)
```

With:
```python
character_option_lookup._repository_context["repository"] = mock_repo
results = await lookup_character_option(type="class")
```

**Step 2: Run all character option lookup tests**

Run: `uv run pytest tests/test_tools/test_character_option_lookup.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_tools/test_character_option_lookup.py
git commit -m "feat: update character option lookup tests to use context injection"
```

### Task 12: Update rule lookup tests

**Files:**
- Modify: `tests/test_tools/test_rule_lookup.py`
- Test: `tests/test_tools/test_rule_lookup.py`

**Step 1: Update test file with context injection**

Replace all instances of:
```python
results = await lookup_rule(type="condition", repository=mock_repo)
```

With:
```python
rule_lookup._repository_context["repository"] = mock_repo
results = await lookup_rule(type="condition")
```

**Step 2: Run all rule lookup tests**

Run: `uv run pytest tests/test_tools/test_rule_lookup.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_tools/test_rule_lookup.py
git commit -m "feat: update rule lookup tests to use context injection"
```

### Task 13: Validate integration tests

**Files:**
- Test: `tests/test_tools/test_integration.py`
- Test: `tests/test_tools/test_integration.py`

**Step 1: Run integration tests**

Run: `uv run pytest tests/test_tools/test_integration.py -v`
Expected: Integration tests still pass (they don't use repository parameter)

**Step 2: Verify no changes needed**

Check that integration tests work without modifications

**Step 3: Commit**

```bash
git commit -m "feat: validate integration tests work without changes"
```

### Task 14: Run all tool tests

**Files:**
- Test: `tests/test_tools/`

**Step 1: Run all tool tests**

Run: `uv run pytest tests/test_tools/ -v`
Expected: All 54+ tests pass

**Step 2: Verify no test pollution**

Run tests multiple times to ensure no context pollution between runs

**Step 3: Commit**

```bash
git commit -m "feat: validate all tool tests pass with context injection"
```

## Phase 3: Update Specs and Documentation

### Task 15: Update tool-repository-migration spec

**Files:**
- Modify: `openspec/changes/implement-repository-pattern/specs/tool-repository-migration/spec.md`

**Step 1: Remove repository parameter requirements**

Update acceptance criteria to remove:
- "Add optional `repository: SpellRepository | None` parameter for dependency injection"
- Update scenarios to describe internal repository usage

Update to require:
- "Use internal `_get_repository()` function to obtain repository"
- "Repository obtained respects module-level test context"
- "Tool function signature contains NO repository parameter"

**Step 2: Validate spec**

Run: `openspec validate implement-repository-pattern --strict`
Expected: No validation errors

**Step 3: Commit**

```bash
git add openspec/changes/implement-repository-pattern/specs/tool-repository-migration/spec.md
git commit -m "docs: update repository migration spec to remove repository parameter"
```

### Task 16: Update implement-repository-pattern proposal

**Files:**
- Modify: `openspec/changes/implement-repository-pattern/proposal.md`

**Step 1: Update success criteria**

Add note about subsequent fix in this change proposal

**Step 2: Add cross-reference**

Reference this change proposal in the proposal

**Step 3: Commit**

```bash
git add openspec/changes/implement-repository-pattern/proposal.md
git commit -m "docs: update repository pattern proposal to reference cleanup"
```

### Task 17: Update implement-repository-pattern tasks

**Files:**
- Modify: `openspec/changes/implement-repository-pattern/tasks.md`

**Step 1: Mark relevant tasks**

Mark tasks as "Updated by remove-repository-parameter change"

**Step 2: Add cross-reference**

Add cross-reference to this change proposal

**Step 3: Commit**

```bash
git add openspec/changes/implement-repository-pattern/tasks.md
git commit -m "docs: update repository pattern tasks to reference cleanup"
```

### Task 18: Update architecture documentation

**Files:**
- Check: `docs/architecture.md`

**Step 1: Review documentation**

Check if architecture.md mentions repository parameter and update if needed

**Step 2: Commit if changes made**

```bash
git add docs/architecture.md
git commit -m "docs: update architecture documentation if needed"
```

### Task 19: Update testing documentation

**Files:**
- Check: `docs/testing.md`

**Step 1: Review documentation**

Check if testing.md has examples of tool testing and update with context injection pattern

**Step 2: Commit if changes made**

```bash
git add docs/testing.md
git commit -m "docs: update testing documentation with context injection pattern"
```

### Task 20: Validate all specs

**Files:**
- Test: All specs

**Step 1: Run spec validation**

Run: `openspec validate --all --strict`
Expected: No validation errors

**Step 2: Commit**

```bash
git commit -m "docs: validate all specifications"
```

## Phase 4: Final Validation and MCP Testing

### Task 21: Run type checking

**Files:**
- Test: `src/lorekeeper_mcp/`

**Step 1: Run mypy**

Run: `uv run mypy src/`
Expected: No errors, no warnings about `Any` parameters

**Step 2: Run linting and formatting**

Run: `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/ --check`
Expected: No errors, no formatting needed

**Step 3: Run pre-commit hooks**

Run: `uv run pre-commit run --all-files`
Expected: All hooks pass

**Step 4: Commit**

```bash
git commit -m "feat: pass all quality checks"
```

### Task 22: Run full test suite

**Files:**
- Test: All tests

**Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass

**Step 2: Commit**

```bash
git commit -m "feat: pass full test suite"
```

### Task 23: Inspect MCP tool schemas

**Files:**
- Test: MCP server functionality

**Step 1: Start MCP server**

Run: `uv run python -m lorekeeper_mcp`
Expected: Server starts successfully

**Step 2: Inspect tool schemas**

Use MCP client to verify tool schemas contain no `repository` parameter
Expected: All 5 tools have clean schemas with only domain parameters

**Step 3: Commit**

```bash
git commit -m "feat: validate MCP tool schemas are clean"
```

### Task 24: Test MCP tools functionally

**Files:**
- Test: MCP tool functionality

**Step 1: Test each tool via MCP client**

- `lookup_spell(name="Fireball")` - should work
- `lookup_creature(name="Dragon")` - should work
- `lookup_equipment(type="weapon")` - should work
- `lookup_character_option(type="class")` - should work
- `lookup_rule(type="condition")` - should work

Expected: All tools return correct data

**Step 2: Test caching behavior**

Verify caching still works (second call is faster)

**Step 3: Commit**

```bash
git commit -m "feat: validate MCP tools work correctly"
```

---

## Summary

This plan removes the erroneous `repository` parameter from all 5 MCP tool functions and implements a clean, testable architecture using module-level context variables. The implementation follows TDD principles with bite-sized tasks, maintains all existing functionality, and ensures MCP tool schemas are clean and professional.

**Key Benefits:**
- Clean MCP interface for external clients
- Maintained testability through context injection
- Type-safe tool signatures
- No breaking changes for existing functionality
- Professional encapsulation of implementation details

**Success Criteria:**
- All 5 tools have NO `repository` parameter
- All 54+ tests pass with new injection pattern
- Type checking passes
- MCP schemas validated
- Integration tests work unchanged
