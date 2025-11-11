"""End-to-end integration tests for MCP tools."""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.models import Monster, Spell
from lorekeeper_mcp.tools import (
    lookup_character_option,
    lookup_creature,
    lookup_equipment,
    lookup_rule,
    lookup_spell,
)


@pytest.mark.asyncio
async def test_full_spell_lookup_workflow():
    """Test complete spell lookup workflow."""
    # Create a mock spell repository that returns Spell objects
    spell_obj = Spell(
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
    )

    mock_spell_repository = MagicMock()
    mock_spell_repository.search = AsyncMock(return_value=[spell_obj])

    result = await lookup_spell(name="Fireball", level=3, limit=5, repository=mock_spell_repository)

    assert isinstance(result, list)
    assert len(result) == 1
    spell = result[0]
    # Result should be a dict since tools call model_dump()
    assert spell["name"] == "Fireball"
    assert spell["level"] == 3
    assert "desc" in spell


@pytest.mark.asyncio
async def test_full_creature_lookup_workflow():
    """Test complete creature lookup workflow."""
    # Create a mock creature repository that returns Monster objects
    monster_obj = Monster(
        name="Ancient Red Dragon",
        slug="ancient-red-dragon",
        desc="A large red dragon",
        size="Gargantuan",
        type="dragon",
        alignment="chaotic evil",
        armor_class=22,
        hit_points=546,
        hit_dice="28d20+252",
        strength=30,
        dexterity=10,
        constitution=29,
        intelligence=18,
        wisdom=15,
        charisma=23,
        challenge_rating="24",
        speed={"walk": 40, "climb": 40, "fly": 80},
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        document_url="https://example.com/dragon",
    )

    mock_creature_repository = MagicMock()
    mock_creature_repository.search = AsyncMock(return_value=[monster_obj])

    result = await lookup_creature(
        name="Ancient Red Dragon", cr=24, repository=mock_creature_repository
    )

    assert isinstance(result, list)
    assert len(result) == 1
    creature = result[0]
    # Result should be a dict since tools call model_dump()
    assert creature["name"] == "Ancient Red Dragon"
    assert creature["challenge_rating"] == "24"
    assert "hit_points" in creature
    assert "strength" in creature


@pytest.mark.asyncio
async def test_all_tools_callable():
    """Verify all tools can be imported and called."""

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
async def test_character_option_lookup_workflow():
    """Test character option lookup workflow."""
    # Create a mock character option repository
    # The repository returns dicts directly from search method
    mock_character_option_repository = MagicMock()
    mock_character_option_repository.search = AsyncMock(
        return_value=[{"name": "Wizard", "hit_dice": "1d6"}]
    )

    result = await lookup_character_option(
        type="class",
        name="Wizard",
        repository=mock_character_option_repository,
    )

    assert isinstance(result, list)
    assert len(result) == 1
    option = result[0]
    assert option["name"] == "Wizard"


@pytest.mark.asyncio
async def test_equipment_lookup_workflow():
    """Test equipment lookup workflow."""
    # Create mock equipment objects with model_dump method
    mock_weapon = MagicMock()
    mock_weapon.name = "Longsword"
    mock_weapon.damage_dice = "1d8"
    mock_weapon.model_dump.return_value = {
        "name": "Longsword",
        "damage_dice": "1d8",
    }

    mock_equipment_repository = MagicMock()
    mock_equipment_repository.search = AsyncMock(return_value=[mock_weapon])

    result = await lookup_equipment(
        type="weapon",
        name="Longsword",
        repository=mock_equipment_repository,
    )

    assert isinstance(result, list)
    assert len(result) == 1
    equipment = result[0]
    assert equipment["name"] == "Longsword"
    assert equipment["damage_dice"] == "1d8"


@pytest.mark.asyncio
async def test_rule_lookup_workflow():
    """Test rule lookup workflow."""

    mock_repository = MagicMock()
    mock_repository.search = AsyncMock(
        return_value=[{"name": "Grappled", "desc": "A grappled creature..."}]
    )

    result = await lookup_rule(rule_type="condition", name="Grappled", repository=mock_repository)

    assert isinstance(result, list)
    assert len(result) == 1
    rule = result[0]
    assert rule["name"] == "Grappled"
