"""Tests for character option lookup tool."""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_lookup_class(mock_open5e_v1_client):
    """Test looking up a class."""
    from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

    mock_open5e_v1_client.get_classes.return_value = [{"name": "Paladin", "hit_dice": "1d10"}]

    with patch(
        "lorekeeper_mcp.tools.character_option_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_character_option(type="class", name="Paladin")

    assert len(result) == 1
    assert result[0]["name"] == "Paladin"
    mock_open5e_v1_client.get_classes.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_race(mock_open5e_v1_client):
    """Test looking up a race."""
    from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

    mock_open5e_v1_client.get_races.return_value = [{"name": "Elf", "speed": 30}]

    with patch(
        "lorekeeper_mcp.tools.character_option_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_character_option(type="race", name="Elf")

    assert len(result) == 1
    assert result[0]["name"] == "Elf"
    mock_open5e_v1_client.get_races.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_background(mock_open5e_v2_client):
    """Test looking up a background."""
    from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

    mock_open5e_v2_client.get_backgrounds.return_value = [{"name": "Acolyte"}]

    with patch(
        "lorekeeper_mcp.tools.character_option_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_character_option(type="background", name="Acolyte")

    assert len(result) == 1
    assert result[0]["name"] == "Acolyte"
    mock_open5e_v2_client.get_backgrounds.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_feat(mock_open5e_v2_client):
    """Test looking up a feat."""
    from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

    mock_open5e_v2_client.get_feats.return_value = [{"name": "Sharpshooter"}]

    with patch(
        "lorekeeper_mcp.tools.character_option_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_character_option(type="feat", name="Sharpshooter")

    assert len(result) == 1
    assert result[0]["name"] == "Sharpshooter"
    mock_open5e_v2_client.get_feats.assert_awaited_once()


@pytest.mark.asyncio
async def test_lookup_invalid_type():
    """Test invalid type parameter raises ValueError."""
    from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option

    with pytest.raises(ValueError, match="Invalid type"):
        await lookup_character_option(type="invalid-type")
