"""Tests for creature lookup tool."""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_lookup_creature_by_name(mock_open5e_v1_client, mock_creature_response):
    """Test looking up creature by exact name."""
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_creature(name="Ancient Red Dragon")

    assert len(result) == 1
    assert result[0]["name"] == "Ancient Red Dragon"
    assert result[0]["challenge_rating"] == "24"
    mock_open5e_v1_client.get_monsters.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_creature_by_cr_and_type(mock_open5e_v1_client):
    """Test creature lookup with CR and type filters."""
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        await lookup_creature(cr=5, type="undead", limit=15)

    call_kwargs = mock_open5e_v1_client.get_monsters.call_args[1]
    assert call_kwargs["cr"] == 5
    assert call_kwargs["type"] == "undead"
    assert call_kwargs["limit"] == 15


@pytest.mark.asyncio
async def test_lookup_creature_fractional_cr(mock_open5e_v1_client):
    """Test creature lookup with fractional CR."""
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        await lookup_creature(cr=0.25)

    call_kwargs = mock_open5e_v1_client.get_monsters.call_args[1]
    assert call_kwargs["cr"] == 0.25


@pytest.mark.asyncio
async def test_lookup_creature_cr_range(mock_open5e_v1_client):
    """Test creature lookup with CR range."""
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        await lookup_creature(cr_min=1, cr_max=3)

    call_kwargs = mock_open5e_v1_client.get_monsters.call_args[1]
    assert call_kwargs["cr_min"] == 1
    assert call_kwargs["cr_max"] == 3


@pytest.mark.asyncio
async def test_lookup_creature_empty_results(mock_open5e_v1_client):
    """Test creature lookup with no results."""
    from lorekeeper_mcp.tools.creature_lookup import lookup_creature

    mock_open5e_v1_client.get_monsters.return_value = []

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_creature(name="Nonexistent")

    assert result == []
