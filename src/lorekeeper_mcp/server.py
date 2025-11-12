"""FastMCP server instance and lifecycle management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from lorekeeper_mcp.cache.db import init_db
from lorekeeper_mcp.tools import (
    lookup_character_option,
    lookup_creature,
    lookup_equipment,
    lookup_rule,
    lookup_spell,
    search_dnd_content,
)


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncGenerator[None]:
    """Initialize resources on startup, cleanup on shutdown."""
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Cleanup if needed (currently none)


# Create FastMCP server instance
# Note: FastMCP doesn't support description parameter in constructor
# Description will be available through tools when they are implemented
mcp = FastMCP(
    name="lorekeeper-mcp",
    version="0.1.0",
    lifespan=lifespan,
)

# Register tools with FastMCP
mcp.tool()(lookup_spell)
mcp.tool()(lookup_creature)
mcp.tool()(lookup_character_option)
mcp.tool()(lookup_equipment)
mcp.tool()(lookup_rule)
mcp.tool()(search_dnd_content)
