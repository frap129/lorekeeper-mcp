# mcp-tool-cleanup Specification

## Purpose
Remove the erroneous `repository` parameter from all MCP tool function signatures. This parameter was mistakenly exposed as part of the public MCP tool interface during the repository pattern implementation, violating encapsulation principles and confusing external clients.

## ADDED Requirements

### Requirement: Spell Lookup Tool Has Clean Interface
The system SHALL remove the `repository` parameter from the `lookup_spell` function signature, making it an internal implementation detail rather than a public API parameter.

#### Scenario: External MCP clients see only domain parameters
When an MCP client inspects the `lookup_spell` tool schema, it should see only domain-relevant parameters.

**Acceptance Criteria:**
- Remove `repository: Any = None` parameter from `lookup_spell()` function signature
- Add `_repository_context: dict[str, Any] = {}` module-level variable for test injection
- Add `_get_repository() -> SpellRepository` private function that checks context and creates repository
- Update `lookup_spell()` implementation to call `_get_repository()` instead of using parameter
- Update function docstring to remove repository parameter documentation
- MCP tool schema does not expose `repository` field to external clients
- Tool functionality unchanged for normal (non-test) usage
- Tests inject repositories via `spell_lookup._repository_context["repository"] = mock_repo`

#### Scenario: Unit tests inject mock repositories
When running unit tests, they should inject mock repositories without using function parameters.

**Acceptance Criteria:**
- Tests can inject mocks via module-level `_repository_context` dictionary
- `_get_repository()` checks context before creating real repository
- Context cleared after each test via cleanup fixture
- No test pollution between test cases
- Tests still have full control over repository behavior

---

### Requirement: Creature Lookup Tool Has Clean Interface
The system SHALL remove the `repository` parameter from the `lookup_creature` function signature.

#### Scenario: External MCP clients see only domain parameters
When an MCP client inspects the `lookup_creature` tool schema, it should see only creature-related parameters.

**Acceptance Criteria:**
- Remove `repository: Any = None` parameter from `lookup_creature()` signature
- Add `_repository_context` and `_get_repository()` to creature_lookup module
- Update implementation to use internal repository acquisition
- Update docstring to remove repository parameter
- MCP tool schema clean
- Tests use context injection pattern

---

### Requirement: Equipment Lookup Tool Has Clean Interface
The system SHALL remove the `repository` parameter from the `lookup_equipment` function signature.

#### Scenario: External MCP clients see only equipment parameters
When an MCP client inspects the `lookup_equipment` tool schema, it should see only equipment-related parameters.

**Acceptance Criteria:**
- Remove `repository: Any = None` parameter from `lookup_equipment()` signature
- Add `_repository_context` and `_get_repository()` to equipment_lookup module
- Update implementation to use internal repository acquisition
- Update docstring to remove repository parameter
- MCP tool schema clean
- Tests use context injection pattern

---

### Requirement: Character Option Lookup Tool Has Clean Interface
The system SHALL remove the `repository` parameter from the `lookup_character_option` function signature.

#### Scenario: External MCP clients see only character option parameters
When an MCP client inspects the `lookup_character_option` tool schema, it should see only character option parameters.

**Acceptance Criteria:**
- Remove `repository: Any = None` parameter from `lookup_character_option()` signature
- Add `_repository_context` and `_get_repository()` to character_option_lookup module
- Update implementation to use internal repository acquisition
- Update docstring to remove repository parameter
- MCP tool schema clean
- Tests use context injection pattern

---

### Requirement: Rule Lookup Tool Has Clean Interface
The system SHALL remove the `repository` parameter from the `lookup_rule` function signature.

#### Scenario: External MCP clients see only rule lookup parameters
When an MCP client inspects the `lookup_rule` tool schema, it should see only rule-related parameters.

**Acceptance Criteria:**
- Remove `repository: Any = None` parameter from `lookup_rule()` signature
- Add `_repository_context` and `_get_repository()` to rule_lookup module
- Update implementation to use internal repository acquisition
- Update docstring to remove repository parameter
- MCP tool schema clean
- Tests use context injection pattern

---

## ADDED Requirements

### Requirement: Test Context Cleanup Fixture
The system SHALL provide an automatic cleanup fixture that clears all tool repository contexts after each test.

#### Scenario: Prevent test pollution
When running multiple tests, repository context from one test should not affect other tests.

**Acceptance Criteria:**
- New `cleanup_tool_contexts` fixture in `tests/test_tools/conftest.py`
- Fixture has `autouse=True` to run automatically
- Fixture clears `_repository_context` for all 5 tools after each test
- Runs in teardown phase (yield pattern)
- Imports all tool modules to access their contexts
- Zero test pollution between test cases

#### Scenario: Automatic context isolation
When a test sets a repository context, it should be automatically cleared after the test.

**Acceptance Criteria:**
- Developer does not need to manually clear context
- Context empty at start of each test
- Failed tests do not leave context dirty
- Works with parallel test execution (pytest-xdist)

---

### Requirement: Type Safety for Tool Signatures
The system SHALL ensure all tool function signatures are properly typed without `Any` parameters.

#### Scenario: Type checking passes
When running mypy on tool modules, there should be no warnings about `Any` type parameters.

**Acceptance Criteria:**
- No `repository: Any = None` parameters in any tool
- `_get_repository()` functions have proper return type annotations
- `_repository_context` properly typed as `dict[str, Any]`
- `uv run mypy src/lorekeeper_mcp/tools/` passes with no errors
- No `Type of parameter "repository" is Any` warnings

---

### Requirement: Backward Compatibility for Tool Callers
The system SHALL ensure existing tool callers (MCP server, integration tests) continue to work without modification.

#### Scenario: MCP server requires no changes
When the server registers tools, it should work identically to before.

**Acceptance Criteria:**
- `src/lorekeeper_mcp/server.py` requires no changes
- Tools still registered with `mcp.tool()` decorator
- Server starts and serves all 5 tools correctly
- Tool invocations work identically for external clients

#### Scenario: Integration tests work without modification
When running integration tests that don't inject repositories, they should work unchanged.

**Acceptance Criteria:**
- `tests/test_tools/test_integration.py` requires no changes (or minimal)
- Integration tests call tools normally without repository parameter
- Tools use real repositories via factory
- Caching behavior unchanged

---

### Requirement: Documentation Accuracy
The system SHALL update all tool docstrings and comments to reflect the internal repository pattern.

#### Scenario: Docstrings don't mention repository parameter
When reading tool function docstrings, developers should see accurate parameters.

**Acceptance Criteria:**
- All tool docstrings updated to remove repository parameter from Args section
- Module-level docstrings mention repository pattern is used internally
- Examples in docstrings show usage without repository parameter
- Comments about repository usage clarify it's internal only

---
