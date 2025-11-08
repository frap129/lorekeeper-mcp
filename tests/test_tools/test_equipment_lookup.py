"""Tests for equipment lookup tool."""

from unittest.mock import AsyncMock, patch

import pytest

from lorekeeper_mcp.api_clients.exceptions import ParseError
from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment


@pytest.mark.asyncio
async def test_lookup_weapon(mock_open5e_v2_client):
    """Test looking up a weapon."""

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


@pytest.mark.asyncio
async def test_lookup_equipment_parse_error(mock_open5e_v2_client):
    """Test equipment lookup handles malformed responses."""

    mock_open5e_v2_client.get_weapons.side_effect = ParseError(
        "Invalid JSON response", raw_data="<html>Error</html>"
    )

    with (
        patch(
            "lorekeeper_mcp.tools.equipment_lookup.Open5eV2Client",
            return_value=mock_open5e_v2_client,
        ),
        pytest.raises(ParseError, match="Invalid JSON response"),
    ):
        await lookup_equipment(type="weapon", name="Sword")


@pytest.mark.asyncio
async def test_equipment_search_parameter():
    """Test that equipment lookup uses 'search' parameter instead of 'name'"""

    # Mock the API client to verify parameter usage
    with patch("lorekeeper_mcp.tools.equipment_lookup.Open5eV2Client") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get_weapons.return_value = []
        mock_client.return_value = mock_instance

        # Call the equipment lookup function
        await lookup_equipment(type="weapon", name="longsword")

        # Verify the API was called with search parameter, not name
        mock_instance.get_weapons.assert_called_once()
        call_args = mock_instance.get_weapons.call_args
        assert "search" in call_args.kwargs
        assert call_args.kwargs["search"] == "longsword"
