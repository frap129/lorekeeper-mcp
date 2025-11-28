"""Configuration management using Pydantic Settings."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides.

    Configuration for LoreKeeper MCP including cache backend, database paths,
    and API settings. All settings can be overridden via environment variables
    with the LOREKEEPER_ prefix (handled automatically by pydantic-settings).

    Attributes:
        cache_backend: Cache backend type ("milvus" or "sqlite"). Defaults to "milvus".
        milvus_db_path: Path to Milvus Lite database file.
        embedding_model: Name of sentence-transformers model for embeddings.
        db_path: Legacy SQLite database path.
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

    # Cache backend configuration
    cache_backend: str = Field(default="milvus")
    milvus_db_path: Path = Field(default=Path("~/.lorekeeper/milvus.db"))
    embedding_model: str = Field(default="all-MiniLM-L6-v2")

    # Legacy SQLite configuration (for backward compatibility)
    db_path: Path = Field(default=Path("./data/cache.db"))

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

    @field_validator("db_path", mode="before")
    @classmethod
    def expand_db_path(cls, v: str | Path) -> Path:
        """Expand tilde in SQLite database path."""
        return Path(v).expanduser()


# Global settings instance
settings = Settings()
