# Implementation Tasks: --build-cache Flag

This document outlines the ordered sequence of tasks to implement the `--build-cache` flag feature.

## Prerequisites

- `replace-sqlite-with-marqo` change MUST be completed and merged first
- Marqo service available for local testing
- All existing tests passing

## Task Breakdown

### Phase 1: Foundation (0.5 days)

#### Task 1.1: Add argparse to __main__.py
**Effort**: 0.25 days

Add CLI argument parsing to support `--build-cache` flag.

**Acceptance Criteria**:
- `argparse.ArgumentParser` configured in `__main__.py`
- `--build-cache` flag defined as boolean action
- `--help` displays usage information
- Default behavior (no args) starts MCP server normally
- Tests verify argument parsing

**Files Modified**:
- `src/lorekeeper_mcp/__main__.py`

**Tests Required**:
- Unit test: `test_argparse_no_args()` → starts server
- Unit test: `test_argparse_build_cache()` → calls build_cache()
- Unit test: `test_argparse_help()` → displays help

---

#### Task 1.2: Create cache_builder.py skeleton
**Effort**: 0.25 days

Create new module with main entry point and stub functions.

**Acceptance Criteria**:
- `src/lorekeeper_mcp/cache_builder.py` created
- `async def build_cache() -> int` entry point defined
- Returns exit code 0 (stub implementation)
- Type hints present on all functions
- Docstrings with Google style

**Files Created**:
- `src/lorekeeper_mcp/cache_builder.py`

**Tests Required**:
- Unit test: `test_build_cache_stub()` → returns 0

---

### Phase 2: API Client Extensions (1.0 days)

#### Task 2.1: Add fetch_all_*() methods to Open5eV2Client
**Effort**: 0.35 days

Implement complete fetching with pagination for Open5e v2 API.

**Acceptance Criteria**:
- `fetch_all_spells()` handles pagination, returns all spells
- `fetch_all_weapons()` handles pagination, returns all weapons
- `fetch_all_armor()` handles pagination, returns all armor
- `fetch_all_backgrounds()` handles pagination, returns all backgrounds
- `fetch_all_feats()` handles pagination, returns all feats
- `fetch_all_conditions()` handles pagination, returns all conditions
- Generic `_fetch_all_paginated()` helper method implemented
- All methods use `use_cache=False` for fresh data

**Files Modified**:
- `src/lorekeeper_mcp/api_clients/open5e_v2.py`

**Tests Required**:
- Integration test: `test_fetch_all_spells()` with mock API (2 pages)
- Integration test: `test_fetch_all_weapons()` with mock API (1 page)
- Unit test: `test_fetch_all_handles_empty_results()`
- Unit test: `test_fetch_all_handles_no_next_url()`

---

#### Task 2.2: Add fetch_all_*() methods to Open5eV1Client
**Effort**: 0.3 days

Implement complete fetching with pagination for Open5e v1 API.

**Acceptance Criteria**:
- `fetch_all_monsters()` handles pagination, returns all monsters
- `fetch_all_classes()` handles pagination, returns all classes
- `fetch_all_races()` handles pagination, returns all races
- Generic `_fetch_all_paginated()` helper method implemented
- All methods use `use_cache=False` for fresh data

**Files Modified**:
- `src/lorekeeper_mcp/api_clients/open5e_v1.py`

**Tests Required**:
- Integration test: `test_fetch_all_monsters()` with mock API (multiple pages)
- Integration test: `test_fetch_all_classes()` with mock API

---

#### Task 2.3: Add fetch_all_*() methods to DnD5eAPIClient
**Effort**: 0.35 days

Implement complete fetching with pagination for D&D 5e API.

**Acceptance Criteria**:
- `fetch_all_rules()` handles pagination, returns all rules
- `fetch_all_rule_sections()` handles pagination, returns all rule sections
- Generic `_fetch_all_paginated()` helper method implemented (different API structure)
- All methods use `use_cache=False` for fresh data

**Files Modified**:
- `src/lorekeeper_mcp/api_clients/dnd5e_api.py`

**Tests Required**:
- Integration test: `test_fetch_all_rules()` with mock API
- Integration test: `test_fetch_all_rule_sections()` with mock API

---

### Phase 3: Cache Builder Orchestration (1.0 days)

#### Task 3.1: Implement Marqo initialization check
**Effort**: 0.2 days

Add Marqo health check and index initialization to cache builder.

**Acceptance Criteria**:
- `init_marqo()` function calls `init_indexes()` from marqo cache module
- `check_marqo_health()` verifies Marqo is reachable
- Returns exit code 1 if Marqo unavailable
- Logs error message with Marqo URL

**Files Modified**:
- `src/lorekeeper_mcp/cache_builder.py`

**Tests Required**:
- Unit test: `test_marqo_unavailable()` → returns 1
- Unit test: `test_marqo_available()` → proceeds to fetch

---

#### Task 3.2: Implement entity fetching orchestration
**Effort**: 0.4 days

Orchestrate fetching from all API clients in parallel.

**Acceptance Criteria**:
- `fetch_all_entities()` calls all client `fetch_all_*()` methods
- Uses `asyncio.gather()` with `return_exceptions=True` for parallel fetching
- Returns dict of `entity_type -> list[entity_dict]`
- Handles client failures gracefully (logs error, continues)
- Deduplicates entities by slug (last-write-wins)

**Files Modified**:
- `src/lorekeeper_mcp/cache_builder.py`

**Tests Required**:
- Unit test: `test_fetch_all_entities()` with mock clients
- Unit test: `test_fetch_handles_client_failure()` → continues with other clients
- Unit test: `test_fetch_deduplicates_by_slug()`

---

#### Task 3.3: Implement batch indexing to Marqo
**Effort**: 0.4 days

Index fetched entities to Marqo in optimized batches.

**Acceptance Criteria**:
- `index_entities_to_marqo()` batches entities by 100 (configurable)
- Calls `bulk_cache_entities()` for each batch
- Handles batch failures (logs error, continues with next batch)
- Returns count of successfully indexed entities

**Files Modified**:
- `src/lorekeeper_mcp/cache_builder.py`

**Tests Required**:
- Unit test: `test_index_entities_batched()` → verifies batch size
- Unit test: `test_index_handles_batch_failure()` → continues with remaining batches
- Integration test: `test_index_to_marqo()` with real Marqo (few entities)

---

### Phase 4: Progress Reporting (0.5 days)

#### Task 4.1: Add progress logging
**Effort**: 0.3 days

Emit progress logs during fetch and index phases.

**Acceptance Criteria**:
- Logs "Fetching {entity_type} from {client}..." before fetch
- Logs "Fetched {count} {entity_type}" after fetch
- Logs "Indexing {count} {entity_type}..." before index
- Logs "✓ Indexed {count} {entity_type}" after index
- Logs errors with context (entity_type, client, error message)

**Files Modified**:
- `src/lorekeeper_mcp/cache_builder.py`

**Tests Required**:
- Integration test: `test_progress_logging()` → verifies log messages emitted
- Unit test: `test_error_logging()` → verifies error context included

---

#### Task 4.2: Add build summary report
**Effort**: 0.2 days

Log comprehensive summary after cache build completes.

**Acceptance Criteria**:
- Summary includes: total entities, entity types built, duration, status
- Summary distinguishes success vs partial success
- Failed entity types listed in summary
- Pretty formatted with borders
- Build duration measured with `time.perf_counter()`

**Files Modified**:
- `src/lorekeeper_mcp/cache_builder.py`

**Tests Required**:
- Integration test: `test_build_summary_success()` → verifies summary format
- Integration test: `test_build_summary_partial()` → verifies partial success format

---

### Phase 5: Integration & Testing (0.75 days)

#### Task 5.1: Wire up CLI to cache builder
**Effort**: 0.25 days

Connect CLI argument parsing to cache builder invocation.

**Acceptance Criteria**:
- `__main__.py` calls `cache_builder.build_cache()` when `--build-cache` flag used
- Exit code from `build_cache()` propagated to `sys.exit()`
- MCP server NOT started when `--build-cache` flag used
- Async context properly initialized for cache builder

**Files Modified**:
- `src/lorekeeper_mcp/__main__.py`

**Tests Required**:
- End-to-end test: `test_build_cache_cli()` → runs full build with mock APIs

---

#### Task 5.2: Add comprehensive integration tests
**Effort**: 0.3 days

Test complete build flow with real Marqo and mock APIs.

**Acceptance Criteria**:
- Integration test with all clients mocked, real Marqo
- Validates all entity types indexed to Marqo
- Tests partial failure scenario (one client fails)
- Tests Marqo unavailable scenario
- Tests empty API response scenario

**Files Created**:
- `tests/test_cache_builder.py`

**Tests Required**:
- `test_build_cache_full_success()`
- `test_build_cache_partial_failure()`
- `test_build_cache_marqo_unavailable()`
- `test_build_cache_all_apis_fail()`
- `test_build_cache_empty_responses()`

---

#### Task 5.3: Add live tests (optional)
**Effort**: 0.2 days

Optional tests with real APIs for validation.

**Acceptance Criteria**:
- Live test fetches from real APIs (annotated with `@pytest.mark.live`)
- Indexes to real Marqo
- Validates entity counts are reasonable (> 0)
- Skipped by default (`pytest -m live` to run)

**Files Modified**:
- `tests/test_cache_builder.py`

**Tests Required**:
- `@pytest.mark.live test_build_cache_live()`

---

### Phase 6: Documentation & Polish (0.25 days)

#### Task 6.1: Update README.md
**Effort**: 0.15 days

Document `--build-cache` flag usage.

**Acceptance Criteria**:
- README includes `--build-cache` flag in usage examples
- Build cache section explains purpose and usage
- Example commands provided
- Expected build time mentioned

**Files Modified**:
- `README.md`

---

#### Task 6.2: Add docstrings and type hints
**Effort**: 0.1 days

Ensure all new code has proper documentation.

**Acceptance Criteria**:
- All public functions have Google-style docstrings
- All functions have type hints (strict mypy)
- No `Any` types used where avoidable
- Module docstring for `cache_builder.py`

**Files Modified**:
- All modified files

---

## Testing Strategy

### Unit Tests
- Mock all external dependencies (API clients, Marqo)
- Test individual functions in isolation
- Fast execution (< 1s total)

### Integration Tests
- Real Marqo (Docker container in CI)
- Mock external APIs (respx)
- Validate end-to-end flows
- Medium execution time (5-10s total)

### Live Tests
- Real external APIs + real Marqo
- Validate actual API contracts
- Slow execution (30-60s)
- Skipped by default (`-m live` to enable)

---

## Validation Checklist

Before marking complete:

- [ ] All unit tests pass: `uv run pytest tests/test_cache_builder.py -v`
- [ ] All integration tests pass: `uv run pytest tests/test_cache_builder.py -m integration`
- [ ] Live test passes (manual): `uv run pytest tests/test_cache_builder.py -m live`
- [ ] Lint passes: `uv run ruff check src/ tests/`
- [ ] Format passes: `uv run ruff format --check src/ tests/`
- [ ] Type check passes: `uv run mypy src/`
- [ ] Manual test: `uv run lorekeeper-mcp --build-cache` completes successfully
- [ ] Manual test: `uv run lorekeeper-mcp --help` shows `--build-cache` flag
- [ ] Manual test: `uv run lorekeeper-mcp` starts server normally
- [ ] Documentation updated: README includes `--build-cache` usage

---

## Dependencies

### Hard Dependencies
- `replace-sqlite-with-marqo` MUST be completed first
- Marqo service running (local or CI)

### Soft Dependencies
- None - this is a standalone feature

---

## Parallel Work Opportunities

These tasks can be parallelized:

- **Track 1**: Tasks 2.1, 2.2, 2.3 (API client extensions)
- **Track 2**: Task 3.1 (Marqo initialization)
- **Track 3**: Task 1.1, 1.2 (CLI foundation)

**After Track 1-3 complete**: Tasks 3.2, 3.3, 4.1, 4.2 (sequential)

**Final Phase**: Tasks 5.1, 5.2, 5.3, 6.1, 6.2 (mostly sequential)

---

## Estimated Timeline

| Phase | Tasks | Estimated Days | Cumulative |
|-------|-------|----------------|------------|
| 1. Foundation | 1.1-1.2 | 0.5 | 0.5 |
| 2. API Extensions | 2.1-2.3 | 1.0 | 1.5 |
| 3. Orchestration | 3.1-3.3 | 1.0 | 2.5 |
| 4. Progress Reporting | 4.1-4.2 | 0.5 | 3.0 |
| 5. Integration | 5.1-5.3 | 0.75 | 3.75 |
| 6. Documentation | 6.1-6.2 | 0.25 | 4.0 |

**Total**: ~4 days with sequential execution

**Total (Optimized)**: ~2.5 days with parallel execution (Tracks 1-3)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API rate limiting | Add exponential backoff, respect rate limit headers |
| Marqo connection issues | Fail fast with clear error, provide Marqo health check |
| Memory usage during bulk fetch | Batch processing (100 entities at a time) |
| Long build times (5+ min) | Parallel fetching, progress logging shows activity |
| Test flakiness | Use Docker-based Marqo fixtures, mock external APIs |

---

## Completion Criteria

This change is complete when:

1. All tasks marked complete
2. All tests passing (unit, integration, live)
3. Manual validation successful
4. Documentation updated
5. Code review approved
6. Merged to main branch
