"""FastMCP server instance and lifecycle management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from lorekeeper_mcp.tools import (
    list_documents,
    search_all,
    search_character_option,
    search_creature,
    search_equipment,
    search_rule,
    search_spell,
)


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncGenerator[None]:
    """Initialize resources on startup, cleanup on shutdown."""
    # Milvus Lite initializes lazily on first cache access
    # No explicit init_db() needed
    yield


mcp = FastMCP(
    name="lorekeeper-mcp",
    version="0.1.0",
    lifespan=lifespan,
)
mcp.tool()(list_documents)
mcp.tool()(search_spell)
mcp.tool()(search_creature)
mcp.tool()(search_character_option)
mcp.tool()(search_equipment)
mcp.tool()(search_rule)
mcp.tool()(search_all)
