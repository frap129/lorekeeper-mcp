# testing-infrastructure Specification

## Purpose
Defines the pytest testing infrastructure including async test support via pytest-asyncio, test fixtures for temporary databases and mock API clients, test organization mirroring source structure, and configuration in pyproject.toml with automatic asyncio mode.
## Requirements
### Requirement: pytest must be configured for async testing

The project SHALL use pytest with asyncio support for testing async code.

#### Scenario: Async tests can be written and executed
```
GIVEN pytest and pytest-asyncio are installed
WHEN writing tests with async def test_*
THEN tests can use await keyword
AND async fixtures are supported
AND tests run with pytest command
```

#### Scenario: Test discovery works correctly
```
GIVEN tests in the tests/ directory
WHEN running `pytest`
THEN all test_*.py files are discovered
AND all test_* functions are executed
AND test results are reported clearly
```

### Requirement: Test fixtures must support database testing

Common test fixtures SHALL be provided for database and server testing.

#### Scenario: Temporary database fixture is available
```
GIVEN the conftest.py fixtures
WHEN a test uses the test_db fixture
THEN a temporary SQLite database is created
AND schema is initialized
AND database is cleaned up after test
AND each test gets isolated database state
```

#### Scenario: Mock API client fixture is available
```
GIVEN the conftest.py fixtures
WHEN a test uses the mock_api_client fixture
THEN HTTP requests are intercepted
AND predefined responses are returned
AND no actual API calls are made
AND test execution is fast and reliable
```

#### Scenario: MCP server fixture is available
```
GIVEN the conftest.py fixtures
WHEN a test uses the mcp_server fixture
THEN a configured FastMCP server instance is available
AND server has all tools registered
AND server can be tested without starting actual process
```

### Requirement: Test organization must mirror source structure

Test files SHALL be organized to match the source code structure.

#### Scenario: Test directory structure matches src
```
GIVEN the tests/ directory
WHEN examining test organization
THEN structure mirrors src/lorekeeper_mcp/:
  - tests/test_server.py (tests server.py)
  - tests/test_config.py (tests config.py)
  - tests/test_cache/ (tests cache module)
  - tests/test_tools/ (tests tools module)
  - tests/test_api_clients/ (tests api_clients module)
AND each test module has clear scope
```

### Requirement: Test configuration must be specified

pytest configuration SHALL be defined in pyproject.toml.

#### Scenario: pytest settings are configured
```
GIVEN the [tool.pytest.ini_options] section in pyproject.toml
WHEN examining test configuration
THEN it specifies:
  - testpaths = ["tests"]
  - python_files = ["test_*.py"]
  - python_classes = ["Test*"]
  - python_functions = ["test_*"]
  - asyncio_mode = "auto"
  - addopts for verbose output and coverage (optional)
AND configuration is applied automatically when running pytest
```

#### Scenario: Async test mode is configured
```
GIVEN pytest-asyncio is installed and configured
WHEN running async tests
THEN asyncio_mode = "auto" applies
AND async tests run without explicit markers
AND event loop is managed automatically
```

## Test Dependencies

The following testing libraries SHALL be included in dev dependencies:

- `pytest>=8.0.0` - Core testing framework
- `pytest-asyncio>=0.23.0` - Async test support
- `pytest-cov` (optional) - Coverage reporting
- `respx>=0.21.0` - Mock HTTP client for httpx testing
- `pytest-env` (optional) - Environment variable management in tests

## Example Test Structure

```python
# tests/conftest.py
import pytest
import aiosqlite
from pathlib import Path

@pytest.fixture
async def test_db():
    """Provide a temporary SQLite database for testing."""
    db_path = ":memory:"  # In-memory database
    async with aiosqlite.connect(db_path) as db:
        # Initialize schema
        await db.execute("CREATE TABLE IF NOT EXISTS api_cache (...)")
        await db.commit()
        yield db

@pytest.fixture
def mcp_server():
    """Provide a configured MCP server instance."""
    from lorekeeper_mcp.server import mcp
    return mcp
```

```python
# tests/test_cache/test_db.py
import pytest

@pytest.mark.asyncio
async def test_cache_stores_data(test_db):
    """Test that cache can store and retrieve data."""
    # Test implementation
    pass

@pytest.mark.asyncio
async def test_expired_cache_returns_none(test_db):
    """Test that expired cache entries return None."""
    # Test implementation
    pass
```
