"""Tests for ClientFactory."""

from lorekeeper_mcp.api_clients.factory import ClientFactory
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


def test_create_open5e_v1_client() -> None:
    """Test factory creates Open5eV1Client."""
    client = ClientFactory.create_open5e_v1()

    assert isinstance(client, Open5eV1Client)
    assert client.base_url == "https://api.open5e.com/v1"


def test_create_open5e_v2_client() -> None:
    """Test factory creates Open5eV2Client."""
    client = ClientFactory.create_open5e_v2()

    assert isinstance(client, Open5eV2Client)
    assert client.base_url == "https://api.open5e.com/v2"


def test_factory_with_custom_timeout() -> None:
    """Test factory accepts custom configuration."""
    client = ClientFactory.create_open5e_v1(timeout=60.0)

    assert client.timeout == 60.0


async def test_factory_clients_are_independent() -> None:
    """Test that factory creates independent client instances."""
    client1 = ClientFactory.create_open5e_v1()
    client2 = ClientFactory.create_open5e_v1()

    assert client1 is not client2

    await client1.close()
    await client2.close()
