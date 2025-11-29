"""Cache factory for creating Milvus cache instances.

This module provides factory functions for creating MilvusCache instances
with semantic/vector search capabilities.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lorekeeper_mcp.cache.protocol import CacheProtocol

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_MILVUS_DB_PATH = "~/.lorekeeper/milvus.db"


def create_cache(
    db_path: str | None = None,
) -> "CacheProtocol":
    """Create a MilvusCache instance.

    Args:
        db_path: Path to Milvus database file. If not provided, uses default path.

    Returns:
        MilvusCache instance conforming to CacheProtocol.
    """
    from lorekeeper_mcp.cache.milvus import MilvusCache

    if db_path is None:
        db_path = str(Path(DEFAULT_MILVUS_DB_PATH).expanduser())
    logger.info("Creating MilvusCache with db_path: %s", db_path)
    return MilvusCache(db_path)


def get_cache_from_config() -> "CacheProtocol":
    """Create a MilvusCache instance based on environment configuration.

    Reads configuration from environment variables:
    - LOREKEEPER_MILVUS_DB_PATH: Path for Milvus database

    Returns:
        MilvusCache instance conforming to CacheProtocol.
    """
    db_path = os.environ.get("LOREKEEPER_MILVUS_DB_PATH", DEFAULT_MILVUS_DB_PATH)
    return create_cache(db_path=db_path)
