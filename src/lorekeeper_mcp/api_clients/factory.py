"""Factory for creating API client instances with dependency injection."""

from typing import Any

from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


class ClientFactory:
    """Factory for creating API client instances."""

    @staticmethod
    def create_open5e_v1(**kwargs: Any) -> Open5eV1Client:
        """Create an Open5e v1 API client.

        Args:
            **kwargs: Configuration options for the client

        Returns:
            Configured Open5eV1Client instance
        """
        return Open5eV1Client(**kwargs)

    @staticmethod
    def create_open5e_v2(**kwargs: Any) -> Open5eV2Client:
        """Create an Open5e v2 API client.

        Args:
            **kwargs: Configuration options for the client

        Returns:
            Configured Open5eV2Client instance
        """
        return Open5eV2Client(**kwargs)

    @staticmethod
    def create_dnd5e_api(**kwargs: Any) -> Dnd5eApiClient:
        """Create a D&D 5e API client.

        Args:
            **kwargs: Configuration options for the client
                base_url: Override base URL (default: https://www.dnd5eapi.co/api/2014)
                cache_ttl: Override cache TTL (default: 604800 = 7 days)
                timeout: Request timeout in seconds (default: 30.0)
                max_retries: Maximum retry attempts (default: 5)

        Returns:
            Configured Dnd5eApiClient instance

        Example:
            >>> client = ClientFactory.create_dnd5e_api()
            >>> rules = await client.get_rules()
        """
        return Dnd5eApiClient(**kwargs)
