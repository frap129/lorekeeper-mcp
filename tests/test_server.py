"""Tests for FastMCP server initialization."""

from lorekeeper_mcp import mcp


def test_server_instance_exists(mcp_server):
    """Test that server instance is created with correct name."""
    assert mcp_server is not None
    assert mcp_server.name == "lorekeeper-mcp"


def test_server_exports_from_package():
    """Test that server is exported from package."""
    assert mcp is not None
