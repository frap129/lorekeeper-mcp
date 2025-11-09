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


@respx.mock
async def test_get_magic_items_by_type(v1_client: Open5eV1Client) -> None:
    """Test magic item lookup by type."""
    respx.get("https://api.open5e.com/v1/magicitems/?type=wondrous+item").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "bag-of-holding",
                        "name": "Bag of Holding",
                        "type": "wondrous item",
                        "rarity": "uncommon",
                        "requires_attunement": False,
                    }
                ]
            },
        )
    )

    items = await v1_client.get_magic_items(item_type="wondrous item")

    assert len(items) == 1
    assert items[0]["name"] == "Bag of Holding"
    assert items[0]["type"] == "wondrous item"


@respx.mock
async def test_get_magic_items_by_attunement(v1_client: Open5eV1Client) -> None:
    """Test magic item lookup by attunement requirement."""
    respx.get("https://api.open5e.com/v1/magicitems/?requires_attunement=true").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "staff-of-power",
                        "name": "Staff of Power",
                        "type": "staff",
                        "rarity": "very rare",
                        "requires_attunement": True,
                    }
                ]
            },
        )
    )

    items = await v1_client.get_magic_items(requires_attunement=True)

    assert len(items) == 1
    assert items[0]["name"] == "Staff of Power"
    assert items[0]["requires_attunement"] is True


@respx.mock
async def test_get_magic_items_multiple_filters(v1_client: Open5eV1Client) -> None:
    """Test magic item lookup with multiple filter parameters."""
    respx.get(
        "https://api.open5e.com/v1/magicitems/?type=ring&rarity=rare&requires_attunement=true"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "ring-of-spell-storing",
                        "name": "Ring of Spell Storing",
                        "type": "ring",
                        "rarity": "rare",
                        "requires_attunement": True,
                    }
                ]
            },
        )
    )

    items = await v1_client.get_magic_items(
        item_type="ring",
        rarity="rare",
        requires_attunement=True,
    )

    assert len(items) == 1
    assert items[0]["name"] == "Ring of Spell Storing"
    assert items[0]["type"] == "ring"
    assert items[0]["rarity"] == "rare"
    assert items[0]["requires_attunement"] is True


@respx.mock
async def test_get_spell_list(v1_client: Open5eV1Client) -> None:
    """Test spell list lookup."""
    respx.get("https://api.open5e.com/v1/spells/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "fireball",
                        "name": "Fireball",
                        "level": 3,
                        "school": "evocation",
                        "concentration": False,
                        "ritual": False,
                    }
                ]
            },
        )
    )

    spells = await v1_client.get_spell_list()

    assert len(spells) == 1
    assert spells[0]["name"] == "Fireball"
    assert spells[0]["level"] == 3
    assert spells[0]["school"] == "evocation"


@respx.mock
async def test_get_spell_list_by_class(v1_client: Open5eV1Client) -> None:
    """Test spell list lookup by class."""
    respx.get("https://api.open5e.com/v1/spells/?class=wizard").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "fireball",
                        "name": "Fireball",
                        "level": 3,
                        "school": "evocation",
                        "concentration": False,
                        "ritual": False,
                    },
                    {
                        "slug": "magic-missile",
                        "name": "Magic Missile",
                        "level": 1,
                        "school": "evocation",
                        "concentration": False,
                        "ritual": False,
                    },
                ]
            },
        )
    )

    spells = await v1_client.get_spell_list(class_name="wizard")

    assert len(spells) == 2
    assert spells[0]["name"] == "Fireball"
    assert spells[1]["name"] == "Magic Missile"


@respx.mock
async def test_get_manifest(v1_client: Open5eV1Client) -> None:
    """Test manifest retrieval."""
    respx.get("https://api.open5e.com/v1/").mock(
        return_value=httpx.Response(
            200,
            json={
                "spells": "https://api.open5e.com/v1/spells/",
                "monsters": "https://api.open5e.com/v1/monsters/",
                "magicitems": "https://api.open5e.com/v1/magicitems/",
                "weapons": "https://api.open5e.com/v1/weapons/",
                "armor": "https://api.open5e.com/v1/armor/",
                "classes": "https://api.open5e.com/v1/classes/",
                "races": "https://api.open5e.com/v1/races/",
                "planes": "https://api.open5e.com/v1/planes/",
                "sections": "https://api.open5e.com/v1/sections/",
            },
        )
    )

    manifest = await v1_client.get_manifest()

    assert isinstance(manifest, dict)
    assert "spells" in manifest
    assert "monsters" in manifest
    assert "magicitems" in manifest
