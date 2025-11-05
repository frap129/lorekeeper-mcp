"""Pytest configuration and fixtures for lorekeeper-mcp testing."""

import pytest

from lorekeeper_mcp.cache.db import init_db
from lorekeeper_mcp.config import settings
from lorekeeper_mcp.server import mcp


@pytest.fixture
async def test_db(tmp_path, monkeypatch):
    """Provide a temporary database for testing.

    This fixture:
    - Creates a temporary database file
    - Initializes the schema
    - Uses monkeypatch to modify settings.db_path
    - Cleans up after the test
    """
    # Create temporary database file
    db_file = tmp_path / "test_cache.db"

    # Patch settings to use temporary database
    monkeypatch.setattr(settings, "db_path", db_file)

    # Initialize database schema
    await init_db()

    yield db_file


@pytest.fixture
def mcp_server():
    """Provide a configured MCP server instance for testing.

    Returns the mcp instance from lorekeeper_mcp.server.
    """
    return mcp
