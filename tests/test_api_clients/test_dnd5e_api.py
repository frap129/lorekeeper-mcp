"""Tests for Dnd5eApiClient."""

import pytest

from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient


@pytest.fixture
async def dnd5e_client(test_db) -> Dnd5eApiClient:
    """Create Dnd5eApiClient for testing."""
    client = Dnd5eApiClient()
    yield client
    await client.close()


async def test_client_initialization(dnd5e_client: Dnd5eApiClient) -> None:
    """Test client initializes with correct configuration."""
    assert dnd5e_client.base_url == "https://www.dnd5eapi.co/api/2014"
    assert dnd5e_client.source_api == "dnd5e_api"
    assert dnd5e_client.cache_ttl == 604800  # 7 days default
