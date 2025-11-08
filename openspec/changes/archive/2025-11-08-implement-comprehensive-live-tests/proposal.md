# Implement Comprehensive Live MCP Tests

## Why

The current live test scripts (`test_mcp_tools.py` and `test_mcp_tools_live.py`) provide basic validation but lack comprehensive coverage of real-world scenarios, edge cases, error handling, and cache behavior with actual API data. We need a pytest-based suite that validates:
- Complete MCP tool functionality against live APIs
- Error handling and recovery mechanisms
- Cache performance and correctness with real data
- API response validation and schema conformance
- Rate limiting and retry behavior

## What Changes

- Create comprehensive pytest-based live test suite in `tests/test_tools/test_live_mcp.py`
- Add pytest markers for live tests (`@pytest.mark.live`)
- Implement test fixtures for live API testing (optional cache clearing, rate limiting)
- Add validation for API response schemas and data types
- Test error scenarios (network failures, invalid queries, missing data)
- Validate cache hit/miss behavior with live data
- Add performance benchmarks for API calls and cache retrieval
- Document how to run live tests and interpret results
- **BREAKING**: Deprecate standalone `test_mcp_tools_live.py` script in favor of pytest suite

## Impact

- **Affected specs**: New capability `mcp-live-testing`
- **Affected code**:
  - `tests/test_tools/test_live_mcp.py` (new comprehensive test suite)
  - `tests/conftest.py` (add live test fixtures and markers)
  - `pyproject.toml` (add pytest marker configuration)
  - `test_mcp_tools_live.py` (deprecate after migration)
  - `test_mcp_tools.py` (keep as example/manual testing script)
- **Dependencies**: None (uses existing testing infrastructure)
- **Documentation**: `docs/testing.md` (add live testing section)
