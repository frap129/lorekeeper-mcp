# Development Guide

This guide provides comprehensive information for developers working on the LoreKeeper MCP project.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Project Architecture](#project-architecture)
- [Code Organization](#code-organization)
- [Database Cache Layer](#database-cache-layer)
- [Configuration Management](#configuration-management)
- [Testing Guidelines](#testing-guidelines)
- [Code Quality Standards](#code-quality-standards)
- [Development Workflow](#development-workflow)
- [Debugging and Troubleshooting](#debugging-and-troubleshooting)

## Development Environment Setup

### Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Git
- SQLite3 (usually included with Python)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-org/lorekeeper-mcp.git
cd lorekeeper-mcp

# Create virtual environment and install dependencies
uv sync

# Set up pre-commit hooks
uv run pre-commit install

# Copy environment configuration
cp .env.example .env

# Verify installation
uv run python -m lorekeeper_mcp --help
```

### Development Commands

```bash
# Run the server
uv run python -m lorekeeper_mcp

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=lorekeeper_mcp --cov-report=html

# Code formatting
uv run black src/ tests/

# Linting and fixing
uv run ruff check src/ tests/ --fix

# Type checking
uv run mypy src/

# Run all quality checks
uv run pre-commit run --all-files
```

## Project Architecture

### High-Level Design

LoreKeeper follows a layered architecture:

```
┌─────────────────────────────────────┐
│           FastMCP Server           │
├─────────────────────────────────────┤
│         MCP Tools Layer           │
├─────────────────────────────────────┤
│        API Client Layer           │
├─────────────────────────────────────┤
│         Cache Layer               │
├─────────────────────────────────────┤
│      Configuration Layer          │
└─────────────────────────────────────┘
```

### Key Components

1. **FastMCP Server** (`server.py`): Main MCP server with lifecycle management
2. **MCP Tools** (`tools/`): Individual tool implementations for different data types
3. **API Clients** (`api_clients/`): HTTP clients for external APIs
4. **Cache Layer** (`cache/`): SQLite-based caching with TTL support
5. **Configuration** (`config.py`): Pydantic-based settings management

### Design Principles

- **Async-First**: All I/O operations use async/await patterns
- **Type Safety**: Comprehensive type hints with MyPy validation
- **Caching Strategy**: Aggressive caching to reduce API calls and improve response times
- **Error Handling**: Graceful degradation with user-friendly error messages
- **Testability**: Dependency injection and mocking support for comprehensive testing

## Code Organization

### Package Structure

```
src/lorekeeper_mcp/
├── __init__.py              # Package initialization
├── __main__.py             # Entry point for `python -m lorekeeper_mcp`
├── config.py               # Configuration management
├── server.py               # FastMCP server setup
├── cache/                  # Database caching layer
│   ├── __init__.py
│   └── db.py              # SQLite cache implementation
├── api_clients/            # External API clients
│   └── __init__.py
└── tools/                  # MCP tool implementations
    └── __init__.py
```

### Module Responsibilities

#### `config.py`
- Pydantic settings model
- Environment variable handling
- Default configuration values
- Global settings instance

#### `server.py`
- FastMCP server initialization
- Lifecycle management (startup/shutdown)
- Tool registration
- Error handling middleware

#### `cache/db.py`
- Database schema management
- Cache operations (get, set, cleanup)
- TTL enforcement
- Connection management with WAL mode

#### `api_clients/`
- HTTP client implementations
- API-specific request/response handling
- Error handling and retry logic
- Response normalization

#### `tools/`
- MCP tool implementations
- Parameter validation
- Response formatting
- Cache integration

## Database Cache Layer

### Schema Design

```sql
CREATE TABLE api_cache (
    cache_key TEXT PRIMARY KEY,
    response_data TEXT NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    content_type TEXT NOT NULL,
    source_api TEXT NOT NULL
);
```

### Cache Operations

#### Retrieval
```python
async def get_cached(key: str) -> dict[str, Any] | None:
    """Retrieve cached data if not expired."""
    # Checks expiration and returns parsed JSON
```

#### Storage
```python
async def set_cached(
    key: str,
    data: dict[str, Any],
    content_type: str,
    ttl_seconds: int,
    source_api: str = "unknown",
) -> None:
    """Store data in cache with TTL."""
    # Serializes data and stores with expiration
```

#### Cleanup
```python
async def cleanup_expired() -> int:
    """Remove expired cache entries."""
    # Returns count of deleted entries
```

### Cache Keys

Cache keys follow the pattern: `{api}:{endpoint}:{params_hash}`

Examples:
- `open5e:v2/spells:name=fireball`
- `open5e:v1/monsters:cr=5,type=undead`
- `dnd5e:rules:section=combat`

### Performance Optimizations

- **WAL Mode**: Enables concurrent reads/writes
- **Indexes**: Optimized for expiration and content type queries
- **Connection Pooling**: Reuses database connections
- **Batch Operations**: Minimizes transaction overhead

## Configuration Management

### Settings Model

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    db_path: Path = Field(default=Path("./data/cache.db"))
    cache_ttl_days: int = Field(default=7)
    error_cache_ttl_seconds: int = Field(default=300)
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    open5e_base_url: str = Field(default="https://api.open5e.com")
    dnd5e_base_url: str = Field(default="https://www.dnd5eapi.co/api")
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_PATH` | SQLite database file path | `./data/cache.db` |
| `CACHE_TTL_DAYS` | Normal cache TTL in days | `7` |
| `ERROR_CACHE_TTL_SECONDS` | Error cache TTL in seconds | `300` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEBUG` | Enable debug mode | `false` |
| `OPEN5E_BASE_URL` | Open5e API base URL | `https://api.open5e.com` |
| `DND5E_BASE_URL` | D&D 5e API base URL | `https://www.dnd5eapi.co/api` |

### Configuration Validation

- Pydantic provides automatic type validation
- Path validation ensures database directory exists
- URL validation for API endpoints
- Range validation for TTL values

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_config.py           # Configuration tests
├── test_server.py          # Server tests
└── test_cache/             # Cache layer tests
    ├── __init__.py
    └── test_db.py         # Database operations tests
```

### Testing Standards

#### Test Organization
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **Async Tests**: Use `pytest-asyncio` for async code
- **Fixtures**: Use fixtures for consistent test setup

#### Test Naming
- Use descriptive test names: `test_function_name_expected_behavior`
- Group related tests in classes
- Use parameterized tests for multiple scenarios

#### Example Test Structure

```python
import pytest
from lorekeeper_mcp.cache.db import get_cached, set_cached

class TestCacheOperations:
    async def test_set_and_get_cached(self):
        """Test that cached data can be retrieved."""
        # Arrange
        key = "test:key"
        data = {"test": "data"}

        # Act
        await set_cached(key, data, "test", 3600)
        result = await get_cached(key)

        # Assert
        assert result == data

    @pytest.mark.parametrize("ttl_seconds,expected_result", [
        (3600, {"test": "data"}),  # Valid cache
        (-1, None),               # Expired cache
    ])
    async def test_cache_ttl(self, ttl_seconds, expected_result):
        """Test cache TTL enforcement."""
        # Implementation...
```

### Test Fixtures

#### Database Fixture
```python
@pytest.fixture
async def temp_db():
    """Provide a temporary database for testing."""
    # Creates temporary database
    # Yields database path
    # Cleans up after test
```

#### Configuration Fixture
```python
@pytest.fixture
def test_config():
    """Provide test configuration."""
    # Returns Settings with test values
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=lorekeeper_mcp --cov-report=html

# Run specific test file
uv run pytest tests/test_cache/test_db.py

# Run with verbose output
uv run pytest -v

# Run only failed tests
uv run pytest --lf
```

### Coverage Requirements

- Maintain >90% test coverage
- All public APIs must have tests
- All error conditions must be tested
- Async code must be tested with proper await patterns

## Code Quality Standards

### Formatting

- **Black**: Code formatting with 100-character line length
- **Ruff**: Import sorting and additional formatting rules

```bash
uv run black src/ tests/
uv run ruff format src/ tests/
```

### Linting

Ruff configuration includes:
- **pycodestyle** (E, W): Style guide enforcement
- **pyflakes** (F): Error detection
- **isort** (I): Import sorting
- **pep8-naming** (N): Naming conventions
- **pyupgrade** (UP): Python version upgrades
- **flake8-bugbear** (B): Common pitfalls
- **flake8-comprehensions** (C4): Comprehension best practices
- **Ruff-specific** (RUF): Additional rules

```bash
uv run ruff check src/ tests/ --fix
```

### Type Checking

MyPy configuration:
- Strict type checking enabled
- Disallows untyped definitions
- Requires explicit return types
- Warns about unused code

```bash
uv run mypy src/
```

### Pre-commit Hooks

Automated checks run on every commit:
- Trailing whitespace removal
- End-of-file fixer
- YAML validation
- Large file detection
- Merge conflict detection
- Debug statement detection
- Black formatting
- Ruff linting and formatting
- MyPy type checking

## Development Workflow

### Git Workflow

1. **Branch Strategy**: Use feature branches from `main`
2. **Commit Messages**: Use conventional commit format
3. **Pull Requests**: Require review and passing checks
4. **Merge Strategy**: Squash merge with clean commit history

### Feature Development

1. **Setup**: Create feature branch
2. **Development**: Write code and tests
3. **Quality**: Run pre-commit checks
4. **Testing**: Ensure all tests pass
5. **Documentation**: Update relevant docs
6. **PR**: Create pull request with description

### Release Process

1. **Version**: Update version in `pyproject.toml`
2. **Changelog**: Update CHANGELOG.md
3. **Tag**: Create git tag
4. **Build**: Build package with `uv build`
5. **Publish**: Publish to package repository

## Debugging and Troubleshooting

### Debug Mode

Enable debug mode for detailed logging:

```bash
DEBUG=true uv run python -m lorekeeper_mcp
```

### Common Issues

#### Database Connection Issues
- Check database path permissions
- Ensure parent directory exists
- Verify SQLite installation

#### Cache Issues
- Check TTL settings
- Verify database schema
- Run cleanup manually

#### API Issues
- Check network connectivity
- Verify API endpoints
- Check rate limits

### Logging

Configure logging level via environment:

```bash
LOG_LEVEL=DEBUG uv run python -m lorekeeper_mcp
```

Log levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages only

### Performance Monitoring

Monitor cache performance:
- Cache hit rates
- Database query times
- API response times
- Memory usage

### Development Tips

1. **Use Async Patterns**: Always use `async/await` for I/O operations
2. **Type Hints**: Provide comprehensive type hints
3. **Error Handling**: Handle exceptions gracefully
4. **Testing**: Write tests before or alongside code
5. **Documentation**: Update docs when changing functionality
6. **Code Review**: Participate in code reviews for quality
