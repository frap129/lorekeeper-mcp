"""Tests for equipment lookup tool."""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_lookup_weapon(mock_open5e_v2_client):
    """Test looking up a weapon."""
    from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

    mock_open5e_v2_client.get_weapons.return_value = {
        "count": 1,
        "results": [{"name": "Longsword", "damage_dice": "1d8"}],
    }

    with patch(
        "lorekeeper_mcp.tools.equipment_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_equipment(type="weapon", name="Longsword")

    assert len(result) == 1
    assert result[0]["name"] == "Longsword"
    mock_open5e_v2_client.get_weapons.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_armor(mock_open5e_v2_client):
    """Test looking up armor."""
    from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

    mock_open5e_v2_client.get_armor.return_value = {
        "count": 1,
        "results": [{"name": "Chain Mail", "ac_base": 16}],
    }

    with patch(
        "lorekeeper_mcp.tools.equipment_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_equipment(type="armor", name="Chain Mail")

    assert len(result) == 1
    assert result[0]["name"] == "Chain Mail"
    mock_open5e_v2_client.get_armor.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_simple_weapons(mock_open5e_v2_client):
    """Test filtering for simple weapons."""
    from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

    mock_open5e_v2_client.get_weapons.return_value = {
        "count": 2,
        "results": [
            {"name": "Club", "is_simple": True},
            {"name": "Dagger", "is_simple": True},
        ],
    }

    with patch(
        "lorekeeper_mcp.tools.equipment_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        await lookup_equipment(type="weapon", is_simple=True)

    call_kwargs = mock_open5e_v2_client.get_weapons.call_args[1]
    assert call_kwargs["is_simple"] is True


@pytest.mark.asyncio
async def test_lookup_all_equipment_types(mock_open5e_v1_client, mock_open5e_v2_client):
    """Test looking up all equipment types."""
    from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment

    mock_open5e_v2_client.get_weapons.return_value = {
        "count": 1,
        "results": [{"name": "Chain Whip", "type": "weapon"}],
    }
    mock_open5e_v2_client.get_armor.return_value = {
        "count": 1,
        "results": [{"name": "Chain Mail", "type": "armor"}],
    }
    mock_open5e_v1_client.get_magic_items.return_value = {
        "count": 1,
        "results": [{"name": "Chain of Binding", "type": "magic-item"}],
    }

    with (
        patch(
            "lorekeeper_mcp.tools.equipment_lookup.Open5eV2Client",
            return_value=mock_open5e_v2_client,
        ),
        patch(
            "lorekeeper_mcp.tools.equipment_lookup.Open5eV1Client",
            return_value=mock_open5e_v1_client,
        ),
    ):
        result = await lookup_equipment(type="all", name="chain")

    # Should merge results from all three endpoints
    assert len(result) == 3
    names = {r["name"] for r in result}
    assert "Chain Whip" in names
    assert "Chain Mail" in names
    assert "Chain of Binding" in names
