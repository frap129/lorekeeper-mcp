# Implementation Tasks: Remove Repository Parameter from MCP Tools

This task list outlines the concrete work items needed to remove the erroneous `repository` parameter from all MCP tool function signatures. Tasks are organized to minimize rework and maintain test coverage throughout.

## Phase 1: Update Tool Implementations

### Tool File Updates (Can parallelize per tool)
- [ ] **Task 1.1**: Update spell_lookup.py
  - Add `_repository_context: dict[str, Any] = {}` module variable
  - Add `_get_repository() -> SpellRepository` private function
  - Remove `repository: Any = None` parameter from `lookup_spell()` signature
  - Change `if repository is None: repository = Factory...` to `repository = _get_repository()`
  - Update function docstring to remove repository parameter documentation
  - **Validation**: `uv run mypy src/lorekeeper_mcp/tools/spell_lookup.py` (no `Any` parameter warnings)

- [ ] **Task 1.2**: Update creature_lookup.py
  - Add `_repository_context: dict[str, Any] = {}` module variable
  - Add `_get_repository() -> MonsterRepository` private function
  - Remove `repository: Any = None` parameter from `lookup_creature()` signature
  - Change repository acquisition logic to use `_get_repository()`
  - Update function docstring
  - **Validation**: `uv run mypy src/lorekeeper_mcp/tools/creature_lookup.py`

- [ ] **Task 1.3**: Update equipment_lookup.py
  - Add `_repository_context: dict[str, Any] = {}` module variable
  - Add `_get_repository() -> EquipmentRepository` private function
  - Remove `repository: Any = None` parameter from `lookup_equipment()` signature
  - Change repository acquisition logic to use `_get_repository()`
  - Update function docstring
  - **Validation**: `uv run mypy src/lorekeeper_mcp/tools/equipment_lookup.py`

- [ ] **Task 1.4**: Update character_option_lookup.py
  - Add `_repository_context: dict[str, Any] = {}` module variable
  - Add `_get_repository() -> CharacterOptionRepository` private function
  - Remove `repository: Any = None` parameter from `lookup_character_option()` signature
  - Change repository acquisition logic to use `_get_repository()`
  - Update function docstring
  - **Validation**: `uv run mypy src/lorekeeper_mcp/tools/character_option_lookup.py`

- [ ] **Task 1.5**: Update rule_lookup.py
  - Add `_repository_context: dict[str, Any] = {}` module variable
  - Add `_get_repository() -> RuleRepository` private function
  - Remove `repository: Any = None` parameter from `lookup_rule()` signature
  - Change repository acquisition logic to use `_get_repository()`
  - Update function docstring
  - **Validation**: `uv run mypy src/lorekeeper_mcp/tools/rule_lookup.py`

### Phase 1 Validation
- [ ] **Task 1.6**: Verify tool type signatures
  - **Validation**: `uv run mypy src/lorekeeper_mcp/tools/` (all type checks pass)
  - **Validation**: No `repository` parameter in any tool function signature
  - **Validation**: All `_get_repository()` functions properly typed

## Phase 2: Update Tool Tests

### Test Infrastructure
- [ ] **Task 2.1**: Add context cleanup fixture
  - Update `tests/test_tools/conftest.py`
  - Add `cleanup_tool_contexts` fixture with `autouse=True`
  - Fixture clears all 5 tool `_repository_context` dictionaries after each test
  - Import all tool modules in fixture
  - **Validation**: `uv run pytest tests/test_tools/conftest.py::test_import -v` (if such test exists)

### Test File Updates (Can parallelize per tool)
- [ ] **Task 2.2**: Update test_spell_lookup.py (8 tests)
  - Replace all `repository=mock_repo` parameter usage
  - Update to inject via `spell_lookup._repository_context["repository"] = mock_repo`
  - Verify cleanup fixture works (no test pollution)
  - **Validation**: `uv run pytest tests/test_tools/test_spell_lookup.py -v` (8/8 passing)

- [ ] **Task 2.3**: Update test_creature_lookup.py (10 tests)
  - Replace all `repository=mock_repo` parameter usage
  - Update to inject via `creature_lookup._repository_context["repository"] = mock_repo`
  - **Validation**: `uv run pytest tests/test_tools/test_creature_lookup.py -v` (10/10 passing)

- [ ] **Task 2.4**: Update test_equipment_lookup.py (10 tests)
  - Replace all `repository=mock_repo` parameter usage
  - Update to inject via `equipment_lookup._repository_context["repository"] = mock_repo`
  - **Validation**: `uv run pytest tests/test_tools/test_equipment_lookup.py -v` (10/10 passing)

- [ ] **Task 2.5**: Update test_character_option_lookup.py (14 tests)
  - Replace all `repository=mock_repo` parameter usage
  - Update to inject via `character_option_lookup._repository_context["repository"] = mock_repo`
  - **Validation**: `uv run pytest tests/test_tools/test_character_option_lookup.py -v` (14/14 passing)

- [ ] **Task 2.6**: Update test_rule_lookup.py (12 tests)
  - Replace all `repository=mock_repo` parameter usage
  - Update to inject via `rule_lookup._repository_context["repository"] = mock_repo`
  - **Validation**: `uv run pytest tests/test_tools/test_rule_lookup.py -v` (12/12 passing)

### Integration Test Updates
- [ ] **Task 2.7**: Verify integration tests still work
  - Check if `tests/test_tools/test_integration.py` needs updates
  - Integration tests should work without changes (they don't inject repositories)
  - **Validation**: `uv run pytest tests/test_tools/test_integration.py -v -m integration`

### Phase 2 Validation
- [ ] **Task 2.8**: Run all tool tests
  - **Validation**: `uv run pytest tests/test_tools/ -v` (all 54+ tests passing)
  - **Validation**: No test failures or flaky tests due to context pollution

## Phase 3: Update Specs and Documentation

### Spec Updates
- [ ] **Task 3.1**: Update tool-repository-migration spec
  - Edit `openspec/changes/implement-repository-pattern/specs/tool-repository-migration/spec.md`
  - Remove all acceptance criteria about "Add optional `repository` parameter"
  - Update criteria to describe internal repository acquisition via `_get_repository()`
  - Add requirements about module-level context for testing
  - Update all 5 tool requirements (spell, creature, equipment, character_option, rule)
  - **Validation**: `openspec validate implement-repository-pattern --strict`

- [ ] **Task 3.2**: Update implement-repository-pattern proposal
  - Edit `openspec/changes/implement-repository-pattern/proposal.md`
  - Update success criteria to reflect internal repository usage (no public parameter)
  - Add note about subsequent fix in this change proposal
  - **Validation**: Manual review for consistency

- [ ] **Task 3.3**: Update implement-repository-pattern tasks
  - Edit `openspec/changes/implement-repository-pattern/tasks.md`
  - Mark relevant tasks as "Updated by remove-repository-parameter change"
  - Add cross-reference to this change proposal
  - **Validation**: Manual review

### Documentation Updates
- [ ] **Task 3.4**: Update architecture documentation
  - Check if `docs/architecture.md` mentions repository parameter
  - Update any references to tool implementation patterns
  - Ensure documentation reflects internal dependency injection
  - **Validation**: Manual review of documentation

- [ ] **Task 3.5**: Update testing documentation
  - Check if `docs/testing.md` has examples of tool testing
  - Update examples to show context injection pattern
  - Add example of `_repository_context` usage
  - **Validation**: Manual review

### Phase 3 Validation
- [ ] **Task 3.6**: Validate all specs
  - **Validation**: `openspec validate --all --strict`
  - **Validation**: No validation errors

## Phase 4: Final Validation and MCP Testing

### Code Quality
- [ ] **Task 4.1**: Run type checking
  - **Validation**: `uv run mypy src/` (no errors)
  - **Validation**: No `Any` type parameters in tool functions

- [ ] **Task 4.2**: Run linting and formatting
  - **Validation**: `uv run ruff check src/ tests/` (no errors)
  - **Validation**: `uv run ruff format src/ tests/ --check` (no changes needed)

- [ ] **Task 4.3**: Run pre-commit hooks
  - **Validation**: `uv run pre-commit run --all-files` (all hooks pass)

### Test Suite
- [ ] **Task 4.4**: Run full test suite
  - **Validation**: `uv run pytest -v` (all tests passing)
  - **Validation**: No test failures or warnings

### MCP Server Validation
- [ ] **Task 4.5**: Inspect MCP tool schemas
  - Start MCP server: `uv run python -m lorekeeper_mcp`
  - Use MCP client or inspection tool to view tool schemas
  - Verify `repository` parameter is NOT present in any tool
  - Verify all tools still have correct domain parameters
  - **Validation**: Manual inspection confirms clean schemas

- [ ] **Task 4.6**: Test MCP tools functionally
  - Test each tool via MCP client:
    - `lookup_spell(name="Fireball")` - should work
    - `lookup_creature(name="Dragon")` - should work
    - `lookup_equipment(type="weapon")` - should work
    - `lookup_character_option(type="class")` - should work
    - `lookup_rule(type="condition")` - should work
  - Verify all tools return correct data
  - Verify caching still works (second call is faster)
  - **Validation**: Manual functional testing with real MCP client

### Documentation
- [ ] **Task 4.7**: Create migration guide
  - Document the change for maintainers
  - Explain old pattern vs new pattern
  - Provide examples of test updates
  - Add to change proposal or separate migration doc
  - **Validation**: Manual review

## Summary
- **Total Tasks**: 24 tasks across 4 phases
- **Estimated Effort**: Small to Medium (1-2 days for careful implementation)
- **Parallelization**: Phase 1 and Phase 2 tool updates can be parallelized
- **Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4
- **Key Validation**: Type checks pass, all tests pass, MCP schemas clean

## Risk Mitigation
- Implement one tool at a time to catch issues early
- Run tests after each tool update to verify no breakage
- Use Git branching for safe rollback
- Keep old code commented out initially for easy revert if needed

## Success Criteria (Final)
- [ ] All 5 tools have NO `repository` parameter in signatures
- [ ] All 54 tool unit tests passing with new injection pattern
- [ ] Type checking passes with no `Any` parameter warnings
- [ ] MCP tool schemas validated (no `repository` field visible)
- [ ] Integration tests passing
- [ ] Manual MCP functional testing successful
- [ ] All specs updated and validated
- [ ] Documentation updated
