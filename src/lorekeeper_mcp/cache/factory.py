"""Cache factory for creating cache instances based on configuration.

This module provides factory functions for creating cache instances
based on backend configuration. Supports both SQLite (legacy) and
Milvus Lite (default) backends.
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
DEFAULT_SQLITE_DB_PATH = "~/.lorekeeper/cache.db"

# Default backend
DEFAULT_CACHE_BACKEND = "milvus"


def create_cache(
    backend: str = DEFAULT_CACHE_BACKEND,
    db_path: str | None = None,
) -> "CacheProtocol":
    """Create a cache instance based on backend type.

    Args:
        backend: Cache backend type ("milvus" or "sqlite"). Defaults to "milvus".
        db_path: Path to database file. If not provided, uses default path
            for the selected backend.

    Returns:
        Cache instance conforming to CacheProtocol.

    Raises:
        ValueError: If backend type is not recognized.
    """
    backend_lower = backend.lower()

    if backend_lower == "milvus":
        from lorekeeper_mcp.cache.milvus import MilvusCache

        if db_path is None:
            db_path = str(Path(DEFAULT_MILVUS_DB_PATH).expanduser())
        logger.info("Creating MilvusCache with db_path: %s", db_path)
        return MilvusCache(db_path)

    if backend_lower == "sqlite":
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        if db_path is None:
            db_path = str(Path(DEFAULT_SQLITE_DB_PATH).expanduser())
        logger.info("Creating SQLiteCache with db_path: %s", db_path)
        return SQLiteCache(db_path)

    raise ValueError(f"Unknown cache backend: '{backend}'. Supported backends: 'milvus', 'sqlite'")


def get_cache_from_config() -> "CacheProtocol":
    """Create a cache instance based on environment configuration.

    Reads configuration from environment variables:
    - LOREKEEPER_CACHE_BACKEND: Backend type ("milvus" or "sqlite")
    - LOREKEEPER_MILVUS_DB_PATH: Path for Milvus database (when backend=milvus)
    - LOREKEEPER_SQLITE_DB_PATH: Path for SQLite database (when backend=sqlite)

    Returns:
        Cache instance conforming to CacheProtocol.
    """
    backend = os.environ.get("LOREKEEPER_CACHE_BACKEND", DEFAULT_CACHE_BACKEND)

    if backend.lower() == "milvus":
        db_path = os.environ.get("LOREKEEPER_MILVUS_DB_PATH", DEFAULT_MILVUS_DB_PATH)
    else:
        db_path = os.environ.get("LOREKEEPER_SQLITE_DB_PATH", DEFAULT_SQLITE_DB_PATH)

    return create_cache(backend=backend, db_path=db_path)
