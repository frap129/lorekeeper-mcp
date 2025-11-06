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
    from lorekeeper_mcp.tools.spell_lookup import lookup_spell

    mock_open5e_v2_client.get_spells.side_effect = ApiError("API unavailable")

    with (
        patch(
            "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
            return_value=mock_open5e_v2_client,
        ),
        pytest.raises(ApiError, match="API unavailable"),
    ):
        await lookup_spell(name="Fireball")
