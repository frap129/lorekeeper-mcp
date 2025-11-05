"""Client for Open5e API v2 (spells, weapons, armor, etc.)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.models.equipment import Armor, Weapon
from lorekeeper_mcp.api_clients.models.spell import Spell


class Open5eV2Client(BaseHttpClient):
    """Client for Open5e API v2 endpoints."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Open5e v2 client.

        Args:
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(base_url="https://api.open5e.com/v2", **kwargs)

    async def get_spells(self, **filters: Any) -> list[Spell]:
        """Get spells with optional filters.

        Args:
            name: Filter by spell name
            level: Filter by spell level (0-9)
            school: Filter by magic school
            **filters: Additional filter parameters

        Returns:
            List of Spell objects
        """
        # Build query parameters
        params = {k: v for k, v in filters.items() if v is not None}

        # Make request
        response = await self.make_request("/spells/", params=params)

        # Parse results
        results = response.get("results", [])
        return [Spell(**spell_data) for spell_data in results]

    async def get_weapons(self, **filters: Any) -> list[Weapon]:
        """Get weapons with optional filters.

        Args:
            name: Filter by weapon name
            category: Filter by weapon category
            **filters: Additional filter parameters

        Returns:
            List of Weapon objects
        """
        params = {k: v for k, v in filters.items() if v is not None}
        response = await self.make_request("/weapons/", params=params)
        results = response.get("results", [])
        return [Weapon(**weapon_data) for weapon_data in results]

    async def get_armor(self, **filters: Any) -> list[Armor]:
        """Get armor with optional filters.

        Args:
            name: Filter by armor name
            category: Filter by armor category
            **filters: Additional filter parameters

        Returns:
            List of Armor objects
        """
        params = {k: v for k, v in filters.items() if v is not None}
        response = await self.make_request("/armor/", params=params)
        results = response.get("results", [])
        return [Armor(**armor_data) for armor_data in results]
