"""Client for Open5e API v2 (spells, weapons, armor, etc.)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient
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
