"""Tests for Open5eV2Client."""

import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
import respx

import lorekeeper_mcp.config
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.cache.db import get_cached_entity
from lorekeeper_mcp.cache.schema import init_entity_cache


@pytest.fixture
async def v2_client(test_db) -> AsyncGenerator[Open5eV2Client]:
    """Create Open5eV2Client for testing."""
    client = Open5eV2Client()
    yield client
    await client.close()


@respx.mock
async def test_get_spells_basic(v2_client: Open5eV2Client) -> None:
    """Test basic spell lookup."""
    respx.get("https://api.open5e.com/v2/spells/?name=fireball").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Fireball",
                        "slug": "fireball",
                        "level": 3,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "150 feet",
                        "components": "V, S, M",
                        "duration": "Instantaneous",
                        "desc": "A bright streak...",
                    }
                ]
            },
        )
    )

    spells = await v2_client.get_spells(name="fireball")

    assert len(spells) == 1
    assert spells[0].name == "Fireball"
    assert spells[0].level == 3


@respx.mock
async def test_get_spells_with_filters(v2_client: Open5eV2Client) -> None:
    """Test spell lookup with level and school filters.

    School filtering is done client-side (not supported by API),
    so only level is sent to the API.
    """
    respx.get("https://api.open5e.com/v2/spells/?level=3").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    spells = await v2_client.get_spells(level=3, school="Evocation")

    assert isinstance(spells, list)


@respx.mock
async def test_get_weapons(v2_client: Open5eV2Client) -> None:
    """Test weapon lookup."""
    respx.get("https://api.open5e.com/v2/weapons/?name=longsword").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "url": "https://api.open5e.com/v2/weapons/srd-2024_longsword/",
                        "key": "srd-2024_longsword",
                        "name": "Longsword",
                        "slug": "longsword",
                        "damage_dice": "1d8",
                        "damage_type": {
                            "name": "Slashing",
                            "key": "slashing",
                            "url": "https://api.open5e.com/v2/damagetypes/slashing/",
                        },
                        "properties": [
                            {
                                "property": {
                                    "name": "Versatile",
                                    "type": None,
                                    "url": "/v2/weaponproperties/versatile-wp/",
                                },
                                "detail": "1d10",
                            }
                        ],
                        "range": 0.0,
                        "long_range": 0.0,
                        "distance_unit": "feet",
                        "is_simple": False,
                        "is_improvised": False,
                    }
                ]
            },
        )
    )

    weapons = await v2_client.get_weapons(name="longsword")

    assert len(weapons) == 1
    assert weapons[0].name == "Longsword"
    assert weapons[0].damage_dice == "1d8"


@respx.mock
async def test_get_armor(v2_client: Open5eV2Client) -> None:
    """Test armor lookup."""
    respx.get("https://api.open5e.com/v2/armor/?name=chain-mail").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Chain Mail",
                        "slug": "chain-mail",
                        "category": "Heavy",
                        "base_ac": 16,
                        "cost": "75 gp",
                        "weight": 55.0,
                        "stealth_disadvantage": True,
                    }
                ]
            },
        )
    )

    armors = await v2_client.get_armor(name="chain-mail")

    assert len(armors) == 1
    assert armors[0].name == "Chain Mail"
    assert armors[0].base_ac == 16


@pytest.fixture
async def v2_client_with_cache() -> AsyncGenerator[Open5eV2Client]:
    """Create V2 client with test cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await init_entity_cache(str(db_path))

        original = lorekeeper_mcp.config.settings.db_path
        lorekeeper_mcp.config.settings.db_path = db_path

        client = Open5eV2Client()
        yield client

        lorekeeper_mcp.config.settings.db_path = original
        await client.close()


@respx.mock
async def test_get_spells_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get spells caches entities."""
    respx.get("https://api.open5e.com/v2/spells/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "fireball",
                        "name": "Fireball",
                        "level": 3,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "150 feet",
                        "components": "V, S, M",
                        "duration": "Instantaneous",
                    }
                ]
            },
        )
    )

    spells = await v2_client_with_cache.get_spells()
    # Verify we got Pydantic models
    assert len(spells) == 1
    assert spells[0].name == "Fireball"
    assert spells[0].level == 3

    # Verify caching worked
    cached = await get_cached_entity("spells", "fireball")
    assert cached is not None
    assert cached["level"] == 3


@respx.mock
@pytest.mark.asyncio
async def test_get_weapons_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get weapons caches entities and returns Pydantic models."""
    respx.get("https://api.open5e.com/v2/weapons/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "url": "https://api.open5e.com/v2/weapons/srd-2024_longsword/",
                        "key": "srd-2024_longsword",
                        "slug": "longsword",
                        "name": "Longsword",
                        "damage_dice": "1d8",
                        "damage_type": {
                            "name": "Slashing",
                            "key": "slashing",
                            "url": "https://api.open5e.com/v2/damagetypes/slashing/",
                        },
                        "properties": [],
                        "range": 0.0,
                        "long_range": 0.0,
                        "distance_unit": "feet",
                        "is_simple": False,
                        "is_improvised": False,
                    }
                ]
            },
        )
    )

    weapons = await v2_client_with_cache.get_weapons()
    assert len(weapons) == 1
    assert weapons[0].name == "Longsword"

    cached = await get_cached_entity("weapons", "longsword")
    assert cached is not None


@respx.mock
@pytest.mark.asyncio
async def test_get_armor_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get armor caches entities and returns Pydantic models."""
    respx.get("https://api.open5e.com/v2/armor/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "plate-armor",
                        "name": "Plate Armor",
                        "category": "Heavy",
                        "base_ac": 18,
                        "cost": "1500 gp",
                        "weight": 65.0,
                    }
                ]
            },
        )
    )

    armors = await v2_client_with_cache.get_armor()
    assert len(armors) == 1
    assert armors[0].name == "Plate Armor"

    cached = await get_cached_entity("armor", "plate-armor")
    assert cached is not None


@respx.mock
@pytest.mark.asyncio
async def test_get_backgrounds_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get backgrounds caches entities."""
    respx.get("https://api.open5e.com/v2/backgrounds/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"slug": "acolyte", "name": "Acolyte", "desc": "You have always been..."}
                ]
            },
        )
    )

    backgrounds = await v2_client_with_cache.get_backgrounds()
    assert len(backgrounds) == 1
    assert backgrounds[0]["name"] == "Acolyte"

    cached = await get_cached_entity("backgrounds", "acolyte")
    assert cached is not None


@respx.mock
@pytest.mark.asyncio
async def test_get_feats_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get feats caches entities."""
    respx.get("https://api.open5e.com/v2/feats/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "alert", "name": "Alert", "desc": "Always vigilant..."}]},
        )
    )

    feats = await v2_client_with_cache.get_feats()
    assert len(feats) == 1
    assert feats[0]["name"] == "Alert"

    cached = await get_cached_entity("feats", "alert")
    assert cached is not None


@respx.mock
@pytest.mark.asyncio
async def test_get_conditions_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get conditions caches entities."""
    respx.get("https://api.open5e.com/v2/conditions/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "blinded", "name": "Blinded", "desc": "A blinded..."}]},
        )
    )

    conditions = await v2_client_with_cache.get_conditions()
    assert len(conditions) == 1
    assert conditions[0]["name"] == "Blinded"

    cached = await get_cached_entity("conditions", "blinded")
    assert cached is not None


@respx.mock
async def test_spell_school_filtering(v2_client: Open5eV2Client) -> None:
    """Test that get_spells filters by school on client side.

    Open5e v2 API doesn't support server-side school filtering, so
    client must filter results after retrieval.
    """
    # Mock the API call without school parameter - API returns all spells
    respx.get("https://api.open5e.com/v2/spells/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Fireball",
                        "slug": "fireball",
                        "level": 3,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "150 feet",
                        "components": "V, S, M",
                        "duration": "Instantaneous",
                        "desc": "A bright streak...",
                    },
                    {
                        "name": "Magic Missile",
                        "slug": "magic-missile",
                        "level": 1,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "120 feet",
                        "components": "V, S",
                        "duration": "Instantaneous",
                        "desc": "A missile of magical force...",
                    },
                    {
                        "name": "Detect Magic",
                        "slug": "detect-magic",
                        "level": 1,
                        "school": "Divination",
                        "casting_time": "1 action",
                        "range": "Self",
                        "components": "V, S",
                        "duration": "Concentration, up to 10 minutes",
                        "desc": "For the spell's duration...",
                    },
                ]
            },
        )
    )

    # Request spells filtered by school
    spells = await v2_client.get_spells(school="Evocation")

    # Should only return evocation spells
    assert len(spells) == 2
    assert all(spell.school == "Evocation" for spell in spells)
    assert {spell.name for spell in spells} == {"Fireball", "Magic Missile"}


@respx.mock
async def test_spell_school_filtering_case_insensitive(
    v2_client: Open5eV2Client,
) -> None:
    """Test that school filtering is case-insensitive.

    The filtering should match spells regardless of the case of the
    school parameter provided by the user.
    """
    respx.get("https://api.open5e.com/v2/spells/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Fireball",
                        "slug": "fireball",
                        "level": 3,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "150 feet",
                        "components": "V, S, M",
                        "duration": "Instantaneous",
                        "desc": "A bright streak...",
                    },
                    {
                        "name": "Detect Magic",
                        "slug": "detect-magic",
                        "level": 1,
                        "school": "Divination",
                        "casting_time": "1 action",
                        "range": "Self",
                        "components": "V, S",
                        "duration": "Concentration, up to 10 minutes",
                        "desc": "For the spell's duration...",
                    },
                ]
            },
        )
    )

    # Test with lowercase input
    spells = await v2_client.get_spells(school="evocation")
    assert len(spells) == 1
    assert spells[0].name == "Fireball"

    # Test with uppercase input
    spells = await v2_client.get_spells(school="EVOCATION")
    assert len(spells) == 1
    assert spells[0].name == "Fireball"

    # Test with mixed case input
    spells = await v2_client.get_spells(school="EvOcAtIoN")
    assert len(spells) == 1
    assert spells[0].name == "Fireball"
