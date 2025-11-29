"""FastMCP server instance and lifecycle management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from lorekeeper_mcp.tools import (
    list_documents,
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
    # Milvus Lite initializes lazily on first cache access
    # No explicit init_db() needed
    yield


mcp = FastMCP(
    name="lorekeeper-mcp",
    version="0.1.0",
    lifespan=lifespan,
)
mcp.tool()(list_documents)
mcp.tool()(lookup_spell)
mcp.tool()(lookup_creature)
mcp.tool()(lookup_character_option)
mcp.tool()(lookup_equipment)
mcp.tool()(lookup_rule)
mcp.tool()(search_dnd_content)
