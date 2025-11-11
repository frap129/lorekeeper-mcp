"""Fixtures for tool tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.api_clients.models import Monster, Spell


@pytest.fixture(autouse=True)
def cleanup_tool_contexts():
    """Clear all tool repository contexts after each test."""
    from lorekeeper_mcp.tools import creature_lookup, spell_lookup

    yield
    spell_lookup._repository_context.clear()
    creature_lookup._repository_context.clear()


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
    # Convert dict response to Monster models for get_monsters
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

    client = MagicMock()
    client.get_monsters = AsyncMock(return_value=[monster_obj])
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
    )

    client = MagicMock()
    client.get_spells = AsyncMock(return_value=[spell_obj])
    client.get_backgrounds = AsyncMock(return_value=[])
    client.get_feats = AsyncMock(return_value=[])
    client.get_weapons = AsyncMock(return_value=[])
    client.get_armor = AsyncMock(return_value=[])
    client.get_conditions = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_dnd5e_client():
    """Mock Dnd5eApiClient."""
    client = MagicMock()
    client.get_rules = AsyncMock(return_value={"count": 0, "results": []})
    client.get_damage_types = AsyncMock(return_value={"count": 0, "results": []})
    client.get_weapon_properties = AsyncMock(return_value={"count": 0, "results": []})
    client.get_skills = AsyncMock(return_value={"count": 0, "results": []})
    client.get_ability_scores = AsyncMock(return_value={"count": 0, "results": []})
    client.get_magic_schools = AsyncMock(return_value={"count": 0, "results": []})
    client.get_languages = AsyncMock(return_value={"count": 0, "results": []})
    client.get_proficiencies = AsyncMock(return_value={"count": 0, "results": []})
    client.get_alignments = AsyncMock(return_value={"count": 0, "results": []})
    return client
