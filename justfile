# Justfile for lorekeeper-mcp

# Default task to run when no recipe is specified
default:
    @echo "Available tasks:"
    @just --list

# Run all tests
test:
    @uv run pytest

# Lint the codebase
lint:
    @uv run ruff check src/ tests/

# Format the codebase with ruff and black
format:
    @uv run ruff format src/ tests/
    @uv run black src/ tests/

# Type check the codebase
type-check:
    @uv run mypy src/

# Run all pre-commit hooks
pre-commit:
    @uv run pre-commit run --all-files

# Run all quality checks
check: lint type-check

# Run the Model Context Protocol inspector
inspect:
    #!/usr/bin/env bash
    if command -v bun >/dev/null 2>&1; then
        echo "Using bunx to run MCP inspector..."
        bunx -y @modelcontextprotocol/inspector uv run src/lorekeeper_mcp/
    else
        echo "Using npx to run MCP inspector..."
        npx -y @modelcontextprotocol/inspector uv run src/lorekeeper_mcp/
    fi
