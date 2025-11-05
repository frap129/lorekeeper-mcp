"""FastMCP server instance and lifecycle management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from lorekeeper_mcp.cache.db import init_db


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


# Tools will be registered here in future tasks
