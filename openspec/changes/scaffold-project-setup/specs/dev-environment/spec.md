# Spec: Development Environment Setup

## ADDED Requirements

### Requirement: Python package must be configured with uv

The project SHALL use `uv` as the package manager and build tool, with all dependencies declared in `pyproject.toml`.

#### Scenario: Developer initializes development environment
```
GIVEN a fresh clone of the repository
WHEN the developer runs `uv sync`
THEN all project dependencies are installed in a virtual environment
AND the project is installed in editable mode
AND development tools (pytest, ruff) are available
```

#### Scenario: Package metadata is properly configured
```
GIVEN the pyproject.toml file
WHEN inspecting package configuration
THEN name is "lorekeeper-mcp"
AND version follows semantic versioning
AND Python version constraint is >=3.13
AND all required dependencies are declared with appropriate version constraints
```

### Requirement: FastMCP framework must be integrated

The project SHALL use FastMCP as the MCP server framework with proper server initialization.

#### Scenario: FastMCP server can be instantiated
```
GIVEN the FastMCP library is installed
WHEN importing the main server module
THEN an MCP server instance is created
AND the server is configured with appropriate settings (name, version)
AND the server is ready to accept tool registrations
```

#### Scenario: Server can be run via uv
```
GIVEN the project is installed
WHEN running `uv run python -m lorekeeper_mcp`
THEN the MCP server starts
AND listens for MCP protocol messages
AND responds to standard MCP commands (list tools, etc.)
```

### Requirement: Async HTTP client must be available

The project SHALL include httpx library for making asynchronous HTTP requests to external APIs.

#### Scenario: HTTP client can make async requests
```
GIVEN httpx is installed
WHEN importing the httpx module
THEN AsyncClient is available for use
AND supports async context manager pattern
AND can make GET/POST requests with proper error handling
```

### Requirement: Pydantic must be available for data validation

The project SHALL include Pydantic for data modeling and validation of API responses and MCP tool schemas.

#### Scenario: Pydantic models can be defined
```
GIVEN Pydantic is installed
WHEN defining data models using BaseModel
THEN models support type hints and validation
AND models can serialize to/from JSON
AND validation errors provide clear messages
```

## Dependencies Specification

### Core Dependencies
- `fastmcp` - Latest stable version for MCP server framework
- `httpx` - For async HTTP requests to D&D APIs
- `pydantic` - For data validation and modeling
- `aiosqlite>=0.20.0` - Async SQLite adapter for database caching
- `python-dotenv` - For environment variable management

### Development Dependencies
- `pytest>=8.0.0` - Testing framework
- `pytest-asyncio>=0.23.0` - Async test support
- `ruff>=0.6.0` - Linting and formatting
- `pre-commit` - Git hooks for code quality

## Configuration Requirements

### Requirement: Environment configuration must be managed

The project SHALL use environment variables for configuration with sensible defaults.

#### Scenario: Configuration is loaded from environment
```
GIVEN a .env file with database credentials
WHEN the application starts
THEN configuration values are loaded from environment
AND missing optional values use defaults
AND missing required values raise clear errors
```

#### Scenario: Development defaults are provided
```
GIVEN no .env file exists
WHEN the application starts in development mode
THEN default values are used (localhost database, development mode, etc.)
AND the application can run for local development
```
