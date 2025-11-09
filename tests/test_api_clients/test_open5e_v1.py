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


@respx.mock
async def test_get_magic_items(v1_client: Open5eV1Client) -> None:
    """Test magic item lookup."""
    respx.get("https://api.open5e.com/v1/magicitems/?name=ring").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "ring-of-protection",
                        "name": "Ring of Protection",
                        "type": "ring",
                        "rarity": "uncommon",
                        "requires_attunement": False,
                        "description": "This ring provides +1 to AC and saves.",
                    }
                ]
            },
        )
    )

    items = await v1_client.get_magic_items(name="ring")

    assert len(items) == 1
    assert items[0]["name"] == "Ring of Protection"
    assert items[0]["type"] == "ring"
    assert items[0]["rarity"] == "uncommon"


@respx.mock
async def test_get_magic_items_uses_entity_cache(v1_client: Open5eV1Client) -> None:
    """Get magic items caches entities."""
    mock_response = {
        "results": [
            {
                "slug": "ring-of-protection",
                "name": "Ring of Protection",
                "type": "ring",
                "rarity": "uncommon",
                "requires_attunement": False,
                "description": "This ring provides +1 to AC and saves.",
            }
        ]
    }
    respx.get("https://api.open5e.com/v1/magicitems/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await v1_client.get_magic_items()

    cached = await get_cached_entity("magicitems", "ring-of-protection")
    assert cached is not None
    assert cached["name"] == "Ring of Protection"
    assert cached["type"] == "ring"
    assert cached["rarity"] == "uncommon"


@respx.mock
async def test_get_magic_items_by_rarity(v1_client: Open5eV1Client) -> None:
    """Test magic item lookup by rarity."""
    respx.get("https://api.open5e.com/v1/magicitems/?rarity=legendary").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "bag-of-holding",
                        "name": "Bag of Holding",
                        "type": "wondrous item",
                        "rarity": "legendary",
                        "requires_attunement": False,
                    }
                ]
            },
        )
    )

    items = await v1_client.get_magic_items(rarity="legendary")

    assert isinstance(items, list)


@respx.mock
async def test_get_planes(v1_client: Open5eV1Client) -> None:
    """Test plane lookup."""
    respx.get("https://api.open5e.com/v1/planes/?name=feywild").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "feywild",
                        "name": "Feywild",
                        "description": "A realm of magic and wonder.",
                    }
                ]
            },
        )
    )

    planes = await v1_client.get_planes(name="feywild")

    assert len(planes) == 1
    assert planes[0]["name"] == "Feywild"
    assert planes[0]["slug"] == "feywild"


@respx.mock
async def test_get_planes_uses_entity_cache(v1_client: Open5eV1Client) -> None:
    """Get planes caches entities."""
    mock_response = {
        "results": [
            {
                "slug": "feywild",
                "name": "Feywild",
                "description": "A realm of magic and wonder.",
            }
        ]
    }
    respx.get("https://api.open5e.com/v1/planes/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await v1_client.get_planes()

    cached = await get_cached_entity("planes", "feywild")
    assert cached is not None
    assert cached["name"] == "Feywild"
    assert cached["description"] == "A realm of magic and wonder."


@respx.mock
async def test_get_sections(v1_client: Open5eV1Client) -> None:
    """Test sections lookup with name filter."""
    respx.get("https://api.open5e.com/v1/sections/?name=introduction").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "introduction",
                        "name": "Introduction",
                        "parent": None,
                        "desc": "Getting started with D&D",
                    }
                ]
            },
        )
    )

    sections = await v1_client.get_sections(name="introduction")

    assert len(sections) == 1
    assert sections[0]["name"] == "Introduction"
    assert sections[0]["slug"] == "introduction"
    assert sections[0]["parent"] is None


@respx.mock
async def test_get_sections_uses_entity_cache(v1_client: Open5eV1Client) -> None:
    """Get sections caches entities."""
    mock_response = {
        "results": [
            {
                "slug": "introduction",
                "name": "Introduction",
                "parent": None,
                "desc": "Getting started with D&D",
            }
        ]
    }
    respx.get("https://api.open5e.com/v1/sections/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await v1_client.get_sections()

    cached = await get_cached_entity("sections", "introduction")
    assert cached is not None
    assert cached["name"] == "Introduction"
    assert cached["parent"] is None


@respx.mock
async def test_get_sections_by_parent(v1_client: Open5eV1Client) -> None:
    """Test sections lookup by parent (hierarchical filtering)."""
    respx.get("https://api.open5e.com/v1/sections/?parent=phb").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "phb-chapter-1",
                        "name": "Chapter 1",
                        "parent": "phb",
                        "desc": "Overview of rules",
                    }
                ]
            },
        )
    )

    sections = await v1_client.get_sections(parent="phb")

    assert len(sections) == 1
    assert sections[0]["name"] == "Chapter 1"
    assert sections[0]["parent"] == "phb"
