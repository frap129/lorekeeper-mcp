# Implementation Tasks: List and Filter Open5e Documents

## Overview
This document outlines the implementation tasks for adding document listing and configuration capabilities to LoreKeeper MCP. Tasks are ordered to deliver incremental value with minimal risk.

## Phase 1: Document Listing CLI Command

### Task 1.1: Extend Configuration with Document Fields
**Priority:** High
**Estimated Effort:** 30 minutes
**Dependencies:** None

**Steps:**
1. Add `included_documents` field to `Settings` class in `src/lorekeeper_mcp/config.py`
2. Add `excluded_documents` field to `Settings` class
3. Add field validator to parse comma-separated strings into lists
4. Add `is_document_enabled(key: str)` helper method to Settings
5. Update `.env.example` with documentation and examples

**Acceptance Criteria:**
- Settings class has both new fields with proper type hints
- Fields default to `None`
- Environment variables `INCLUDED_DOCUMENTS` and `EXCLUDED_DOCUMENTS` are loaded
- Comma-separated parsing works correctly
- Configuration validates basic format (alphanumeric, hyphens, underscores)

**Testing:**
- Unit test for configuration loading from environment
- Unit test for comma-separated parsing
- Unit test for `is_document_enabled()` method
- Unit test for conflict resolution (included takes precedence)

---

### Task 1.2: Add CLI Argument Parsing to __main__.py
**Priority:** High
**Estimated Effort:** 45 minutes
**Dependencies:** None

**Steps:**
1. Import `argparse` in `src/lorekeeper_mcp/__main__.py`
2. Create argument parser with subcommands: `run` (default) and `list-documents`
3. Add `list-documents` subcommand with options: `--format`, `--publisher`, `--game-system`, `--refresh`
4. Modify main entry point to route to appropriate handler
5. Keep default behavior (no args = run server)

**Acceptance Criteria:**
- `lorekeeper-mcp list-documents` command exists
- `lorekeeper-mcp` (no args) still runs the server
- All flags parse correctly (`--format json`, `-p "Publisher"`, etc.)
- Help text is clear and useful
- Exit codes are correct (0 for success, 1 for errors)

**Testing:**
- Integration test for CLI parsing
- Test help output
- Test default behavior preserved

---

### Task 1.3: Implement Document Listing Logic
**Priority:** High
**Estimated Effort:** 1 hour
**Dependencies:** Task 1.2

**Steps:**
1. Create `src/lorekeeper_mcp/cli/` directory
2. Create `src/lorekeeper_mcp/cli/documents.py` module
3. Implement `list_documents()` async function that calls Open5eV2Client
4. Implement filtering by publisher and game-system
5. Add error handling for API failures
6. Implement caching with 7-day TTL using SQLite cache

**Acceptance Criteria:**
- Function fetches documents from Open5e API v2
- Returns list of document dictionaries
- Filters work correctly (publisher, game-system)
- Cache reduces redundant API calls
- Graceful error handling with helpful messages

**Testing:**
- Unit test with mocked Open5eV2Client
- Test filtering logic
- Test cache hit/miss scenarios
- Integration test with real API (marked with pytest marker for CI skip)

---

### Task 1.4: Implement Table Output Formatter
**Priority:** High
**Estimated Effort:** 45 minutes
**Dependencies:** Task 1.3

**Steps:**
1. Create `src/lorekeeper_mcp/cli/formatters.py` module
2. Implement `format_documents_table()` function
3. Use simple ASCII table formatting (no external dependencies)
4. Handle truncation for long fields with ellipsis
5. Make columns: Key, Display Name, Publisher, License
6. Adapt to terminal width if possible (fallback to 80 chars)

**Acceptance Criteria:**
- Table output is human-readable and aligned
- Truncation works for long content
- Headers are clear
- All documents fit without excessive scrolling
- Works on various terminal widths

**Testing:**
- Unit test with sample document data
- Visual testing in terminal
- Test with 1 document, 5 documents, and 25+ documents

---

### Task 1.5: Implement JSON Output Formatter
**Priority:** Medium
**Estimated Effort:** 15 minutes
**Dependencies:** Task 1.3

**Steps:**
1. Add `format_documents_json()` function to `formatters.py`
2. Use `json.dumps()` with proper indentation
3. Ensure all fields are included
4. Handle datetime serialization

**Acceptance Criteria:**
- Valid JSON output
- Pretty-printed with indentation
- All document fields included
- Can be piped to `jq`

**Testing:**
- Unit test validating JSON structure
- Test JSON parsing with `json.loads()`
- Integration test with `jq` piping

---

### Task 1.6: Wire CLI Command to Handler
**Priority:** High
**Estimated Effort:** 30 minutes
**Dependencies:** Tasks 1.2, 1.3, 1.4, 1.5

**Steps:**
1. Create async handler function in `cli/documents.py`
2. Call `list_documents()` with appropriate filters
3. Format output based on `--format` flag
4. Print to stdout
5. Handle errors and return appropriate exit codes
6. Update `__main__.py` to call handler

**Acceptance Criteria:**
- `lorekeeper-mcp list-documents` works end-to-end
- All format and filter options work
- Error messages are helpful
- Exit codes are correct

**Testing:**
- End-to-end test of full command
- Test all flag combinations
- Test error scenarios

---

## Phase 2: Server Configuration and Logging

### Task 2.1: Add Server Startup Logging
**Priority:** Medium
**Estimated Effort:** 30 minutes
**Dependencies:** Task 1.1

**Steps:**
1. Update `src/lorekeeper_mcp/server.py` lifespan function
2. Add logging statements showing document configuration
3. Log included/excluded documents if configured
4. Log warnings for conflicts
5. Use INFO log level for normal config, WARNING for issues

**Acceptance Criteria:**
- Server logs document configuration on startup
- Logs are clear and concise
- Shows number of documents and keys (if not too many)
- Warnings appear for conflicts or invalid keys

**Testing:**
- Integration test checking log output
- Test with various configurations
- Verify log levels are correct

---

### Task 2.2: Add Configuration Validation
**Priority:** Medium
**Estimated Effort:** 30 minutes
**Dependencies:** Task 1.1

**Steps:**
1. Add Pydantic validator to Settings class
2. Validate document key format (regex: `^[a-z0-9][a-z0-9-_]*$`)
3. Log warnings for invalid keys but continue operation
4. Add conflict detection (both included and excluded set)

**Acceptance Criteria:**
- Invalid keys trigger warnings
- Validation doesn't require API call
- Server starts despite invalid configuration
- Valid keys still work

**Testing:**
- Unit test for validation logic
- Test with invalid key formats
- Test with conflicting configuration

---

## Phase 3: Documentation and Polish

### Task 3.1: Update Documentation
**Priority:** Low
**Estimated Effort:** 30 minutes
**Dependencies:** All previous tasks

**Steps:**
1. Update `.env.example` with document configuration examples
2. Update README.md with document filtering section
3. Add examples of common use cases
4. Document CLI command and options

**Acceptance Criteria:**
- `.env.example` has clear, commented examples
- README explains feature and usage
- Examples are practical and helpful

---

### Task 3.2: Add Integration Tests
**Priority:** Medium
**Estimated Effort:** 1 hour
**Dependencies:** All implementation tasks

**Steps:**
1. Create `tests/test_cli/` directory
2. Add integration tests for CLI command
3. Add integration tests for configuration loading
4. Add live API test (marked for CI skip)

**Acceptance Criteria:**
- Tests cover happy path and error cases
- Tests can run without network (mocked)
- Live tests verify API integration

---

## Task Summary

**Total Estimated Effort:** ~6 hours

### Critical Path:
1. Task 1.1 → Task 1.2 → Task 1.3 → Task 1.6 (Minimum viable CLI)
2. Task 1.4 (Table output)
3. Task 2.1 (Server logging)

### Parallelizable:
- Task 1.4 and 1.5 can be done in parallel
- Task 2.1 and 2.2 can be done in parallel with Phase 1
- Task 3.1 can be done anytime after implementation

### Priority Order:
1. **High:** Tasks 1.1, 1.2, 1.3, 1.4, 1.6 (Core functionality)
2. **Medium:** Tasks 1.5, 2.1, 2.2, 3.2 (Enhancements and quality)
3. **Low:** Task 3.1 (Documentation polish)

## Validation Checklist

Before marking this change as complete:
- [ ] `lorekeeper-mcp list-documents` command works
- [ ] Both table and JSON output formats work
- [ ] Publisher and game-system filters work
- [ ] Configuration loads from environment variables
- [ ] Server logs document configuration on startup
- [ ] Conflicts are detected and handled
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] No breaking changes to existing functionality
- [ ] Exit codes are correct
- [ ] Error messages are helpful
