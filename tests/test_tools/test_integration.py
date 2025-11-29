"""Integration tests for MCP tools with real repositories and database cache.

These tests verify:
1. Tools work with real repositories (not mocks)
2. All 5 tools function correctly
3. Database cache persists data
4. Tool registration and schemas are valid
"""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.cache.sqlite import SQLiteCache
from lorekeeper_mcp.repositories.factory import RepositoryFactory
from lorekeeper_mcp.server import mcp
from lorekeeper_mcp.tools.character_option_lookup import lookup_character_option
from lorekeeper_mcp.tools.creature_lookup import lookup_creature
from lorekeeper_mcp.tools.equipment_lookup import lookup_equipment
from lorekeeper_mcp.tools.rule_lookup import lookup_rule
from lorekeeper_mcp.tools.spell_lookup import lookup_spell

# ============================================================================
# Tool Registration and Validation Tests
# ============================================================================


@pytest.mark.integration
def test_all_tools_registered():
    """Verify all 5 tools are registered with FastMCP."""
    tools = mcp._tool_manager._tools
    tool_names = set(tools.keys())

    expected_tools = {
        "lookup_spell",
        "lookup_creature",
        "lookup_character_option",
        "lookup_equipment",
        "lookup_rule",
    }

    assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"


@pytest.mark.integration
def test_tool_schemas_valid():
    """Verify tool schemas are properly defined."""
    tools = mcp._tool_manager._tools

    # Check lookup_spell schema
    spell_tool = tools.get("lookup_spell")
    assert spell_tool is not None
    assert "name" in spell_tool.parameters["properties"]
    assert "level" in spell_tool.parameters["properties"]
    assert "limit" in spell_tool.parameters["properties"]

    # Check lookup_creature schema
    creature_tool = tools.get("lookup_creature")
    assert creature_tool is not None
    assert "cr" in creature_tool.parameters["properties"]

    # Check lookup_character_option schema
    char_tool = tools.get("lookup_character_option")
    assert char_tool is not None
    assert "type" in char_tool.parameters["required"]

    # Check lookup_equipment schema
    equip_tool = tools.get("lookup_equipment")
    assert equip_tool is not None

    # Check lookup_rule schema
    rule_tool = tools.get("lookup_rule")
    assert rule_tool is not None
    assert "rule_type" in rule_tool.parameters["required"]


# ============================================================================
# Spell Lookup Integration Tests
# ============================================================================


@pytest.mark.integration
@respx.mock
async def test_spell_lookup_basic(test_db):
    """Test basic spell lookup with real repository."""
    # Mock the API response
    spell_response = {
        "results": [
            {
                "name": "Fireball",
                "slug": "fireball",
                "level": 3,
                "school": "Evocation",
                "casting_time": "1 action",
                "range": "150 feet",
                "components": "V, S, M",
                "material": "a tiny ball of bat guano and sulfur",
                "duration": "Instantaneous",
                "concentration": False,
                "ritual": False,
                "desc": "A bright streak flashes from pointing...",
                "document_url": "https://example.com/fireball",
            }
        ]
    }

    respx.get("https://api.open5e.com/v2/spells/?").mock(
        return_value=httpx.Response(200, json=spell_response)
    )

    # Use default repository (not mocked)
    result = await lookup_spell(name="fireball")
    # Verify result structure
    assert isinstance(result, list)
    if len(result) > 0:
        assert "name" in result[0]
        assert "level" in result[0]


@pytest.mark.integration
@respx.mock
async def test_spell_lookup_by_level(test_db):
    """Test spell lookup filtered by level."""
    spell_response = {
        "results": [
            {
                "name": "Magic Missile",
                "slug": "magic-missile",
                "level": 1,
                "school": "Evocation",
                "casting_time": "1 action",
                "range": "120 feet",
                "components": "V, S",
                "material": None,
                "duration": "Instantaneous",
                "concentration": False,
                "ritual": False,
                "desc": "You hurl magical energy...",
                "document_url": "https://example.com/magic-missile",
            }
        ]
    }

    respx.get("https://api.open5e.com/v2/spells/?").mock(
        return_value=httpx.Response(200, json=spell_response)
    )

    # Test that tool can be called with level filter
    result = await lookup_spell(level=1)
    assert isinstance(result, list)


# ============================================================================
# Creature Lookup Integration Tests
# ============================================================================


@pytest.mark.integration
@respx.mock
async def test_creature_lookup_basic(test_db):
    """Test basic creature lookup with real repository."""
    monster_response = {
        "results": [
            {
                "name": "Ancient Red Dragon",
                "slug": "ancient-red-dragon",
                "desc": "A massive red dragon...",
                "size": "Gargantuan",
                "type": "dragon",
                "alignment": "chaotic evil",
                "armor_class": 22,
                "hit_points": 546,
                "hit_dice": "28d20+252",
                "strength": 30,
                "dexterity": 10,
                "constitution": 29,
                "intelligence": 18,
                "wisdom": 15,
                "charisma": 23,
                "challenge_rating": "24",
                "speed": {"walk": 40, "climb": 40, "fly": 80},
                "document_url": "https://example.com/dragon",
            }
        ]
    }

    respx.get("https://api.open5e.com/v2/creatures/?limit=20&name__icontains=dragon").mock(
        return_value=httpx.Response(200, json=monster_response)
    )

    # Test basic creature lookup
    result = await lookup_creature(name="dragon")
    assert isinstance(result, list)
    if len(result) > 0:
        assert "name" in result[0]
        assert "hit_points" in result[0]


@pytest.mark.integration
@respx.mock
async def test_creature_lookup_by_cr(test_db):
    """Test creature lookup filtered by challenge rating."""
    monster_response = {
        "results": [
            {
                "name": "Lich",
                "slug": "lich",
                "desc": "A lich is an undead wizard...",
                "size": "Medium",
                "type": "undead",
                "alignment": "any evil",
                "armor_class": 17,
                "hit_points": 135,
                "hit_dice": "10d8+40",
                "strength": 11,
                "dexterity": 16,
                "constitution": 16,
                "intelligence": 20,
                "wisdom": 14,
                "charisma": 16,
                "challenge_rating": "21",
                "speed": {"walk": 0, "fly": 0},
                "document_url": "https://example.com/lich",
            }
        ]
    }

    respx.get("https://api.open5e.com/v2/creatures/?limit=20&challenge_rating_decimal=21.0").mock(
        return_value=httpx.Response(200, json=monster_response)
    )

    # Test that tool can be called with CR filter
    result = await lookup_creature(cr=21.0)
    assert isinstance(result, list)


# ============================================================================
# Equipment Lookup Integration Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.skip(
    reason="Equipment repository requires D&D 5e API which is being removed. "
    "Will be updated when equipment repository is refactored for Open5e API."
)
@respx.mock
async def test_equipment_lookup_weapons(test_db):
    """Test equipment lookup for weapons."""
    result = await lookup_equipment(name="longsword", type="weapon")
    assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.skip(
    reason="Equipment repository requires D&D 5e API which is being removed. "
    "Will be updated when equipment repository is refactored for Open5e API."
)
@respx.mock
async def test_equipment_lookup_armor(test_db):
    """Test equipment lookup for armor."""
    result = await lookup_equipment(name="plate", type="armor")
    assert isinstance(result, list)


# ============================================================================
# Character Option Lookup Integration Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.skip(
    reason="Character option repository requires D&D 5e API which is being removed. "
    "Will be updated when character option repository is refactored for Open5e API."
)
@respx.mock
async def test_character_option_lookup_class(test_db):
    """Test character option lookup for classes."""
    result = await lookup_character_option(type="class", name="barbarian")
    assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.skip(
    reason="Character option repository requires D&D 5e API which is being removed. "
    "Will be updated when character option repository is refactored for Open5e API."
)
@respx.mock
async def test_character_option_lookup_race(test_db):
    """Test character option lookup for races."""
    result = await lookup_character_option(type="race", name="dwarf")
    assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.skip(
    reason="Rule repository requires D&D 5e API which is being removed. "
    "Will be updated when rule repository is refactored for Open5e API."
)
@respx.mock
async def test_rule_lookup_ability_scores_with_cache(test_db):
    """Test ability score lookup with cache support."""
    result1 = await lookup_rule(rule_type="ability-score", name="Strength")
    assert len(result1) == 1
    assert result1[0]["name"] == "Strength"


# ============================================================================
# Database Cache Tests
# ============================================================================
# Rule Lookup Integration Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.skip(
    reason="Rule repository requires D&D 5e API which is being removed. "
    "Will be updated when rule repository is refactored for Open5e API."
)
@respx.mock
async def test_rule_lookup_condition(test_db):
    """Test rule lookup for conditions."""
    result = await lookup_rule(rule_type="condition", name="blinded")
    assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.skip(
    reason="Rule repository requires D&D 5e API which is being removed. "
    "Will be updated when rule repository is refactored for Open5e API."
)
@respx.mock
async def test_rule_lookup_damage_type(test_db):
    """Test rule lookup for damage types."""
    result = await lookup_rule(rule_type="damage-type", name="fire")
    assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.skip(
    reason="Rule repository requires D&D 5e API which is being removed. "
    "Will be updated when rule repository is refactored for Open5e API."
)
@respx.mock
async def test_rule_lookup_skill(test_db):
    """Test rule lookup for skills."""
    result = await lookup_rule(rule_type="skill", name="acrobatics")
    assert isinstance(result, list)


# ============================================================================
# Database Cache Tests
# ============================================================================


@pytest.mark.integration
async def test_cache_persistence(test_db):
    """Test that cache persists data correctly across operations."""
    cache = SQLiteCache(db_path=str(test_db))

    test_spell = {
        "name": "Test Spell",
        "slug": "test-spell",
        "level": 1,
        "school": "abjuration",
        "casting_time": "1 action",
        "range": "Self",
        "components": "V",
        "material": None,
        "duration": "1 minute",
        "concentration": False,
        "ritual": False,
        "desc": "A test spell",
        "document_url": "https://example.com",
        "higher_level": None,
        "damage_type": None,
    }

    # Store entity
    stored = await cache.store_entities([test_spell], "spells")
    assert stored > 0

    # Retrieve entity by indexed field (level)
    retrieved = await cache.get_entities("spells", level=1)
    assert len(retrieved) > 0
    assert retrieved[0]["name"] == "Test Spell"


@pytest.mark.integration
async def test_cache_filtering(test_db):
    """Test cache filtering capabilities."""
    cache = SQLiteCache(db_path=str(test_db))

    spells = [
        {
            "name": "Fireball",
            "slug": "fireball",
            "level": 3,
            "school": "evocation",
            "casting_time": "1 action",
            "range": "150 feet",
            "components": "V, S, M",
            "material": "a tiny ball of bat guano and sulfur",
            "duration": "Instantaneous",
            "concentration": False,
            "ritual": False,
            "desc": "A bright streak flashes...",
            "document_url": "https://example.com",
            "higher_level": None,
            "damage_type": None,
        },
        {
            "name": "Magic Missile",
            "slug": "magic-missile",
            "level": 1,
            "school": "evocation",
            "casting_time": "1 action",
            "range": "120 feet",
            "components": "V, S",
            "material": None,
            "duration": "Instantaneous",
            "concentration": False,
            "ritual": False,
            "desc": "You hurl magical energy...",
            "document_url": "https://example.com",
            "higher_level": None,
            "damage_type": None,
        },
    ]

    # Store spells
    stored = await cache.store_entities(spells, "spells")
    assert stored == 2

    # Filter by level
    level_1_spells = await cache.get_entities("spells", level=1)
    assert len(level_1_spells) > 0
    assert level_1_spells[0]["level"] == 1

    # Filter by school
    evocation_spells = await cache.get_entities("spells", school="evocation")
    assert len(evocation_spells) >= 2


@pytest.mark.integration
async def test_repository_factory_creates_instances():
    """Test that repository factory creates properly configured instances."""
    v1_client = Open5eV1Client()
    v2_client = Open5eV2Client()

    try:
        # Create repositories that support Open5e API
        spell_repo = RepositoryFactory.create_spell_repository(client=v2_client)
        creature_repo = RepositoryFactory.create_creature_repository(client=v1_client)

        # Verify repositories are created
        assert spell_repo is not None
        assert creature_repo is not None

        # Verify repositories have required methods
        assert hasattr(spell_repo, "search")
        assert hasattr(spell_repo, "get_all")
        assert hasattr(creature_repo, "search")
    finally:
        await v1_client.close()
        await v2_client.close()
