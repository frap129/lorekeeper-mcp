# Testing Guide

This comprehensive guide covers testing practices, patterns, and tools used in the LoreKeeper MCP project.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Testing Tools](#testing-tools)
- [Writing Tests](#writing-tests)
- [Test Patterns](#test-patterns)
- [Async Testing](#async-testing)
- [Mocking and Fixtures](#mocking-and-fixtures)
- [Test Coverage](#test-coverage)
- [Running Tests](#running-tests)
- [CI/CD Integration](#cicd-integration)

## Testing Philosophy

### Principles

1. **Test-Driven Development (TDD)**: Write tests before or alongside code
2. **Comprehensive Coverage**: Test all public APIs and error conditions
3. **Fast Feedback**: Keep tests fast and reliable
4. **Clear Intent**: Tests should document expected behavior
5. **Isolation**: Tests should not depend on each other

### Test Pyramid

```
    E2E Tests (Few)
   ─────────────────
  Integration Tests (Some)
 ─────────────────────────
Unit Tests (Many)
```

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows (minimal)

## Test Structure

### Directory Layout

```
tests/
├── conftest.py              # Global fixtures and configuration
├── test_config.py           # Configuration tests
├── test_server.py          # Server tests
├── test_project_structure.py # Project structure validation
└── test_cache/             # Cache layer tests
    ├── __init__.py
    └── test_db.py         # Database operations tests
```

### File Naming

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Test Organization

```python
# Group related tests in classes
class TestCacheOperations:
    """Test cache read/write operations."""

    async def test_set_and_get_cached(self):
        """Test that cached data can be retrieved."""
        pass

    async def test_get_expired_returns_none(self):
        """Test that expired cache returns None."""
        pass

class TestCacheTTL:
    """Test cache TTL functionality."""

    async def test_ttl_enforcement(self):
        """Test that TTL is properly enforced."""
        pass
```

## Testing Tools

### Core Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",           # Test framework
    "pytest-asyncio>=0.23.0",  # Async test support
    "pytest-cov>=4.0.0",       # Coverage reporting
    "respx>=0.21.0",           # HTTP mocking
]
```

### Tool Configuration

#### pytest.ini (in pyproject.toml)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--verbose",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

## Writing Tests

### Basic Test Structure

```python
import pytest
from lorekeeper_mcp.cache.db import get_cached, set_cached

class TestCacheOperations:
    """Test cache read/write operations."""

    async def test_set_and_get_cached(self, temp_db):
        """Test that cached data can be retrieved."""
        # Arrange
        key = "test:key"
        data = {"test": "data", "number": 42}

        # Act
        await set_cached(key, data, "test", 3600)
        result = await get_cached(key)

        # Assert
        assert result == data
        assert result["test"] == "data"
        assert result["number"] == 42

    async def test_get_nonexistent_returns_none(self, temp_db):
        """Test that getting non-existent key returns None."""
        # Act
        result = await get_cached("nonexistent:key")

        # Assert
        assert result is None
```

### Parameterized Tests

Use parameterization for testing multiple scenarios:

```python
@pytest.mark.parametrize("level,expected_count", [
    (0, 15),   # Cantrips
    (1, 30),   # 1st level spells
    (3, 25),   # 3rd level spells
    (9, 5),    # 9th level spells
])
async def test_spells_by_level(level, expected_count):
    """Test spell filtering by level."""
    results = await lookup_spell(level=level)
    assert len(results) <= expected_count

    # Verify all returned spells have correct level
    for spell in results:
        assert spell["level"] == level

@pytest.mark.parametrize("content_type,ttl", [
    ("spell", 7 * 24 * 3600),
    ("monster", 7 * 24 * 3600),
    ("rule", 14 * 24 * 3600),
    ("error", 300),
])
def test_ttl_configuration(content_type, ttl):
    """Test TTL values for different content types."""
    from lorekeeper_mcp.cache.db import get_ttl_for_content_type

    assert get_ttl_for_content_type(content_type) == ttl
```

### Exception Testing

Test both success and failure scenarios:

```python
import pytest
from lorekeeper_mcp.config import Settings

class TestConfiguration:
    """Test configuration management."""

    def test_default_configuration(self):
        """Test that default configuration is valid."""
        settings = Settings()

        assert settings.db_path == Path("./data/cache.db")
        assert settings.cache_ttl_days == 7
        assert settings.error_cache_ttl_seconds == 300
        assert settings.log_level == "INFO"
        assert settings.debug is False

    def test_environment_override(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("CACHE_TTL_DAYS", "14")
        monkeypatch.setenv("DEBUG", "true")

        settings = Settings()

        assert settings.cache_ttl_days == 14
        assert settings.debug is True

    def test_invalid_configuration(self, monkeypatch):
        """Test that invalid configuration raises errors."""
        monkeypatch.setenv("CACHE_TTL_DAYS", "invalid")

        with pytest.raises(ValidationError):
            Settings()
```

## Test Patterns

### AAA Pattern (Arrange, Act, Assert)

```python
async def test_cache_expiration(self, temp_db):
    """Test that cache entries expire correctly."""
    # Arrange
    key = "test:expiration"
    data = {"test": "data"}
    short_ttl = 1  # 1 second

    # Act
    await set_cached(key, data, "test", short_ttl)

    # Should be available immediately
    result = await get_cached(key)
    assert result == data

    # Wait for expiration
    await asyncio.sleep(1.1)

    # Assert
    result = await get_cached(key)
    assert result is None
```

### Builder Pattern for Test Data

```python
class SpellBuilder:
    """Builder for creating test spell data."""

    def __init__(self):
        self.spell = {
            "name": "Test Spell",
            "level": 1,
            "school": "evocation",
            "casting_time": "1 action",
            "range": "120 feet",
            "components": ["V", "S", "M"],
            "duration": "Instantaneous",
            "description": "A test spell for testing.",
        }

    def with_name(self, name: str):
        self.spell["name"] = name
        return self

    def with_level(self, level: int):
        self.spell["level"] = level
        return self

    def with_school(self, school: str):
        self.spell["school"] = school
        return self

    def build(self):
        return self.spell.copy()

# Usage in tests
async def test_spell_filtering_by_school(self):
    """Test spell filtering by magic school."""
    # Arrange
    evocation_spell = SpellBuilder().with_name("Fireball").with_school("evocation").build()
    illusion_spell = SpellBuilder().with_name("Mirror Image").with_school("illusion").build()

    # Mock API responses
    with respx.mock:
        respx.get("https://api.open5e.com/v2/spells/").mock(
            return_value=httpx.Response(200, json={"results": [evocation_spell, illusion_spell]})
        )

        # Act
        results = await lookup_spell(school="evocation")

        # Assert
        assert len(results) == 1
        assert results[0]["school"] == "evocation"
        assert results[0]["name"] == "Fireball"
```

### Custom Assertions

Create reusable assertion helpers:

```python
class CacheAssertions:
    """Custom assertions for cache testing."""

    @staticmethod
    async def assert_cached(key: str, expected_data: dict):
        """Assert that data is cached correctly."""
        cached_data = await get_cached(key)
        assert cached_data == expected_data, f"Cached data mismatch for key: {key}"

    @staticmethod
    async def assert_not_cached(key: str):
        """Assert that data is not cached."""
        cached_data = await get_cached(key)
        assert cached_data is None, f"Unexpected cached data for key: {key}"

    @staticmethod
    async def assert_cache_expires(key: str, ttl_seconds: int):
        """Assert that cache entry expires after TTL."""
        # Set cache
        await set_cached(key, {"test": "data"}, "test", ttl_seconds)

        # Should be available
        await CacheAssertions.assert_cached(key, {"test": "data"})

        # Wait for expiration
        await asyncio.sleep(ttl_seconds + 0.1)

        # Should be expired
        await CacheAssertions.assert_not_cached(key)

# Usage in tests
async def test_cache_ttl_functionality(self, temp_db):
    """Test cache TTL functionality."""
    await CacheAssertions.assert_cache_expires("test:ttl", 2)
```

## Async Testing

### Async Test Functions

All async tests must use `async def` and be properly decorated:

```python
import pytest

@pytest.mark.asyncio
async def test_async_cache_operation(self):
    """Test async cache operation."""
    result = await get_cached("test:key")
    assert result is None
```

### Async Context Managers

Test async context managers properly:

```python
async def test_database_connection_context_manager(self):
    """Test database connection context manager."""
    db_path = ":memory:"

    async with aiosqlite.connect(db_path) as db:
        # Database is open within context
        await db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        await db.execute("INSERT INTO test (id) VALUES (1)")
        await db.commit()

        cursor = await db.execute("SELECT COUNT(*) FROM test")
        count = (await cursor.fetchone())[0]
        assert count == 1

    # Database is closed outside context
    with pytest.raises(sqlite3.ProgrammingError):
        await db.execute("SELECT 1")
```

### Async Fixtures

Create async fixtures for test setup:

```python
@pytest.fixture
async def temp_database():
    """Provide a temporary database for testing."""
    # Create temporary database
    db_path = tempfile.mktemp(suffix=".db")

    # Initialize database
    await init_db_with_path(db_path)

    yield db_path

    # Cleanup
    os.unlink(db_path)

@pytest.fixture
async def populated_cache(temp_database):
    """Provide a cache with test data."""
    test_data = [
        ("spell:fireball", {"name": "Fireball", "level": 3}, "spell", 3600),
        ("monster:goblin", {"name": "Goblin", "cr": 0.25}, "monster", 3600),
    ]

    for key, data, content_type, ttl in test_data:
        await set_cached(key, data, content_type, ttl)

    return test_data
```

## Mocking and Fixtures

### HTTP Mocking with respx

Mock external API calls:

```python
import respx
import httpx

@pytest.fixture
def mock_open5e_api():
    """Mock Open5e API responses."""
    with respx.mock:
        # Mock spell search
        respx.get("https://api.open5e.com/v2/spells/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Fireball",
                            "level": 3,
                            "school": "evocation",
                            "casting_time": "1 action",
                            "range": "150 feet",
                            "components": ["V", "S", "M"],
                            "duration": "Instantaneous",
                            "description": "A brilliant streak of flame...",
                        }
                    ]
                }
            )
        )

        # Mock monster search
        respx.get("https://api.open5e.com/v1/monsters/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "Goblin",
                            "cr": "0.25",
                            "type": "humanoid",
                            "size": "Small",
                            "hp": 7,
                            "ac": 15,
                        }
                    ]
                }
            )
        )

        yield

async def test_spell_lookup_with_mock_api(mock_open5e_api):
    """Test spell lookup with mocked API."""
    results = await lookup_spell(name="fireball")

    assert len(results) == 1
    assert results[0]["name"] == "Fireball"
    assert results[0]["level"] == 3

    # Verify API was called
    assert respx.calls.last.request.url == "https://api.open5e.com/v2/spells/?name=fireball"
```

### Database Fixtures

Create reusable database fixtures:

```python
@pytest.fixture
async def temp_db():
    """Provide a temporary database for testing."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # Override settings for test
    original_db_path = settings.db_path
    settings.db_path = Path(db_path)

    # Initialize database
    await init_db()

    yield db_path

    # Cleanup
    settings.db_path = original_db_path
    os.unlink(db_path)

@pytest.fixture
async def cache_with_data(temp_db):
    """Provide a cache with pre-populated test data."""
    test_entries = [
        ("spell:test", {"name": "Test Spell"}, "spell", 3600, "open5e"),
        ("monster:test", {"name": "Test Monster"}, "monster", 3600, "open5e"),
    ]

    for key, data, content_type, ttl, source in test_entries:
        await set_cached(key, data, content_type, ttl, source)

    return test_entries
```

### Configuration Fixtures

Test different configuration scenarios:

```python
@pytest.fixture
def test_config():
    """Provide test configuration."""
    return Settings(
        db_path=Path(":memory:"),
        cache_ttl_days=1,
        error_cache_ttl_seconds=60,
        log_level="DEBUG",
        debug=True,
    )

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("CACHE_TTL_DAYS", "30")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
```

## Test Coverage

### Coverage Requirements

- **Overall Coverage**: >90%
- **Branch Coverage**: >85%
- **Public APIs**: 100% coverage
- **Error Paths**: All error conditions tested

### Coverage Configuration

```toml
[tool.coverage.run]
source = ["src/lorekeeper_mcp"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
show_missing = true
precision = 2

[tool.coverage.html]
directory = "htmlcov"
```

### Running Coverage

```bash
# Run tests with coverage
uv run pytest --cov=lorekeeper_mcp --cov-report=html

# Generate coverage report
uv run pytest --cov=lorekeeper_mcp --cov-report=term-missing

# Coverage for specific module
uv run pytest --cov=lorekeeper_mcp.cache tests/test_cache/

# Minimum coverage threshold
uv run pytest --cov=lorekeeper_mcp --cov-fail-under=90
```

### Coverage Exclusions

Justified exclusions:

```python
def __repr__(self) -> str:  # pragma: no cover
    """String representation for debugging."""
    return f"{self.__class__.__name__}({self.id})"

if TYPE_CHECKING:  # pragma: no cover
    # Type checking imports
    from typing import Optional

if __name__ == "__main__":  # pragma: no cover
    # CLI entry point
    main()
```

## Running Tests

### Basic Commands

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_cache/test_db.py

# Run specific test class
uv run pytest tests/test_cache/test_db.py::TestCacheOperations

# Run specific test method
uv run pytest tests/test_cache/test_db.py::TestCacheOperations::test_set_and_get_cached
```

### Test Selection

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"

# Run tests by keyword
uv run pytest -k "cache"

# Run failed tests only
uv run pytest --lf

# Run tests in parallel (if pytest-xdist installed)
uv run pytest -n auto
```

### Debugging Tests

```bash
# Stop on first failure
uv run pytest -x

# Enter debugger on failure
uv run pytest --pdb

# Show local variables on failure
uv run pytest -l

# Run with maximum verbosity
uv run pytest -vv -s

# Print test collection
uv run pytest --collect-only
```

### Performance Testing

```bash
# Run tests with timing
uv run pytest --durations=10

# Profile slow tests
uv run pytest --profile

# Run with memory profiling (if pytest-memray installed)
uv run pytest --memray
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.13"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install uv
      uses: astral-sh/setup-uv@v2
      with:
        version: "latest"

    - name: Install dependencies
      run: |
        uv sync --dev

    - name: Run linting
      run: |
        uv run ruff check src/ tests/
        uv run mypy src/

    - name: Run tests
      run: |
        uv run pytest --cov=lorekeeper_mcp --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
```

### Pre-commit Integration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        pass_filenames: false
        always_run: true
        args: [--cov=lorekeeper_mcp, --cov-fail-under=90]
```

This comprehensive testing guide ensures high-quality, reliable code for the LoreKeeper MCP project.
