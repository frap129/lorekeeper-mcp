"""Caching module for API responses.

This module provides Milvus-based caching with semantic/vector search support
for storing and retrieving D&D entity data.

Use the factory functions to create cache instances:

    from lorekeeper_mcp.cache import create_cache, get_cache_from_config

    # Create Milvus cache
    cache = create_cache(db_path="~/.lorekeeper/milvus.db")

    # Create from environment configuration
    cache = get_cache_from_config()
"""

from lorekeeper_mcp.cache.embedding import EmbeddingService
from lorekeeper_mcp.cache.factory import create_cache, get_cache_from_config
from lorekeeper_mcp.cache.milvus import MilvusCache
from lorekeeper_mcp.cache.protocol import CacheProtocol

__all__ = [
    "CacheProtocol",
    "EmbeddingService",
    "MilvusCache",
    "create_cache",
    "get_cache_from_config",
]
