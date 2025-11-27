"""Pydantic models for API response parsing and validation.

DEPRECATED: Import models from lorekeeper_mcp.models instead.
This module re-exports from the canonical models package for backward compatibility.
"""

import warnings

from lorekeeper_mcp.models import Armor, Creature, MagicItem, Spell, Weapon

# Re-export canonical models
__all__ = ["Armor", "BaseModel", "Creature", "MagicItem", "Monster", "Spell", "Weapon"]

# Keep BaseModel for backward compatibility
from lorekeeper_mcp.models.base import BaseEntity as BaseModel


def __getattr__(name: str) -> type:
    """Emit deprecation warning for Monster import."""
    if name == "Monster":
        warnings.warn(
            "Importing Monster from api_clients.models is deprecated. "
            "Use 'from lorekeeper_mcp.models import Creature' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return Creature
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
