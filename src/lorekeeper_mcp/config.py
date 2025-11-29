"""Configuration management using Pydantic Settings."""

import logging
import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Path constants
LEGACY_MILVUS_DB_PATH = Path("~/.lorekeeper/milvus.db")
XDG_DATA_HOME_DEFAULT = Path("~/.local/share")
LOREKEEPER_DATA_DIR = "lorekeeper"
MILVUS_DB_FILENAME = "milvus.db"


def get_xdg_data_home() -> Path:
    """Get XDG_DATA_HOME path, defaulting to ~/.local/share if not set.

    Returns:
        Path to the XDG data home directory.
    """
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home).expanduser()
    return XDG_DATA_HOME_DEFAULT.expanduser()


def get_default_milvus_db_path() -> Path:
    """Determine the default Milvus database path with backward compatibility.

    Path resolution order:
    1. If legacy path (~/.lorekeeper/milvus.db) exists AND XDG path doesn't exist,
       use legacy path for backward compatibility
    2. Otherwise, use XDG path ($XDG_DATA_HOME/lorekeeper/milvus.db or
       ~/.local/share/lorekeeper/milvus.db)

    If both paths exist, prefer XDG and log a warning about the orphaned legacy database.

    Returns:
        Path to the Milvus database file.
    """
    legacy_path = LEGACY_MILVUS_DB_PATH.expanduser()
    xdg_path = get_xdg_data_home() / LOREKEEPER_DATA_DIR / MILVUS_DB_FILENAME

    legacy_exists = legacy_path.exists()
    xdg_exists = xdg_path.exists()

    if legacy_exists and xdg_exists:
        logger.warning(
            "Database exists at both legacy (%s) and XDG (%s) locations. "
            "Using XDG location. Consider removing the legacy database.",
            legacy_path,
            xdg_path,
        )
        return xdg_path
    if legacy_exists and not xdg_exists:
        logger.info(
            "Using legacy database location (%s) for backward compatibility. "
            "New installations use %s.",
            legacy_path,
            xdg_path,
        )
        return legacy_path
    # Either XDG exists, or neither exists (new installation)
    return xdg_path


class Settings(BaseSettings):
    """Application settings with environment variable overrides.

    Configuration for LoreKeeper MCP including cache database path,
    and API settings. All settings can be overridden via environment variables
    with the LOREKEEPER_ prefix (handled automatically by pydantic-settings).

    Attributes:
        milvus_db_path: Path to Milvus Lite database file.
        embedding_model: Name of sentence-transformers model for embeddings.
        cache_ttl_days: TTL for cached responses in days.
        error_cache_ttl_seconds: TTL for cached error responses in seconds.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        debug: Enable debug mode with verbose logging.
        open5e_base_url: Base URL for Open5e API.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="LOREKEEPER_",
    )

    # Cache configuration (Milvus)
    milvus_db_path: Path = Field(default_factory=get_default_milvus_db_path)
    embedding_model: str = Field(default="all-MiniLM-L6-v2")

    # Cache TTL configuration
    cache_ttl_days: int = Field(default=7)
    error_cache_ttl_seconds: int = Field(default=300)

    # Logging configuration
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)

    # API configuration
    open5e_base_url: str = Field(default="https://api.open5e.com")

    @field_validator("milvus_db_path", mode="before")
    @classmethod
    def expand_milvus_path(cls, v: str | Path) -> Path:
        """Expand tilde in Milvus database path."""
        return Path(v).expanduser()


# Global settings instance
settings = Settings()
