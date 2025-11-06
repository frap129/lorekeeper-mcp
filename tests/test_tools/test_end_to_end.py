"""End-to-end integration tests for MCP tools."""

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_full_spell_lookup_workflow(mock_open5e_v2_client, mock_spell_response):
    """Test complete spell lookup workflow."""
    from lorekeeper_mcp.tools import lookup_spell

    with patch(
        "lorekeeper_mcp.tools.spell_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_spell(name="Fireball", level=3, limit=5)

    assert isinstance(result, list)
    assert len(result) == 1
    spell = result[0]
    # Check if it's a Spell model object or dict
    if hasattr(spell, "name"):
        assert spell.name == "Fireball"
        assert spell.level == 3
        assert spell.desc is not None
    else:
        assert spell["name"] == "Fireball"
        assert spell["level"] == 3
        assert "desc" in spell


@pytest.mark.asyncio
async def test_full_creature_lookup_workflow(mock_open5e_v1_client, mock_spell_response):
    """Test complete creature lookup workflow."""
    from lorekeeper_mcp.tools import lookup_creature

    with patch(
        "lorekeeper_mcp.tools.creature_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_creature(name="Ancient Red Dragon", cr=24)

    assert isinstance(result, list)
    assert len(result) == 1
    creature = result[0]
    # Check if it's a Monster model object or dict
    if hasattr(creature, "name"):
        assert creature.name == "Ancient Red Dragon"
        assert creature.challenge_rating == "24"
        assert creature.hit_points == 546
        assert creature.strength == 30
    else:
        assert creature["name"] == "Ancient Red Dragon"
        assert creature["challenge_rating"] == "24"
        assert "hit_points" in creature
        assert "strength" in creature


@pytest.mark.asyncio
async def test_all_tools_callable():
    """Verify all tools can be imported and called."""
    from lorekeeper_mcp.tools import (
        lookup_character_option,
        lookup_creature,
        lookup_equipment,
        lookup_rule,
        lookup_spell,
    )

    # All should be async callables
    assert callable(lookup_spell)
    assert callable(lookup_creature)
    assert callable(lookup_character_option)
    assert callable(lookup_equipment)
    assert callable(lookup_rule)

    # Verify they're async
    assert inspect.iscoroutinefunction(lookup_spell)
    assert inspect.iscoroutinefunction(lookup_creature)
    assert inspect.iscoroutinefunction(lookup_character_option)
    assert inspect.iscoroutinefunction(lookup_equipment)
    assert inspect.iscoroutinefunction(lookup_rule)


@pytest.mark.asyncio
async def test_character_option_lookup_workflow(mock_open5e_v1_client):
    """Test character option lookup workflow."""
    from lorekeeper_mcp.tools import lookup_character_option

    mock_class = MagicMock()
    mock_class.name = "Wizard"
    mock_class.hit_dice = "1d6"
    mock_open5e_v1_client.get_classes.return_value = [mock_class]

    with patch(
        "lorekeeper_mcp.tools.character_option_lookup.Open5eV1Client",
        return_value=mock_open5e_v1_client,
    ):
        result = await lookup_character_option(type="class", name="Wizard")

    assert isinstance(result, list)
    assert len(result) == 1
    option = result[0]
    if hasattr(option, "name"):
        assert option.name == "Wizard"
    else:
        assert option["name"] == "Wizard"


@pytest.mark.asyncio
async def test_equipment_lookup_workflow(mock_open5e_v2_client):
    """Test equipment lookup workflow."""
    from lorekeeper_mcp.tools import lookup_equipment

    mock_weapon = MagicMock()
    mock_weapon.name = "Longsword"
    mock_weapon.damage_dice = "1d8"
    mock_weapon.model_dump.return_value = {
        "name": "Longsword",
        "damage_dice": "1d8",
    }
    mock_open5e_v2_client.get_weapons.return_value = [mock_weapon]

    with patch(
        "lorekeeper_mcp.tools.equipment_lookup.Open5eV2Client",
        return_value=mock_open5e_v2_client,
    ):
        result = await lookup_equipment(type="weapon", name="Longsword")

    assert isinstance(result, list)
    assert len(result) == 1
    equipment = result[0]
    assert equipment["name"] == "Longsword"
    assert equipment["damage_dice"] == "1d8"


@pytest.mark.asyncio
async def test_rule_lookup_workflow():
    """Test rule lookup workflow."""
    from lorekeeper_mcp.tools import lookup_rule

    mock_condition = MagicMock()
    mock_condition.name = "Grappled"
    mock_condition.desc = "A grappled creature..."

    mock_v2_client = MagicMock()
    mock_v2_client.get_conditions = AsyncMock(return_value=[mock_condition])

    with patch(
        "lorekeeper_mcp.tools.rule_lookup.Open5eV2Client",
        return_value=mock_v2_client,
    ):
        result = await lookup_rule(rule_type="condition", name="Grappled")

    assert isinstance(result, list)
    assert len(result) == 1
    rule = result[0]
    if hasattr(rule, "name"):
        assert rule.name == "Grappled"
    else:
        assert rule["name"] == "Grappled"
