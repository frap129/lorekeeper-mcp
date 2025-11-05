"""Configuration management using Pydantic Settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    db_path: Path = Field(default=Path("./data/cache.db"))
    cache_ttl_days: int = Field(default=7)
    error_cache_ttl_seconds: int = Field(default=300)
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    open5e_base_url: str = Field(default="https://api.open5e.com")
    dnd5e_base_url: str = Field(default="https://www.dnd5eapi.co/api")


# Global settings instance
settings = Settings()
