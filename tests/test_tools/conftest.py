"""Fixtures for tool tests."""

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.models import Creature, Spell
from lorekeeper_mcp.repositories.factory import RepositoryFactory


@pytest.fixture(autouse=True)
def cleanup_tool_contexts():
    """Clear all tool repository contexts after each test."""

    yield
    # Access _repository_context through sys.modules to get the actual module
    spell_mod = sys.modules.get("lorekeeper_mcp.tools.search_spell")
    creature_mod = sys.modules.get("lorekeeper_mcp.tools.search_creature")
    char_mod = sys.modules.get("lorekeeper_mcp.tools.search_character_option")
    equip_mod = sys.modules.get("lorekeeper_mcp.tools.search_equipment")
    rule_mod = sys.modules.get("lorekeeper_mcp.tools.search_rule")

    if spell_mod and hasattr(spell_mod, "_repository_context"):
        spell_mod._repository_context.clear()
    if creature_mod and hasattr(creature_mod, "_repository_context"):
        creature_mod._repository_context.clear()
    if char_mod and hasattr(char_mod, "_repository_context"):
        char_mod._repository_context.clear()
    if equip_mod and hasattr(equip_mod, "_repository_context"):
        equip_mod._repository_context.clear()
    if rule_mod and hasattr(rule_mod, "_repository_context"):
        rule_mod._repository_context.clear()

    # Clear the factory cache singleton to prevent test isolation issues
    RepositoryFactory._cache_instance = None


@pytest.fixture
def mock_spell_response():
    """Mock Open5e v2 spell response."""
    return {
        "count": 1,
        "results": [
            {
                "name": "Fireball",
                "level": 3,
                "school": "evocation",
                "casting_time": "1 action",
                "range": "150 feet",
                "components": "V,S,M",
                "material": "a tiny ball of bat guano and sulfur",
                "duration": "Instantaneous",
                "concentration": False,
                "ritual": False,
                "desc": "A bright streak flashes...",
                "higher_level": "When you cast this spell...",
                "document__slug": "srd",
            }
        ],
    }


@pytest.fixture
def mock_open5e_v1_client():
    """Mock Open5eV1Client."""
    # Convert dict response to Creature models for get_creatures
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
        challenge_rating="24",
        challenge_rating_decimal=24.0,
        strength=30,
        dexterity=10,
        constitution=29,
        intelligence=18,
        wisdom=15,
        charisma=23,
        speed={"walk": 40, "climb": 40, "fly": 80},
        actions=None,
        legendary_actions=None,
        special_abilities=None,
        document_url="https://example.com/dragon",
        document=None,
    )

    client = MagicMock()
    client.get_monsters = AsyncMock(return_value=[creature_obj])
    client.get_creatures = AsyncMock(return_value=[creature_obj])
    client.get_classes = AsyncMock(return_value={"count": 0, "results": []})
    client.get_races = AsyncMock(return_value={"count": 0, "results": []})
    client.get_magic_items = AsyncMock(return_value={"count": 0, "results": []})
    return client


@pytest.fixture
def mock_open5e_v2_client(mock_spell_response):
    """Mock Open5eV2Client."""
    # Convert dict response to Spell models for get_spells
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
        document=None,
    )

    client = MagicMock()
    client.get_spells = AsyncMock(return_value=[spell_obj])
    client.get_creatures = AsyncMock(return_value=[])
    client.get_backgrounds = AsyncMock(return_value=[])
    client.get_feats = AsyncMock(return_value=[])
    client.get_weapons = AsyncMock(return_value=[])
    client.get_armor = AsyncMock(return_value=[])
    client.get_conditions = AsyncMock(return_value=[])
    # Methods previously only in D&D 5e API client, now in Open5e v2
    client.get_rules = AsyncMock(return_value=[])
    client.get_damage_types_v2 = AsyncMock(return_value=[])
    client.get_weapon_properties_v2 = AsyncMock(return_value=[])
    client.get_skills_v2 = AsyncMock(return_value=[])
    client.get_abilities = AsyncMock(return_value=[])
    client.get_spell_schools_v2 = AsyncMock(return_value=[])
    client.get_languages_v2 = AsyncMock(return_value=[])
    client.get_alignments_v2 = AsyncMock(return_value=[])
    return client
