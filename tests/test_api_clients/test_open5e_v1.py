"""Tests for Open5eV1Client."""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client


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
