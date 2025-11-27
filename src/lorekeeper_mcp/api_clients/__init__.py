"""API clients for external D&D data sources.

Models are now in lorekeeper_mcp.models. Imports from api_clients.models
are deprecated but still work for backward compatibility.
"""

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.exceptions import (
    ApiClientError,
    ApiError,
    CacheError,
    NetworkError,
    ParseError,
)
from lorekeeper_mcp.api_clients.factory import ClientFactory
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

# Re-export models for backward compatibility (deprecated)
from lorekeeper_mcp.models import Armor, Creature, MagicItem, Spell, Weapon

__all__ = [
    "ApiClientError",
    "ApiError",
    "Armor",
    "BaseHttpClient",
    "CacheError",
    "ClientFactory",
    "Creature",
    "MagicItem",
    "NetworkError",
    "Open5eV1Client",
    "Open5eV2Client",
    "ParseError",
    "Spell",
    "Weapon",
]
