"""Tests for Open5eV1Client."""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.cache.db import get_cached_entity


@pytest.fixture
async def v1_client(test_db) -> Open5eV1Client:
    """Create Open5eV1Client for testing."""
    client = Open5eV1Client()
    yield client
    await client.close()


@respx.mock
async def test_get_monsters(v1_client: Open5eV1Client) -> None:
    """Test monster lookup."""
    respx.get("https://api.open5e.com/v1/monsters/?name=goblin").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Goblin",
                        "slug": "goblin",
                        "size": "Small",
                        "type": "humanoid",
                        "alignment": "neutral evil",
                        "armor_class": 15,
                        "hit_points": 7,
                        "hit_dice": "2d6",
                        "challenge_rating": "1/4",
                    }
                ]
            },
        )
    )

    monsters = await v1_client.get_monsters(name="goblin")

    assert len(monsters) == 1
    assert monsters[0].name == "Goblin"
    assert monsters[0].challenge_rating == "1/4"


@respx.mock
async def test_get_monsters_by_cr(v1_client: Open5eV1Client) -> None:
    """Test monster lookup by challenge rating."""
    respx.get("https://api.open5e.com/v1/monsters/?challenge_rating=5").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    monsters = await v1_client.get_monsters(challenge_rating="5")

    assert isinstance(monsters, list)


@respx.mock
async def test_get_monsters_uses_entity_cache(v1_client: Open5eV1Client) -> None:
    """Get monsters caches entities, not URLs."""
    mock_response = {
        "results": [
            {
                "slug": "goblin",
                "name": "Goblin",
                "type": "humanoid",
                "challenge_rating": "1/4",
                "size": "Small",
                "alignment": "neutral evil",
                "armor_class": 15,
                "hit_points": 7,
                "hit_dice": "2d6",
            }
        ]
    }
    respx.get("https://api.open5e.com/v1/monsters/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await v1_client.get_monsters()

    # Verify entity cached
    cached = await get_cached_entity("monsters", "goblin")
    assert cached is not None
    assert cached["name"] == "Goblin"
    assert cached["type"] == "humanoid"


@respx.mock
async def test_get_classes_uses_entity_cache(v1_client: Open5eV1Client) -> None:
    """Get classes caches entities."""
    mock_response = {"results": [{"slug": "fighter", "name": "Fighter", "hit_die": 10}]}
    respx.get("https://api.open5e.com/v1/classes/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await v1_client.get_classes()

    cached = await get_cached_entity("classes", "fighter")
    assert cached is not None
    assert cached["hit_die"] == 10


@respx.mock
async def test_get_races_uses_entity_cache(v1_client: Open5eV1Client) -> None:
    """Get races caches entities."""
    mock_response = {
        "results": [{"slug": "human", "name": "Human", "ability_bonuses": "+1 to all"}]
    }
    respx.get("https://api.open5e.com/v1/races/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await v1_client.get_races()

    cached = await get_cached_entity("races", "human")
    assert cached is not None
    assert cached["ability_bonuses"] == "+1 to all"
