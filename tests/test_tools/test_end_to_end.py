"""End-to-end integration tests for MCP tools."""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.models import Creature, Spell
from lorekeeper_mcp.tools import (
    search_character_option,
    search_creature,
    search_equipment,
    search_rule,
    search_spell,
)
from lorekeeper_mcp.tools import (
    search_character_option as search_character_option_module,
)
from lorekeeper_mcp.tools import (
    search_creature as search_creature_module,
)
from lorekeeper_mcp.tools import (
    search_equipment as search_equipment_module,
)
from lorekeeper_mcp.tools import (
    search_rule as search_rule_module,
)
from lorekeeper_mcp.tools import (
    search_spell as search_spell_module,
)


@pytest.mark.asyncio
async def test_full_spell_search_workflow():
    """Test complete spell search workflow."""
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

    # Use context-based injection for spell search
    search_spell_module._repository_context["repository"] = mock_spell_repository
    try:
        result = await search_spell(name="Fireball", level=3, limit=5)
    finally:
        # Clean up context
        if "repository" in search_spell_module._repository_context:
            del search_spell_module._repository_context["repository"]

    assert isinstance(result, list)
    assert len(result) == 1
    spell = result[0]
    # Result should be a dict since tools call model_dump()
    assert spell["name"] == "Fireball"
    assert spell["level"] == 3
    assert "desc" in spell


@pytest.mark.asyncio
async def test_full_creature_search_workflow():
    """Test complete creature search workflow."""
    # Create a mock creature repository that returns Creature objects
    creature_obj = Creature(
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
    mock_creature_repository.search = AsyncMock(return_value=[creature_obj])

    # Use context-based injection for creature search
    search_creature_module._repository_context["repository"] = mock_creature_repository
    try:
        result = await search_creature(name="Ancient Red Dragon", cr=24)
    finally:
        # Clean up context
        if "repository" in search_creature_module._repository_context:
            del search_creature_module._repository_context["repository"]

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
    assert callable(search_spell)
    assert callable(search_creature)
    assert callable(search_character_option)
    assert callable(search_equipment)
    assert callable(search_rule)

    # Verify they're async
    assert inspect.iscoroutinefunction(search_spell)
    assert inspect.iscoroutinefunction(search_creature)
    assert inspect.iscoroutinefunction(search_character_option)
    assert inspect.iscoroutinefunction(search_equipment)
    assert inspect.iscoroutinefunction(search_rule)


@pytest.mark.asyncio
async def test_character_option_search_workflow():
    """Test character option search workflow."""

    # Create a mock character option repository
    # The repository returns dicts directly from search method
    mock_character_option_repository = MagicMock()
    mock_character_option_repository.search = AsyncMock(
        return_value=[{"name": "Wizard", "hit_dice": "1d6"}]
    )

    # Use repository context pattern
    search_character_option_module._repository_context["repository"] = (
        mock_character_option_repository
    )

    try:
        result = await search_character_option(
            type="class",
            name="Wizard",
        )

        assert isinstance(result, list)
        assert len(result) == 1
        option = result[0]
        assert option["name"] == "Wizard"
    finally:
        # Clean up context
        if "repository" in search_character_option_module._repository_context:
            del search_character_option_module._repository_context["repository"]


@pytest.mark.asyncio
async def test_equipment_search_workflow():
    """Test equipment search workflow."""
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

    # Set up context injection
    search_equipment_module._repository_context["repository"] = mock_equipment_repository

    result = await search_equipment(
        type="weapon",
        name="Longsword",
    )

    # Clean up context
    if "repository" in search_equipment_module._repository_context:
        del search_equipment_module._repository_context["repository"]

    assert isinstance(result, list)
    assert len(result) == 1
    equipment = result[0]
    assert equipment["name"] == "Longsword"
    assert equipment["damage_dice"] == "1d8"


@pytest.mark.asyncio
async def test_rule_search_workflow():
    """Test rule search workflow."""

    mock_repository = MagicMock()
    mock_repository.search = AsyncMock(
        return_value=[{"name": "Grappled", "desc": "A grappled creature..."}]
    )

    # Set up context injection
    search_rule_module._repository_context["repository"] = mock_repository

    result = await search_rule(rule_type="condition", name="Grappled")

    # Clean up context
    if "repository" in search_rule_module._repository_context:
        del search_rule_module._repository_context["repository"]

    assert isinstance(result, list)
    assert len(result) == 1
    rule = result[0]
    assert rule["name"] == "Grappled"
