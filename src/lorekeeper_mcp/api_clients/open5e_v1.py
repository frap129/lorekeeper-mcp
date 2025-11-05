"""Client for Open5e API v1 (monsters, classes, races, magic items)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.models.monster import Monster


class Open5eV1Client(BaseHttpClient):
    """Client for Open5e API v1 endpoints."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Open5e v1 client.

        Args:
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(base_url="https://api.open5e.com/v1", **kwargs)

    async def get_monsters(self, **filters: Any) -> list[Monster]:
        """Get monsters with optional filters.

        Args:
            name: Filter by monster name
            challenge_rating: Filter by CR
            type: Filter by creature type
            size: Filter by size
            **filters: Additional filter parameters

        Returns:
            List of Monster objects
        """
        params = {k: v for k, v in filters.items() if v is not None}
        response = await self.make_request("/monsters/", params=params)
        results = response.get("results", [])
        return [Monster(**monster_data) for monster_data in results]
