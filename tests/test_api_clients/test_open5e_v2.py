"""Tests for Open5eV2Client."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.cache.db import get_cached_entity
from lorekeeper_mcp.cache.schema import init_entity_cache


@pytest.fixture
async def v2_client(test_db) -> Open5eV2Client:
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
    assert spells[0]["name"] == "Fireball"
    assert spells[0]["level"] == 3


@respx.mock
async def test_get_spells_with_filters(v2_client: Open5eV2Client) -> None:
    """Test spell lookup with multiple filters."""
    respx.get("https://api.open5e.com/v2/spells/?level=3&school=Evocation").mock(
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
                        "name": "Longsword",
                        "slug": "longsword",
                        "category": "Martial Melee",
                        "damage_dice": "1d8",
                        "damage_type": "slashing",
                        "cost": "15 gp",
                        "weight": 3.0,
                    }
                ]
            },
        )
    )

    weapons = await v2_client.get_weapons(name="longsword")

    assert len(weapons) == 1
    assert weapons[0]["name"] == "Longsword"
    assert weapons[0]["damage_dice"] == "1d8"


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
    assert armors[0]["name"] == "Chain Mail"
    assert armors[0]["base_ac"] == 16


@pytest.fixture
async def v2_client_with_cache():
    """Create V2 client with test cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await init_entity_cache(str(db_path))

        import lorekeeper_mcp.config

        original = lorekeeper_mcp.config.settings.db_path
        lorekeeper_mcp.config.settings.db_path = db_path

        client = Open5eV2Client()
        yield client

        lorekeeper_mcp.config.settings.db_path = original
        await client.close()


@pytest.mark.asyncio
async def test_get_spells_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get spells caches entities."""
    mock_response = {
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
    }

    with patch.object(v2_client_with_cache, "_make_request", return_value=mock_response):
        await v2_client_with_cache.get_spells()

    cached = await get_cached_entity("spells", "fireball")
    assert cached is not None
    assert cached["level"] == 3


@pytest.mark.asyncio
async def test_get_weapons_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get weapons caches entities."""
    mock_response = {
        "results": [
            {
                "slug": "longsword",
                "name": "Longsword",
                "category": "martial",
                "damage_dice": "1d8",
                "damage_type": "slashing",
                "cost": "15 gp",
                "weight": 3.0,
            }
        ]
    }

    with patch.object(v2_client_with_cache, "_make_request", return_value=mock_response):
        await v2_client_with_cache.get_weapons()

    cached = await get_cached_entity("weapons", "longsword")
    assert cached is not None


@pytest.mark.asyncio
async def test_get_armor_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get armor caches entities."""
    mock_response = {
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
    }

    with patch.object(v2_client_with_cache, "_make_request", return_value=mock_response):
        await v2_client_with_cache.get_armor()

    cached = await get_cached_entity("armor", "plate-armor")
    assert cached is not None


@pytest.mark.asyncio
async def test_get_backgrounds_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get backgrounds caches entities."""
    mock_response = {
        "results": [{"slug": "acolyte", "name": "Acolyte", "desc": "You have always been..."}]
    }

    with patch.object(v2_client_with_cache, "_make_request", return_value=mock_response):
        await v2_client_with_cache.get_backgrounds()

    cached = await get_cached_entity("backgrounds", "acolyte")
    assert cached is not None


@pytest.mark.asyncio
async def test_get_feats_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get feats caches entities."""
    mock_response = {"results": [{"slug": "alert", "name": "Alert", "desc": "Always vigilant..."}]}

    with patch.object(v2_client_with_cache, "_make_request", return_value=mock_response):
        await v2_client_with_cache.get_feats()

    cached = await get_cached_entity("feats", "alert")
    assert cached is not None


@pytest.mark.asyncio
async def test_get_conditions_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get conditions caches entities."""
    mock_response = {"results": [{"slug": "blinded", "name": "Blinded", "desc": "A blinded..."}]}

    with patch.object(v2_client_with_cache, "_make_request", return_value=mock_response):
        await v2_client_with_cache.get_conditions()

    cached = await get_cached_entity("conditions", "blinded")
    assert cached is not None
