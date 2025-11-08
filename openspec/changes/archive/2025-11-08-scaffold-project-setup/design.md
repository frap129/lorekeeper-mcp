# Design: Scaffold Project Setup

## Architectural Overview

This change establishes the foundational architecture for the LoreKeeper MCP server, implementing a three-layer design:

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Protocol Layer                        │
│              (FastMCP Server Framework)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Tool Registrations
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Business Logic Layer                       │
│        (Tool Implementations: spells, creatures, etc.)       │
└────────┬─────────────────────────┬──────────────────────────┘
         │                         │
         │ API Requests            │ Cache Queries
         │                         │
┌────────▼─────────────┐   ┌──────▼──────────────────────────┐
│  External APIs       │   │    Cache Layer (SQLite)          │
│  - Open5e API        │   │  - aiosqlite (async operations)  │
│  - D&D 5e API        │   │  - 7-day TTL for game data       │
└──────────────────────┘   └──────────────────────────────────┘
```

## Component Design

### 1. Configuration Management (config.py)

**Purpose**: Centralize all application settings with environment variable support.

**Design Pattern**: Settings Object pattern using Pydantic

**Key Design Decisions**:
- Use Pydantic's BaseSettings for automatic environment variable loading
- Provide sensible defaults for local development (no .env required)
- Type-safe configuration access throughout application
- Fail fast with clear errors if required config is missing

**Implementation**:
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Database
    db_path: Path = Path("./data/cache.db")

    # Cache configuration
    cache_ttl_days: int = 7
    error_cache_ttl_seconds: int = 300

    # Logging
    log_level: str = "INFO"
    debug: bool = False

    # API configuration (for future use)
    open5e_base_url: str = "https://api.open5e.com"
    dnd5e_base_url: str = "https://www.dnd5eapi.co/api"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 2. Database Cache Layer (cache/db.py)

**Purpose**: Provide async caching of API responses to minimize external API calls.

**Design Pattern**: Cache-Aside pattern with TTL-based expiration

**Key Design Decisions**:
- SQLite over PostgreSQL for simplicity and zero-configuration
- Async operations using aiosqlite to prevent blocking MCP server
- URL-based cache keys for transparent caching
- Separate TTLs for successful responses (7 days) vs errors (5 minutes)
- Background cleanup of expired entries
- Content-type tagging for selective cache invalidation

**Schema Design**:
```sql
CREATE TABLE api_cache (
    cache_key TEXT PRIMARY KEY,      -- URL or composite key
    response_data TEXT NOT NULL,     -- JSON serialized response
    created_at REAL NOT NULL,        -- Unix timestamp
    expires_at REAL NOT NULL,        -- Unix timestamp for TTL
    content_type TEXT NOT NULL,      -- spell, monster, class, etc.
    source_api TEXT NOT NULL         -- open5e-v1, open5e-v2, dnd5e
);

CREATE INDEX idx_expires_at ON api_cache(expires_at);
CREATE INDEX idx_content_type ON api_cache(content_type);
```

**API Design**:
```python
async def init_db() -> None:
    """Initialize database schema."""

async def get_cached(key: str) -> dict | None:
    """Retrieve cached data if not expired."""

async def set_cached(
    key: str,
    data: dict,
    content_type: str,
    ttl_seconds: int
) -> None:
    """Store data in cache with TTL."""

async def cleanup_expired() -> int:
    """Remove expired cache entries, return count deleted."""

async def clear_cache(content_type: str | None = None) -> int:
    """Clear all cache or specific content type."""
```

**Concurrency Considerations**:
- SQLite Write-Ahead Logging (WAL) mode for better concurrent access
- Connection pooling via aiosqlite
- Read-heavy workload (cache hits) performs well
- Writes (cache misses) are infrequent and acceptable to serialize

### 3. FastMCP Server (server.py, __main__.py)

**Purpose**: Initialize and configure the MCP protocol server.

**Design Pattern**: Factory pattern for server creation

**Key Design Decisions**:
- Single server instance created at module level
- Tools registered declaratively using FastMCP decorators
- Graceful startup/shutdown with database initialization
- Proper async context management

**Implementation**:
```python
# server.py
from fastmcp import FastMCP
from .config import settings

mcp = FastMCP(
    name="lorekeeper-mcp",
    version="0.1.0",
    description="D&D 5e information server for AI assistants"
)

@mcp.lifespan()
async def lifespan():
    """Initialize resources on startup, cleanup on shutdown."""
    from .cache.db import init_db
    await init_db()
    yield
    # Cleanup if needed

# Tools will be registered here in future tasks
```

```python
# __main__.py
from .server import mcp

if __name__ == "__main__":
    mcp.run()
```

### 4. Project Structure

**Design Principle**: Separation of concerns with clear module boundaries

**Module Organization**:
- `config.py` - Pure configuration, no business logic
- `cache/` - Database operations only, no API knowledge
- `api_clients/` - HTTP client code, no cache knowledge (future)
- `tools/` - MCP tool implementations, orchestrates cache + API (future)
- `server.py` - Server setup and tool registration only

**Benefits**:
- Easy to test each module in isolation
- Clear dependencies (config → cache → api_clients → tools → server)
- Future refactoring is localized
- Modules can be developed in parallel

## Technology Choices

### SQLite vs PostgreSQL

**Decision**: Use SQLite instead of PostgreSQL

**Rationale**:
- **Zero Configuration**: No database server to install/manage
- **Portability**: Database is a single file, easy to backup/move
- **Sufficient Performance**: Read-heavy caching workload suits SQLite
- **Development Velocity**: Developers can start immediately
- **Appropriate Scale**: MCP server is single-user, not web-scale

**Trade-offs Accepted**:
- Limited concurrent writes (acceptable for cache-aside pattern)
- No advanced PostgreSQL features (not needed for caching)
- File-based rather than client-server (fine for local MCP server)

### aiosqlite vs sqlite3

**Decision**: Use aiosqlite for async operations

**Rationale**:
- FastMCP is async-based, blocking operations would stall server
- aiosqlite provides async/await interface over sqlite3
- Prevents blocking event loop during database I/O
- Essential for responsive MCP server

### uv vs pip/poetry

**Decision**: Use uv as package manager (per project.md)

**Rationale**:
- **Speed**: Rust-based, significantly faster than pip/poetry
- **Modern**: Built for modern Python workflows
- **Integrated**: Combines package management + formatting
- **Project Requirement**: Specified in project conventions

### ruff vs flake8/black/isort

**Decision**: Use ruff for linting and formatting (per project.md)

**Rationale**:
- **Speed**: 10-100x faster than traditional tools
- **Unified**: Replaces flake8, black, isort, pyupgrade
- **Modern**: Active development, Python 3.13 support
- **Project Requirement**: Specified in project conventions

## Testing Strategy

### Async Testing Approach

**Challenge**: Testing async code requires async test framework

**Solution**: pytest-asyncio with "auto" mode
- Automatically detects async test functions
- Manages event loop lifecycle
- Supports async fixtures

### Database Testing

**Approach**: In-memory SQLite databases per test

**Benefits**:
- Extremely fast (no disk I/O)
- Isolated (each test gets fresh database)
- No cleanup needed (database destroyed after test)

**Implementation**:
```python
@pytest.fixture
async def test_db():
    """Provide in-memory database for testing."""
    from lorekeeper_mcp.cache.db import init_db

    # Use in-memory database
    original_path = settings.db_path
    settings.db_path = ":memory:"

    await init_db()
    yield

    settings.db_path = original_path
```

### API Testing Strategy (Future)

**Approach**: Mock HTTP requests using respx

**Rationale**:
- No actual API calls in tests (fast, reliable)
- Control responses for edge cases
- Test error handling thoroughly
- Works with httpx (our HTTP client)

## Configuration Management

### Environment Variables

**Pattern**: Hierarchical configuration with defaults

**Precedence** (highest to lowest):
1. Environment variables (production)
2. .env file (local development)
3. Default values (fallback)

**Benefits**:
- Development works out-of-box (no .env required)
- Production can override via environment
- Secrets never in version control
- Clear documentation via .env.example

## Error Handling Strategy

### Database Errors

**Approach**: Fail fast on initialization, graceful degradation during operation

- Database initialization failures → crash with clear error
- Cache read failures → log warning, proceed without cache (treat as cache miss)
- Cache write failures → log error, continue (don't block API response)

### API Errors (Future)

**Approach**: Cache errors with short TTL

- Failed API requests cached for 5 minutes
- Prevents hammering failing endpoints
- Still retries after reasonable interval

## Performance Considerations

### Caching Strategy

**TTL Selection**:
- **7 days for game content**: D&D rules rarely change
- **5 minutes for errors**: Allow quick recovery from transient failures

**Cache Key Design**:
- Use full URL as key for simplicity
- Includes query parameters for filtering
- Unique per request, maximizes cache hits

### Async Performance

**Design Principles**:
- Never block event loop with synchronous I/O
- Use aiosqlite for database operations
- Use httpx AsyncClient for API requests (future)
- FastMCP handles concurrency automatically

## Security Considerations

### Data Storage

- No sensitive user data stored
- Only public API responses cached
- SQLite file has standard filesystem permissions
- No authentication/authorization needed (MCP protocol handles this)

### API Keys (Future)

- If APIs require keys, load from environment only
- Never log or cache API keys
- Document in .env.example

## Future Extensibility

### Easy to Add

- New MCP tools (register with decorator)
- New API endpoints (add to api_clients/)
- Cache invalidation strategies (clear_cache() exists)
- Metrics/monitoring (add middleware to FastMCP)

### Migration Paths

If requirements change:
- SQLite → PostgreSQL: Change aiosqlite to asyncpg, same interface
- Single API → Multiple APIs: Already separated in api_clients/
- Local → Remote deployment: Configuration already externalized

## Development Workflow

### Getting Started

```bash
# Clone and setup
git clone <repo>
cd lorekeeper-mcp
uv sync

# Run server
uv run python -m lorekeeper_mcp

# Run tests
uv run pytest

# Check code quality
uv run ruff check .
uv run ruff format --check .
```

### Pre-commit Workflow

```bash
# Install hooks once
pre-commit install

# Hooks run automatically on commit
git commit -m "feat: add new feature"

# Or run manually
pre-commit run --all-files
```

## Open Questions & Future Work

### Questions for Later

1. **API Rate Limits**: What are actual rate limits for Open5e and D&D 5e APIs?
   - May need to implement rate limiting
   - May need exponential backoff

2. **Cache Size Management**: Should we limit cache size?
   - Currently grows unbounded
   - Could add LRU eviction or size limits

3. **Cache Warming**: Should we pre-populate cache with common queries?
   - Could improve first-request latency
   - Requires understanding usage patterns

### Future Enhancements

- Cache statistics and monitoring
- Database migrations framework (if schema evolves)
- Health check endpoint
- Structured logging (JSON logs for production)
- OpenTelemetry instrumentation
- Docker containerization
