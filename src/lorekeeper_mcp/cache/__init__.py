"""Caching module for API responses.

This module provides cache implementations for storing and retrieving
D&D entity data. Supports multiple backends:

- MilvusCache: Default backend with semantic/vector search support
- SQLiteCache: Legacy backend with structured filtering only

Use the factory functions to create cache instances:

    from lorekeeper_mcp.cache import create_cache, get_cache_from_config

    # Create with explicit backend
    cache = create_cache(backend="milvus", db_path="~/.lorekeeper/milvus.db")

    # Create from environment configuration
    cache = get_cache_from_config()
"""

from lorekeeper_mcp.cache.embedding import EmbeddingService
from lorekeeper_mcp.cache.factory import create_cache, get_cache_from_config
from lorekeeper_mcp.cache.milvus import MilvusCache
from lorekeeper_mcp.cache.protocol import CacheProtocol
from lorekeeper_mcp.cache.sqlite import SQLiteCache

__all__ = [
    "CacheProtocol",
    "EmbeddingService",
    "MilvusCache",
    "SQLiteCache",
    "create_cache",
    "get_cache_from_config",
]
