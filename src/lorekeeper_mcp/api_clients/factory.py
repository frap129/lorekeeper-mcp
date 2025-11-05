"""Factory for creating API client instances with dependency injection."""

from typing import Any

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
