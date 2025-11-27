"""Canonical Pydantic models for LoreKeeper entities.

This package contains the single source of truth for all entity models.
All data sources (API clients, OrcBrew parser) transform to these models.
"""

from lorekeeper_mcp.models.base import BaseEntity
from lorekeeper_mcp.models.creature import Creature, Monster

__all__ = ["BaseEntity", "Creature", "Monster"]
