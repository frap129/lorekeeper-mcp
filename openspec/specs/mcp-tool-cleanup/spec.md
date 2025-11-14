# mcp-tool-cleanup Specification

## Purpose
TBD - created by archiving change remove-repository-parameter-from-mcp-tools. Update Purpose after archive.
## Requirements
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
