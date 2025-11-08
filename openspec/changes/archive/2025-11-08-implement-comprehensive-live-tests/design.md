# Design: Comprehensive Live MCP Testing

## Context

Current testing strategy uses mocked HTTP responses (respx) for deterministic, fast unit tests. However, these mocks don't catch:
- API schema changes or breaking changes
- Real-world API behavior (rate limits, timeouts, error responses)
- Cache effectiveness with actual API response patterns
- Data validation issues with live data

Two standalone scripts exist (`test_mcp_tools.py`, `test_mcp_tools_live.py`) but they:
- Are not integrated with pytest infrastructure
- Lack comprehensive coverage and validation
- Don't provide structured pass/fail reporting
- Can't be run selectively or in CI pipelines

## Goals / Non-Goals

### Goals
- Integrate live testing into pytest infrastructure with proper markers
- Validate all MCP tools against real APIs with comprehensive scenarios
- Test error handling, retry logic, and cache behavior with live data
- Provide clear pass/fail reporting and performance metrics
- Enable selective test execution (unit vs live tests)
- Document best practices for live API testing

### Non-Goals
- Replace unit tests with mocks (keep both approaches)
- Run live tests in standard CI pipeline (too slow, API-dependent)
- Test every possible parameter combination (focus on critical paths)
- Implement new MCP tool features (testing only)

## Decisions

### Test Organization

**Decision**: Create single comprehensive test file `tests/test_tools/test_live_mcp.py`

**Rationale**:
- Centralizes all live testing logic
- Easy to skip with pytest markers
- Clear separation from mocked unit tests
- Follows existing test structure pattern

**Alternatives considered**:
- Separate file per tool: Too fragmented, harder to share fixtures
- Mixed with unit tests: Confusing, harder to skip live tests

### Pytest Markers

**Decision**: Use `@pytest.mark.live` for all live API tests

**Rationale**:
- Standard pytest pattern for slow/external tests
- Easy to skip: `pytest -m "not live"`
- Easy to run only live tests: `pytest -m live`
- Can combine with other markers (e.g., `@pytest.mark.slow`)

**Configuration**:
```toml
[tool.pytest.ini_options]
markers = [
    "live: marks tests as live API tests (deselect with '-m \"not live\"')",
    "slow: marks tests as slow running (>1s)",
]
```

### Fixtures Strategy

**Decision**: Create dedicated fixtures for live testing in `conftest.py`

**Fixtures**:
1. `live_db` - Real database with optional reset capability
2. `api_client_factory` - Factory for creating API clients without mocks
3. `rate_limiter` - Fixture to avoid hitting API rate limits during test runs
4. `cache_stats` - Fixture to track cache hit/miss rates

**Rationale**:
- Reusable across all live tests
- Centralized configuration (TTL, rate limits)
- Can track test execution state
- Enables performance monitoring

### Test Coverage Strategy

**Decision**: Organize tests by tool with comprehensive scenarios per tool

**Test structure**:
```python
class TestLiveSpellLookup:
    """Live tests for lookup_spell tool."""

    # Basic functionality
    async def test_spell_by_name_found(self)
    async def test_spell_by_name_not_found(self)

    # Parameter combinations
    async def test_spell_filter_by_level_and_school(self)
    async def test_spell_filter_by_class_and_concentration(self)

    # Edge cases
    async def test_spell_special_characters_in_name(self)
    async def test_spell_limit_boundary_conditions(self)

    # Cache behavior
    async def test_spell_cache_hit_on_duplicate_query(self)
    async def test_spell_cache_miss_on_new_query(self)

    # Error handling
    async def test_spell_handles_api_timeout(self)
    async def test_spell_handles_invalid_parameters(self)
```

**Coverage areas per tool**:
1. **Basic queries**: Name search, simple filters
2. **Complex filters**: Multi-parameter combinations
3. **Edge cases**: Empty results, special characters, boundary values
4. **Cache validation**: Hit/miss behavior, TTL enforcement
5. **Error handling**: Network errors, invalid params, API errors
6. **Data validation**: Response schema, type correctness, required fields

### Performance Tracking

**Decision**: Add performance assertions and benchmarks

**Implementation**:
```python
async def test_spell_lookup_performance(self, cache_stats):
    """Verify spell lookup meets performance targets."""
    start = time.time()
    results = await lookup_spell(name="fireball")
    duration = time.time() - start

    # Cache miss should be under 2s
    assert duration < 2.0, f"Lookup took {duration:.2f}s"

    # Second query should use cache (under 50ms)
    start = time.time()
    cached_results = await lookup_spell(name="fireball")
    cached_duration = time.time() - start

    assert cached_duration < 0.05, f"Cached lookup took {cached_duration:.2f}s"
    assert cache_stats.hits == 1
```

### Error Simulation

**Decision**: Test error handling without mocking (use invalid inputs)

**Approach**:
- Invalid parameters (wrong types, out of range values)
- Missing required parameters (None values)
- Queries returning empty results
- Very large result sets (test pagination)

**Rationale**: Can test error paths without complex mocking infrastructure

### Rate Limiting

**Decision**: Add delays between live API calls to respect rate limits

**Implementation**:
```python
@pytest.fixture
async def rate_limiter():
    """Enforce rate limiting between API calls."""
    last_call = {}

    async def wait_if_needed(api_name: str, min_delay: float = 0.1):
        if api_name in last_call:
            elapsed = time.time() - last_call[api_name]
            if elapsed < min_delay:
                await asyncio.sleep(min_delay - elapsed)
        last_call[api_name] = time.time()

    return wait_if_needed
```

### Test Data Strategy

**Decision**: Use well-known D&D entities for predictable results

**Test data set**:
- Spells: "Magic Missile", "Fireball", "Wish", "Light" (cantrip)
- Creatures: "Goblin", "Ancient Red Dragon", "Tarrasque", "Commoner"
- Equipment: "Longsword", "Plate Armor", "Bag of Holding"
- Classes: "Wizard", "Fighter", "Cleric"
- Conditions: "Prone", "Grappled", "Invisible"

**Rationale**:
- Well-known entities are stable across API versions
- Easy to verify correctness manually
- Cover range of levels, CRs, rarities

### Documentation

**Decision**: Add comprehensive live testing section to `docs/testing.md`

**Content**:
- How to run live tests
- When to run live tests (pre-release, API changes)
- How to interpret failures
- Rate limiting considerations
- Adding new live tests

## Risks / Trade-offs

### Risk: API Rate Limiting
- **Impact**: Tests could trigger rate limits, causing failures
- **Mitigation**: Add delays between calls, run sparingly, document rate limits
- **Acceptance**: Live tests are manual/optional, not in standard CI

### Risk: API Changes
- **Impact**: Tests could fail due to upstream API changes
- **Mitigation**: Pin to stable entities, document expected data, separate from unit tests
- **Acceptance**: Failures indicate real issues we need to address

### Risk: Test Duration
- **Impact**: Live tests will be slow (1-2 minutes total)
- **Mitigation**: Use pytest markers to skip by default, run on-demand
- **Acceptance**: Acceptable for comprehensive validation

### Risk: Network Dependency
- **Impact**: Tests fail without internet connection
- **Mitigation**: Clear error messages, pytest markers, documentation
- **Acceptance**: Expected behavior for live tests

### Trade-off: Coverage vs Speed
- **Decision**: Focus on critical paths and edge cases, not exhaustive combinations
- **Rationale**: Balance thoroughness with practical test execution time
- **Outcome**: ~30-50 live tests covering key scenarios per tool

## Migration Plan

### Phase 1: Infrastructure (Week 1)
1. Add pytest markers to `pyproject.toml`
2. Create fixtures in `tests/conftest.py`
3. Create skeleton `tests/test_tools/test_live_mcp.py`
4. Validate infrastructure with 1-2 simple tests

### Phase 2: Comprehensive Tests (Week 2)
1. Implement spell lookup live tests (all scenarios)
2. Implement creature lookup live tests
3. Implement equipment lookup live tests
4. Implement character option lookup live tests
5. Implement rule lookup live tests

### Phase 3: Validation & Documentation (Week 3)
1. Run full live test suite, fix issues
2. Add performance benchmarks
3. Update `docs/testing.md` with live testing guide
4. Add CI workflow for manual live test execution
5. Deprecate `test_mcp_tools_live.py`

### Rollback
If live tests prove problematic:
- Remove `@pytest.mark.live` from default runs
- Keep as optional validation tool
- No impact on existing unit tests

## Open Questions

1. Should we run live tests in CI on a schedule (e.g., nightly)?
   - **Answer pending**: Evaluate after implementation

2. What's the appropriate rate limit delay between API calls?
   - **Initial**: 100ms between calls
   - **Adjust**: Based on observed rate limits

3. Should we cache API responses for faster subsequent live test runs?
   - **Decision**: No - defeats purpose of testing live behavior
   - **Alternative**: Clear cache before each test

4. How do we handle API outages during live tests?
   - **Decision**: Tests fail with clear error message
   - **Rationale**: Indicates real availability issue
