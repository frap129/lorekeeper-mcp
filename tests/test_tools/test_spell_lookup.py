"""Tests for spell lookup tool."""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_lookup_spell_by_name(mock_open5e_v2_client):
    """Test looking up spell by exact name."""
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell

    with patch(
        "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_spell(name="Fireball")

    assert len(result) == 1
    assert result[0]["name"] == "Fireball"
    assert result[0]["level"] == 3
    assert result[0]["school"] == "evocation"
    mock_open5e_v2_client.get_spells.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_spell_with_filters(mock_open5e_v2_client):
    """Test spell lookup with multiple filters."""
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell

    with patch(
        "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        await lookup_spell(
            level=3,
            school="evocation",
            concentration=False,
            limit=10,
        )

    call_kwargs = mock_open5e_v2_client.get_spells.call_args[1]
    assert call_kwargs["level"] == 3
    assert call_kwargs["school"] == "evocation"
    assert call_kwargs["concentration"] is False
    assert call_kwargs["limit"] == 10


@pytest.mark.asyncio
async def test_lookup_spell_empty_results(mock_open5e_v2_client):
    """Test spell lookup with no results."""
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell

    mock_open5e_v2_client.get_spells.return_value = []

    with patch(
        "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_spell(name="NonexistentSpell")

    assert result == []


@pytest.mark.asyncio
async def test_lookup_spell_api_error(mock_open5e_v2_client):
    """Test spell lookup handles API errors gracefully."""
    from lorekeeper_mcp.api_clients.exceptions import ApiError
    from lorekeeper_mcp.tools.spell_lookup import clear_spell_cache, lookup_spell

    clear_spell_cache()
    mock_open5e_v2_client.get_spells.side_effect = ApiError("API unavailable")

    with (
        patch(
            "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
            return_value=mock_open5e_v2_client,
        ),
        pytest.raises(ApiError, match="API unavailable"),
    ):
        await lookup_spell(name="Fireball")


@pytest.mark.asyncio
async def test_lookup_spell_network_error(mock_open5e_v2_client):
    """Test spell lookup handles network errors."""
    from lorekeeper_mcp.api_clients.exceptions import NetworkError
    from lorekeeper_mcp.tools.spell_lookup import clear_spell_cache, lookup_spell

    clear_spell_cache()
    mock_open5e_v2_client.get_spells.side_effect = NetworkError("Connection timeout")

    with (
        patch(
            "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
            return_value=mock_open5e_v2_client,
        ),
        pytest.raises(NetworkError, match="Connection timeout"),
    ):
        await lookup_spell(name="Fireball")


@pytest.mark.asyncio
async def test_spell_search_parameter():
    """Test that spell lookup filters by name client-side"""
    from unittest.mock import AsyncMock, patch

    from lorekeeper_mcp.api_clients.models import Spell
    from lorekeeper_mcp.tools.spell_lookup import clear_spell_cache, lookup_spell

    clear_spell_cache()

    # Mock the API client to verify parameter usage
    with patch("lorekeeper_mcp.tools.spell_lookup.Open5eV2Client") as mock_client:
        mock_instance = AsyncMock()
        # Return some spell objects, with "Fireball" included
        mock_instance.get_spells.return_value = [
            Spell(
                name="Fireball",
                slug="fireball",
                level=3,
                school="evocation",
                casting_time="1 action",
                range="150 feet",
                components="V,S,M",
                material="a tiny ball of bat guano and sulfur",
                duration="Instantaneous",
                concentration=False,
                ritual=False,
                desc="A bright streak flashes...",
                document_url="https://example.com/fireball",
                higher_level="When you cast this spell...",
                damage_type=None,
            ),
            Spell(
                name="Fire Bolt",
                slug="fire-bolt",
                level=0,
                school="evocation",
                casting_time="1 action",
                range="120 feet",
                components="V,S",
                material=None,
                duration="Instantaneous",
                concentration=False,
                ritual=False,
                desc="You hurl a mote of fire...",
                document_url="https://example.com/fire-bolt",
                higher_level=None,
                damage_type=None,
            ),
        ]
        mock_client.return_value = mock_instance

        # Call the spell lookup function with name filter
        result = await lookup_spell(name="fireball")

        # Verify the API was called with enlarged limit for searching
        mock_instance.get_spells.assert_called_once()
        call_args = mock_instance.get_spells.call_args
        assert call_args.kwargs["limit"] == 20 * 11  # 220 for name search

        # Verify that results were filtered client-side by name
        assert len(result) == 1
        assert result[0]["name"] == "Fireball"
