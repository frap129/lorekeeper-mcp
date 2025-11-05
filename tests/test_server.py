"""Tests for FastMCP server initialization."""

import pytest


def test_server_instance_exists():
    """Test that server instance is created with correct name."""
    from lorekeeper_mcp.server import mcp

    assert mcp is not None
    assert mcp.name == "lorekeeper-mcp"


def test_server_exports_from_package():
    """Test that server is exported from package."""
    from lorekeeper_mcp import mcp

    assert mcp is not None
