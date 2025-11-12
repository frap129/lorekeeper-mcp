# Agent Guidelines for LoreKeeper MCP

## Commands

- **Run all tests**: `just test`
- **Run single test file**: `uv run pytest tests/test_cache/test_db.py`
- **Run single test**: `uv run pytest tests/test_cache/test_db.py::test_function_name`
- **Lint**: `just lint`
- **Format**: `just format`
- **Type check**: `just type-check`
- **All quality checks**: `just check`

## Code Style

- **Line length**: 100 characters max
- **Python version**: 3.11+
- **Type hints**: Required on all functions (strict mypy). Use `dict[str, Any]`, `list[Type]`, `Type | None` (no `Optional`)
- **Imports**: Standard library → third-party → local (ruff handles sorting)
- **Quotes**: Double quotes
- **Indentation**: 4 spaces
- **Async**: Use `async def` for all I/O operations; tests use `@pytest.mark.asyncio` or rely on `asyncio_mode = "auto"`

## Conventions

- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants
- **Docstrings**: Google style with Args, Returns, Raises sections on public functions
- **Error handling**: Use custom exceptions (`ApiError`, `NetworkError`), log warnings for non-fatal errors
- **Logging**: `logger = logging.getLogger(__name__)` at module level, use `logger.debug/info/warning/error`
- **Testing**: Fixtures in `conftest.py`, use `respx.mock` for HTTP mocking, prefer async fixtures with `yield`

# Rules

1. The most important kind of test is a live test. Live tests must ALWAYS pass. Never commit if there is a failing live test.
2. The tests are right. Unless there is a major refactor that breaks some tests, a failing test usually indicates a bad implementation, not a bad test.
