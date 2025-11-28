# LoreKeeper MCP

A Model Context Protocol (MCP) server for D&D 5e information lookup with AI assistants. LoreKeeper provides fast, cached access to comprehensive Dungeons & Dragons 5th Edition data through the Open5e API.

## Features

- **Comprehensive D&D 5e Data**: Access spells, monsters, classes, races, equipment, and rules
- **Intelligent Caching**: SQLite-based caching with TTL support for fast responses
- **Open5e API Integration**: Access to comprehensive D&D 5e content via Open5e API
- **Type-Safe Configuration**: Pydantic-based configuration management
- **Modern Python Stack**: Built with Python 3.13+, async/await patterns, and FastMCP
- **Production Ready**: Comprehensive test suite, code quality tools, and pre-commit hooks

## Quick Start

### Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) for package management

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/lorekeeper-mcp.git
cd lorekeeper-mcp

# Install dependencies
uv sync

# Set up pre-commit hooks
uv run pre-commit install

# Copy environment configuration
cp .env.example .env
```

### Running the Server

```bash
# Start the MCP server (recommended)
lorekeeper serve

# Or with custom configuration
lorekeeper -v serve
lorekeeper --db-path /custom/path.db serve

# Backward compatible: start server without CLI
uv run python -m lorekeeper_mcp
```

## Available Tools

LoreKeeper provides 5 MCP tools for querying D&D 5e game data:

1. **`lookup_spell`** - Search spells by name, level, school, class, and properties
2. **`lookup_creature`** - Find monsters by name, CR, type, and size
3. **`lookup_character_option`** - Get classes, races, backgrounds, and feats
4. **`lookup_equipment`** - Search weapons, armor, and magic items
5. **`lookup_rule`** - Look up game rules, conditions, and reference information

See [docs/tools.md](docs/tools.md) for detailed usage and examples.

### Document Filtering

All lookup tools and the search tool support filtering by source document:

```python
# List available documents first
documents = await list_documents()

# Filter spells to SRD only
srd_spells = await lookup_spell(
    level=3,
    documents=["srd-5e"]
)

# Filter creatures from multiple sources
creatures = await lookup_creature(
    type="dragon",
    documents=["srd-5e", "tce", "phb"]
)

# Search with document filter
results = await search_dnd_content(
    query="fireball",
    documents=["srd-5e"]
)
```

This allows you to:
- Limit searches to SRD (free) content only
- Filter by specific published books or supplements
- Separate homebrew from official content
- Control which sources you're using for licensing reasons

See [docs/document-filtering.md](docs/document-filtering.md) for comprehensive guide and cross-source filtering examples.

## CLI Usage

LoreKeeper includes a command-line interface for importing D&D content:

```bash
# Import content from OrcBrew file
lorekeeper import MegaPak_-_WotC_Books.orcbrew

# Show help
lorekeeper --help
lorekeeper import --help
```

See [docs/cli-usage.md](docs/cli-usage.md) for detailed CLI documentation.

## Configuration

LoreKeeper uses environment variables for configuration. All settings use the `LOREKEEPER_` prefix. Create a `.env` file:

```bash
# Cache backend settings
LOREKEEPER_CACHE_BACKEND=milvus        # "milvus" (default) or "sqlite"
LOREKEEPER_MILVUS_DB_PATH=~/.lorekeeper/milvus.db
LOREKEEPER_EMBEDDING_MODEL=all-MiniLM-L6-v2

# SQLite settings (if using sqlite backend)
LOREKEEPER_DB_PATH=./data/cache.db

# Cache TTL settings
LOREKEEPER_CACHE_TTL_DAYS=7
LOREKEEPER_ERROR_CACHE_TTL_SECONDS=300

# Logging
LOREKEEPER_LOG_LEVEL=INFO
LOREKEEPER_DEBUG=false

# API endpoints
LOREKEEPER_OPEN5E_BASE_URL=https://api.open5e.com
```

## Semantic Search

LoreKeeper uses **Milvus Lite** as the default cache backend, providing semantic search capabilities powered by vector embeddings.

### Features

- **Semantic Search**: Find content by meaning, not just exact text matches
- **Vector Embeddings**: Uses sentence-transformers for high-quality text embeddings
- **Zero Configuration**: Works out of the box with sensible defaults
- **Lightweight**: Embedded database, no external services required

### First-Run Setup

On first run, LoreKeeper downloads the embedding model (~80MB). This is a one-time download:

```bash
# First run will show:
# Downloading model 'all-MiniLM-L6-v2'...
lorekeeper serve
```

### Configuration

Configure Milvus via environment variables:

```bash
# Use Milvus backend (default)
LOREKEEPER_CACHE_BACKEND=milvus

# Custom database path
LOREKEEPER_MILVUS_DB_PATH=/path/to/milvus.db

# Alternative embedding model
LOREKEEPER_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Migrating from SQLite

If you were using an older version with SQLite caching, set the backend for backward compatibility:

```bash
# Keep using SQLite
LOREKEEPER_CACHE_BACKEND=sqlite
LOREKEEPER_DB_PATH=./data/cache.db
```

Note: SQLite cache does not support semantic search—only exact and pattern matching.

## Development

### Project Structure

```
lorekeeper-mcp/
├── src/lorekeeper_mcp/          # Main package
│   ├── cache/                   # Database caching layer
│   │   └── db.py               # SQLite cache implementation
│   ├── api_clients/            # External API clients
│   ├── tools/                  # MCP tool implementations
│   ├── config.py               # Configuration management
│   ├── server.py               # FastMCP server setup
│   └── __main__.py            # Package entry point
├── tests/                      # Test suite
│   ├── test_cache/            # Cache layer tests
│   ├── test_config.py         # Configuration tests
│   ├── test_server.py         # Server tests
│   └── conftest.py            # Pytest fixtures
├── docs/                       # Documentation
├── pyproject.toml             # Project configuration
├── .pre-commit-config.yaml    # Code quality hooks
└── README.md                  # This file
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=lorekeeper_mcp

# Run specific test file
uv run pytest tests/test_cache/test_db.py
```

### Code Quality

The project uses several code quality tools:

- **Black**: Code formatting (100 character line length)
- **Ruff**: Linting and import sorting
- **MyPy**: Static type checking
- **Pre-commit**: Git hooks for automated checks

```bash
# Run all quality checks
uv run ruff check src/
uv run ruff format src/
uv run mypy src/

# Run pre-commit hooks manually
uv run pre-commit run --all-files
```

### Database Cache

LoreKeeper uses SQLite with WAL mode for efficient caching:

- **Schema**: `api_cache` table with indexes on expiration and content type
- **TTL Support**: Configurable cache duration (default: 7 days)
- **Content Types**: Spells, monsters, equipment, etc. for organized storage
- **Source Tracking**: Records which API provided cached data
- **Automatic Cleanup**: Expired entries are automatically pruned

### API Strategy

The project follows a strategic API assignment:

1. **Use Open5e API** for all content lookups
2. **Prefer Open5e v2** over v1 when available
3. **Unified source**: Single API ensures consistent behavior and simplified maintenance

See [docs/tools.md](docs/tools.md) for detailed API mapping and implementation notes.

## 📋 OpenSpec Integration

This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) as its core development tooling for specification management and change tracking. OpenSpec provides:

- **Structured Specifications**: All features, APIs, and architectural changes are documented in detailed specs
- **Change Management**: Comprehensive change tracking with proposals, designs, and implementation tasks
- **Living Documentation**: Specifications evolve alongside the codebase, ensuring documentation stays current
- **Development Workflow**: Integration between specs, implementation, and testing

The `openspec/` directory contains:
- Current specifications for all project components
- Historical change records with full context
- Design documents and implementation plans
- Task breakdowns for development work

When contributing, please review relevant specifications in `openspec/` and follow the established change management process.

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and ensure tests pass
4. Run code quality checks: `uv run pre-commit run --all-files`
5. Commit your changes
6. Push to your fork and create a pull request

### Testing

All contributions must include tests:

- New features should have corresponding unit tests
- Maintain test coverage above 90%
- Use pytest fixtures for consistent test setup
- Follow async/await patterns for async code

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Open5e](https://open5e.com/) for comprehensive D&D 5e API
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP server framework
