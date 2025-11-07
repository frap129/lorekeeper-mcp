# Agent Guidelines for LoreKeeper MCP

## Commands
- **Run all tests**: `uv run pytest`
- **Run single test file**: `uv run pytest tests/test_cache/test_db.py`
- **Run single test**: `uv run pytest tests/test_cache/test_db.py::test_function_name`
- **Lint**: `uv run ruff check src/ tests/`
- **Format**: `uv run ruff format src/ tests/` or `uv run black src/ tests/`
- **Type check**: `uv run mypy src/`
- **All quality checks**: `uv run pre-commit run --all-files`

## Code Style
- **Line length**: 100 characters max
- **Python version**: 3.13+
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
