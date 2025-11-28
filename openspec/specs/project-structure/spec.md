# project-structure Specification

## Purpose
Defines the project directory structure and module organization for LoreKeeper MCP, including source code layout (tools, cache, api_clients, models, parsers, repositories), test organization, configuration management, and package metadata in pyproject.toml with proper entry points.
## Requirements
### Requirement: Source code must be organized in logical modules

The project SHALL organize Python code into a clear module hierarchy that separates concerns.

#### Scenario: Core modules exist with proper structure
```
GIVEN the project repository
WHEN examining the src/lorekeeper_mcp directory
THEN the following module structure exists:
  - src/lorekeeper_mcp/__init__.py (package initialization)
  - src/lorekeeper_mcp/__main__.py (CLI entry point)
  - src/lorekeeper_mcp/server.py (FastMCP server instance)
  - src/lorekeeper_mcp/config.py (configuration and settings)
  - src/lorekeeper_mcp/tools/ (MCP tool implementations)
  - src/lorekeeper_mcp/cache/ (database caching layer)
  - src/lorekeeper_mcp/api_clients/ (HTTP clients for external APIs)
AND each directory has an __init__.py file
```

#### Scenario: Module can be run as a script
```
GIVEN the installed package
WHEN running `python -m lorekeeper_mcp`
THEN the __main__.py module executes
AND the FastMCP server starts
AND listens for MCP protocol connections
```

### Requirement: Configuration must be centralized

All application configuration SHALL be managed through a central config module.

#### Scenario: Configuration loads from environment
```
GIVEN environment variables or .env file
WHEN the config module is imported
THEN configuration values are loaded
AND typed settings are available as Python objects
AND missing required values raise ConfigurationError
```

#### Scenario: Default configuration supports development
```
GIVEN no environment variables are set
WHEN the application starts
THEN sensible defaults are used:
  - DB_PATH=./data/cache.db
  - CACHE_TTL_DAYS=7
  - LOG_LEVEL=INFO
  - DEBUG=False
AND the application can run immediately
```

### Requirement: Data directory must be gitignored

The project SHALL exclude runtime data files from version control.

#### Scenario: Generated files are ignored
```
GIVEN the .gitignore file
WHEN committing changes
THEN the following are excluded:
  - data/ (SQLite database directory)
  - *.db (SQLite database files)
  - .env (environment configuration)
  - __pycache__/ (Python bytecode)
  - *.pyc (compiled Python)
  - .pytest_cache/ (test cache)
  - .ruff_cache/ (linter cache)
  - dist/ (build artifacts)
  - *.egg-info/ (package metadata)
```

### Requirement: Project metadata must be complete

The pyproject.toml SHALL contain all required package metadata.

#### Scenario: Package information is specified
```
GIVEN the pyproject.toml file
WHEN examining the [project] section
THEN it contains:
  - name = "lorekeeper-mcp"
  - version (semantic versioning)
  - description
  - readme = "README.md"
  - requires-python = ">=3.13"
  - license = {text = "MIT"}
  - authors with name and email
  - keywords for discoverability
  - classifiers for PyPI
```

#### Scenario: Entry points are defined
```
GIVEN the pyproject.toml file
WHEN examining [project.scripts]
THEN console_scripts includes:
  - lorekeeper-mcp command pointing to main entry point
AND allows running via `lorekeeper-mcp` command after installation
```

## Directory Structure

```
lorekeeper-mcp/
├── .git/
├── .github/                    # GitHub-specific files (future)
├── .gitignore
├── .python-version            # Python 3.13
├── pyproject.toml             # Project configuration and dependencies
├── README.md                  # Project documentation
├── .env.example               # Example environment configuration
├── data/                      # Runtime data (gitignored)
│   └── cache.db              # SQLite database (created at runtime)
├── docs/                      # Documentation
│   └── tools.md              # MCP tools specification
├── openspec/                  # OpenSpec change management
│   ├── project.md
│   ├── changes/
│   └── specs/
├── src/
│   └── lorekeeper_mcp/
│       ├── __init__.py
│       ├── __main__.py       # Entry point for python -m lorekeeper_mcp
│       ├── server.py         # FastMCP server setup
│       ├── config.py         # Configuration management
│       ├── tools/            # MCP tool implementations
│       │   └── __init__.py
│       ├── cache/            # Database caching layer
│       │   ├── __init__.py
│       │   └── db.py        # SQLite operations
│       └── api_clients/      # External API clients
│           └── __init__.py
└── tests/                     # Test suite
    ├── __init__.py
    ├── conftest.py           # Pytest configuration and fixtures
    ├── test_server.py
    ├── test_cache.py
    └── test_tools/
        └── __init__.py
```
