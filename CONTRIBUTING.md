# Contributing Guidelines

This guide provides information for contributors to the LoreKeeper MCP project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Community Guidelines](#community-guidelines)

## Getting Started

### Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Git
- Basic knowledge of D&D 5e (helpful but not required)

### Initial Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/your-username/lorekeeper-mcp.git
   cd lorekeeper-mcp
   ```

2. **Set Up Development Environment**
   ```bash
   # Install dependencies
   uv sync

   # Set up pre-commit hooks
   uv run pre-commit install

   # Copy environment configuration
   cp .env.example .env
   ```

3. **Verify Setup**
   ```bash
   # Run tests to ensure everything works
   uv run pytest

   # Run the server to verify it starts
   uv run python -m lorekeeper_mcp --help
   ```

### Development Commands

```bash
# Start the server
uv run python -m lorekeeper_mcp

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=lorekeeper_mcp

# Code formatting
uv run black src/ tests/

# Linting and fixing
uv run ruff check src/ tests/ --fix

# Type checking
uv run mypy src/

# Run all quality checks
uv run pre-commit run --all-files
```

## Development Workflow

### 1. Create a Branch

```bash
# Create a feature branch from main
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b bugfix/issue-description
```

### 2. Make Changes

- Write code following the [Code Standards](#code-standards)
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Quality Checks

```bash
# Run pre-commit hooks manually
uv run pre-commit run --all-files

# Run full test suite
uv run pytest

# Check type hints
uv run mypy src/
```

### 4. Commit Changes

Use conventional commit format:

```bash
# Feature
git commit -m "feat: add new spell lookup functionality"

# Bugfix
git commit -m "fix: resolve cache TTL calculation error"

# Documentation
git commit -m "docs: update API client documentation"

# Tests
git commit -m "test: add integration tests for equipment lookup"
```

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## Code Standards

### Python Style

We follow several style guides:

- **PEP 8**: Python style guide
- **Black**: Code formatting (100 character line length)
- **Ruff**: Linting and import sorting
- **MyPy**: Static type checking

#### Code Formatting

```bash
# Format code
uv run black src/ tests/

# Sort imports and fix linting issues
uv run ruff check src/ tests/ --fix
```

#### Type Hints

All functions must have type hints:

```python
from typing import Any, Dict, List, Optional

async def lookup_spell(
    name: Optional[str] = None,
    level: Optional[int] = None,
    school: Optional[str] = None,
) -> Dict[str, Any]:
    """Look up spell information."""
    # Implementation
```

#### Documentation Strings

Use Google-style docstrings:

```python
def calculate_cache_ttl(content_type: str, default_ttl: int) -> int:
    """Calculate cache TTL based on content type.

    Args:
        content_type: Type of content being cached.
        default_ttl: Default TTL in seconds.

    Returns:
        Calculated TTL in seconds.

    Raises:
        ValueError: If content_type is not supported.
    """
    # Implementation
```

### Naming Conventions

- **Variables and functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`
- **Modules**: `lowercase_with_underscores`

### Error Handling

- Use specific exception types
- Include meaningful error messages
- Log errors appropriately
- Handle exceptions gracefully

```python
import logging

logger = logging.getLogger(__name__)

async def fetch_from_api(url: str) -> Dict[str, Any]:
    """Fetch data from API with error handling."""
    try:
        response = await http_client.get(url)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {url}: {e}")
        raise APIClientError(f"Failed to fetch data: {e}") from e
    except httpx.RequestError as e:
        logger.error(f"Request error fetching {url}: {e}")
        raise APIClientError(f"Network error: {e}") from e
```

### Async/Await Patterns

- Use `async/await` for all I/O operations
- Never use blocking calls in async functions
- Use proper async context managers

```python
# Good
async def get_cached_data(key: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT data FROM cache WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return json.loads(row[0]) if row else None

# Bad - blocking call in async function
async def get_cached_data_bad(key: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)  # Blocking!
    cursor = conn.cursor()
    # ... rest of implementation
```

## Testing Requirements

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

### Writing Tests

#### Unit Tests

Test individual functions and methods in isolation:

```python
import pytest
from lorekeeper_mcp.cache.db import get_cached, set_cached

class TestCacheOperations:
    async def test_set_and_get_cached(self, temp_db):
        """Test that cached data can be retrieved."""
        # Arrange
        key = "test:key"
        data = {"test": "data"}

        # Act
        await set_cached(key, data, "test", 3600)
        result = await get_cached(key)

        # Assert
        assert result == data

    async def test_get_expired_returns_none(self, temp_db):
        """Test that expired cache returns None."""
        # Arrange
        key = "test:expired"
        data = {"test": "data"}
        await set_cached(key, data, "test", -1)  # Already expired

        # Act
        result = await get_cached(key)

        # Assert
        assert result is None
```

#### Integration Tests

Test component interactions:

```python
class TestAPIIntegration:
    async def test_spell_lookup_with_cache(self):
        """Test spell lookup with cache integration."""
        # Test the full flow from API call to cache storage
        pass
```

#### Parameterized Tests

Use parameterization for multiple scenarios:

```python
@pytest.mark.parametrize("level,expected_count", [
    (0, 15),  # Cantrips
    (1, 30),  # 1st level spells
    (9, 5),   # 9th level spells
])
async def test_spells_by_level(level, expected_count):
    """Test spell filtering by level."""
    results = await lookup_spell(level=level)
    assert len(results) <= expected_count
```

### Test Requirements

1. **Coverage**: Maintain >90% test coverage
2. **Async Tests**: Use `pytest-asyncio` for async code
3. **Fixtures**: Use fixtures for consistent test setup
4. **Mocking**: Mock external dependencies (APIs, database)
5. **Error Cases**: Test both success and failure scenarios

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

# Run tests with specific marker
uv run pytest -m "integration"
```

## Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings and comments
2. **API Documentation**: Tool descriptions and parameters
3. **User Documentation**: README and usage guides
4. **Developer Documentation**: Architecture and development guides

### Documentation Standards

#### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
async def lookup_creature(
    name: Optional[str] = None,
    cr: Optional[float] = None,
    creature_type: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Search and retrieve creature information.

    Searches for creatures by name, challenge rating, or type.
    Returns full stat blocks for matching creatures.

    Args:
        name: Creature name or partial name to search for.
        cr: Challenge rating (supports 0.125, 0.25, 0.5, 1-30).
        creature_type: Creature type (aberration, beast, etc.).
        limit: Maximum number of results to return.

    Returns:
        List of creature stat blocks with full information.

    Raises:
        ValueError: If limit is less than 1 or greater than 100.
        APIClientError: If the external API is unavailable.

    Example:
        >>> dragons = await lookup_creature(name="dragon", cr=15)
        >>> len(dragons)
        3
    """
    # Implementation
```

#### README Updates

Update README.md when:
- Adding new tools or features
- Changing configuration options
- Updating dependencies
- Modifying installation instructions

#### Architecture Documentation

Update `docs/architecture.md` when:
- Making significant design changes
- Adding new components
- Changing data flow
- Updating performance characteristics

### Tool Documentation

Each MCP tool must have:
- Clear description of purpose
- Complete parameter documentation
- Example usage
- Error condition descriptions

```python
@mcp.tool()
async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    school: str | None = None,
    # ... other parameters
) -> str:
    """Search and retrieve spell information from Open5e v2 API.

    Finds spells by name, level, school, or other criteria.
    Returns detailed spell information including casting requirements,
    effects, and which classes can cast the spell.

    Parameters:
        name: Spell name or partial name (e.g., "fire", "magic missile")
        level: Spell level from 0-9 (0 for cantrips)
        school: Magic school (abjuration, conjuration, divination,
                enchantment, evocation, illusion, necromancy, transmutation)
        class_key: Filter by class (wizard, cleric, sorcerer, etc.)
        concentration: Only return concentration spells if True
        ritual: Only return ritual spells if True
        casting_time: Filter by casting time ("action", "bonus action", etc.)
        limit: Maximum results to return (default: 20)

    Returns:
        Formatted spell information with casting requirements,
        mechanical effects, and descriptions.

    Examples:
        - "What does Fireball do?" → name="fireball"
        - "Show me 3rd level wizard spells" → level=3, class_key="wizard"
        - "Find all evocation cantrips" → level=0, school="evocation"
    """
    # Implementation
```

## Pull Request Process

### Before Submitting

1. **Code Quality**
   ```bash
   uv run pre-commit run --all-files
   uv run pytest
   uv run mypy src/
   ```

2. **Documentation**
   - Update docstrings for new functions
   - Update README if needed
   - Add comments for complex logic

3. **Tests**
   - Add tests for new functionality
   - Ensure all tests pass
   - Maintain test coverage

### Pull Request Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Added tests for new functionality
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

### Review Process

1. **Automated Checks**
   - CI/CD pipeline runs tests
   - Code quality checks pass
   - Type checking succeeds

2. **Code Review**
   - At least one maintainer approval required
   - Focus on logic, architecture, and maintainability
   - Verify test coverage and documentation

3. **Integration**
   - Test in development environment
   - Verify no breaking changes
   - Check performance impact

### Merge Requirements

- All automated checks pass
- At least one maintainer approval
- No merge conflicts
- Documentation updated if needed
- Tests added for new functionality

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:

- Be respectful and considerate
- Use inclusive language
- Focus on constructive feedback
- Help others learn and grow

### Communication

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Pull Requests**: For code contributions

### Getting Help

- Check existing documentation
- Search existing issues and discussions
- Ask questions in GitHub Discussions
- Tag maintainers for urgent issues

### Recognition

Contributors are recognized in:
- README contributors section
- Release notes
- Commit history
- GitHub contributor statistics

Thank you for contributing to LoreKeeper MCP!
