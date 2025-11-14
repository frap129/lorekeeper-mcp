# Implementation Tasks: add-serve-command

## Task List

### 1. Add serve command to CLI
**Description**: Implement the `serve` command in `src/lorekeeper_mcp/cli.py`

**Acceptance Criteria**:
- [x] `@cli.command()` decorated function `serve` added to cli.py
- [x] Function accepts Click context to access global options (db_path, verbose)
- [x] Function imports and calls `mcp.run()` from server module
- [x] Command has appropriate docstring visible in help text
- [x] Global options (--db-path, --verbose) are respected

**Dependencies**: None

**Estimated Effort**: 15 minutes

**Validation**:
- Run `lorekeeper serve` - server starts
- Run `lorekeeper serve --help` - displays help text
- Run `lorekeeper -v serve` - server starts with verbose logging

---

### 2. Update __main__.py routing logic
**Description**: Modify `src/lorekeeper_mcp/__main__.py` to maintain backward compatibility

**Acceptance Criteria**:
- [x] When no arguments: still runs `mcp.run()` (backward compatible)
- [x] When arguments present: delegates to `cli.main()`
- [x] Logic cleanly handles both cases
- [x] Comments explain the routing decision

**Dependencies**: Task 1

**Estimated Effort**: 10 minutes

**Validation**:
- Run `python -m lorekeeper_mcp` - server starts (backward compatible)
- Run `python -m lorekeeper_mcp serve` - server starts via CLI
- Run `python -m lorekeeper_mcp import file.orcbrew` - CLI import works

---

### 3. Add unit tests for serve command
**Description**: Create tests in `tests/test_cli/test_serve.py` (new file)

**Acceptance Criteria**:
- [x] Test file created at `tests/test_cli/test_serve.py`
- [x] Test: `serve` command is registered and callable
- [x] Test: serve command respects global --verbose flag
- [x] Test: serve command respects global --db-path option
- [x] Tests use Click's CliRunner for isolation
- [x] Tests mock `mcp.run()` to avoid actually starting server

**Dependencies**: Task 1

**Estimated Effort**: 30 minutes

**Validation**:
- Run `uv run pytest tests/test_cli/test_serve.py` - all tests pass
- Run `just test` - no regressions

---

### 4. Update backward compatibility tests
**Description**: Verify `__main__.py` routing in `tests/test_cli_basic.py`

**Acceptance Criteria**:
- [x] Test: running module without args still starts server
- [x] Test: running module with CLI args routes to CLI
- [x] Tests mock `mcp.run()` and `cli.main()` appropriately
- [x] Tests verify both code paths are exercised

**Dependencies**: Task 2

**Estimated Effort**: 20 minutes

**Validation**:
- Run `uv run pytest tests/test_cli_basic.py` - all tests pass
- Both routing paths are verified

---

### 5. Update documentation
**Description**: Update README.md and docs/cli-usage.md to reference new command

**Acceptance Criteria**:
- [x] README.md "Running the Server" section updated to show `lorekeeper serve`
- [x] README.md maintains backward compatible example for reference
- [x] docs/cli-usage.md adds `serve` command to Commands section
- [x] docs/cli-usage.md includes usage examples and options

**Dependencies**: Task 1, Task 2

**Estimated Effort**: 15 minutes

**Validation**:
- Review documentation for clarity and accuracy
- Ensure examples are copy-paste ready

---

### 6. Run full test suite and quality checks
**Description**: Ensure all tests pass and code quality is maintained

**Acceptance Criteria**:
- [x] `just test` - all tests pass (including live tests if applicable)
- [x] `just lint` - no linting errors
- [x] `just type-check` - no type errors
- [x] `just format` - code is formatted

**Dependencies**: All previous tasks

**Estimated Effort**: 10 minutes

**Validation**:
- All quality checks pass
- Ready for commit

---

## Parallelizable Work
- Tasks 3 and 5 can be done in parallel after Task 1 completes
- Task 4 requires Task 2 but is independent of Tasks 3 and 5

## Total Estimated Effort
~100 minutes (~1.5 hours)

## Validation Strategy
1. Manual testing: verify all documented usage patterns work
2. Unit tests: ensure isolated command behavior is correct
3. Integration: verify __main__.py routing logic
4. Quality checks: ensure code standards are met
5. Documentation review: ensure examples are accurate
