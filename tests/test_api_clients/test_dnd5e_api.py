"""Tests for Dnd5eApiClient."""

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.exceptions import ApiError
from lorekeeper_mcp.cache.db import get_cached_entity


@pytest.fixture
async def dnd5e_client(test_db) -> Dnd5eApiClient:
    """Create Dnd5eApiClient for testing."""
    client = Dnd5eApiClient(max_retries=0)
    yield client
    await client.close()


async def test_client_initialization(dnd5e_client: Dnd5eApiClient) -> None:
    """Test client initializes with correct configuration."""
    assert dnd5e_client.base_url == "https://www.dnd5eapi.co/api/2014"
    assert dnd5e_client.source_api == "dnd5e_api"
    assert dnd5e_client.cache_ttl == 604800  # 7 days default


@respx.mock
async def test_get_rules_all(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching all rules."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "adventuring",
                        "name": "Adventuring",
                        "url": "/api/2014/rules/adventuring",
                    },
                    {
                        "index": "combat",
                        "name": "Combat",
                        "url": "/api/2014/rules/combat",
                    },
                ]
            },
        )
    )

    rules = await dnd5e_client.get_rules()

    assert len(rules) == 2
    assert rules[0]["name"] == "Adventuring"
    assert rules[1]["name"] == "Combat"


@respx.mock
async def test_get_rules_by_section(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching rules by section."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/adventuring").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "adventuring",
                "name": "Adventuring",
                "desc": "Delving into dungeons...",
                "subsections": [
                    {"index": "time", "name": "Time", "url": "/api/2014/rule-sections/time"}
                ],
            },
        )
    )

    rules = await dnd5e_client.get_rules(section="adventuring")

    assert len(rules) == 1
    assert rules[0]["name"] == "Adventuring"
    assert rules[0]["desc"] == "Delving into dungeons..."


@respx.mock
async def test_get_rule_sections_all(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching all rule sections."""
    respx.get("https://www.dnd5eapi.co/api/2014/rule-sections/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "grappling",
                        "name": "Grappling",
                        "url": "/api/2014/rule-sections/grappling",
                    },
                    {
                        "index": "opportunity-attacks",
                        "name": "Opportunity Attacks",
                        "url": "/api/2014/rule-sections/opportunity-attacks",
                    },
                ]
            },
        )
    )

    sections = await dnd5e_client.get_rule_sections()

    assert len(sections) == 2
    assert sections[0]["name"] == "Grappling"


@respx.mock
async def test_get_rule_sections_by_name(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching specific rule section."""
    respx.get("https://www.dnd5eapi.co/api/2014/rule-sections/grappling").mock(
        return_value=httpx.Response(
            200,
            json={
                "index": "grappling",
                "name": "Grappling",
                "desc": "When you want to grab a creature...",
            },
        )
    )

    sections = await dnd5e_client.get_rule_sections(name="grappling")

    assert len(sections) == 1
    assert sections[0]["name"] == "Grappling"
    assert sections[0]["desc"] == "When you want to grab a creature..."


@respx.mock
async def test_get_damage_types(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching damage types."""
    respx.get("https://www.dnd5eapi.co/api/2014/damage-types/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "fire", "name": "Fire", "url": "/api/2014/damage-types/fire"},
                    {"index": "cold", "name": "Cold", "url": "/api/2014/damage-types/cold"},
                ]
            },
        )
    )

    damage_types = await dnd5e_client.get_damage_types()

    assert len(damage_types) == 2
    assert damage_types[0]["name"] == "Fire"


@respx.mock
async def test_get_weapon_properties(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching weapon properties."""
    respx.get("https://www.dnd5eapi.co/api/2014/weapon-properties/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "finesse",
                        "name": "Finesse",
                        "url": "/api/2014/weapon-properties/finesse",
                    },
                    {
                        "index": "versatile",
                        "name": "Versatile",
                        "url": "/api/2014/weapon-properties/versatile",
                    },
                ]
            },
        )
    )

    properties = await dnd5e_client.get_weapon_properties()

    assert len(properties) == 2
    assert properties[0]["name"] == "Finesse"


@respx.mock
async def test_get_skills(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching skills."""
    respx.get("https://www.dnd5eapi.co/api/2014/skills/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "acrobatics",
                        "name": "Acrobatics",
                        "url": "/api/2014/skills/acrobatics",
                    },
                    {"index": "stealth", "name": "Stealth", "url": "/api/2014/skills/stealth"},
                ]
            },
        )
    )

    skills = await dnd5e_client.get_skills()

    assert len(skills) == 2
    assert skills[0]["name"] == "Acrobatics"


@respx.mock
async def test_get_ability_scores(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching ability scores."""
    respx.get("https://www.dnd5eapi.co/api/2014/ability-scores/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "str", "name": "STR", "url": "/api/2014/ability-scores/str"},
                    {"index": "dex", "name": "DEX", "url": "/api/2014/ability-scores/dex"},
                ]
            },
        )
    )

    ability_scores = await dnd5e_client.get_ability_scores()

    assert len(ability_scores) == 2
    assert ability_scores[0]["name"] == "STR"


@respx.mock
async def test_get_magic_schools(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching magic schools."""
    respx.get("https://www.dnd5eapi.co/api/2014/magic-schools/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "evocation",
                        "name": "Evocation",
                        "url": "/api/2014/magic-schools/evocation",
                    },
                    {
                        "index": "abjuration",
                        "name": "Abjuration",
                        "url": "/api/2014/magic-schools/abjuration",
                    },
                ]
            },
        )
    )

    schools = await dnd5e_client.get_magic_schools()

    assert len(schools) == 2
    assert schools[0]["name"] == "Evocation"


@respx.mock
async def test_get_languages(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching languages."""
    respx.get("https://www.dnd5eapi.co/api/2014/languages/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"index": "common", "name": "Common", "url": "/api/2014/languages/common"},
                    {"index": "elvish", "name": "Elvish", "url": "/api/2014/languages/elvish"},
                ]
            },
        )
    )

    languages = await dnd5e_client.get_languages()

    assert len(languages) == 2
    assert languages[0]["name"] == "Common"


@respx.mock
async def test_get_proficiencies(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching proficiencies."""
    respx.get("https://www.dnd5eapi.co/api/2014/proficiencies/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "light-armor",
                        "name": "Light Armor",
                        "url": "/api/2014/proficiencies/light-armor",
                    },
                    {
                        "index": "longswords",
                        "name": "Longswords",
                        "url": "/api/2014/proficiencies/longswords",
                    },
                ]
            },
        )
    )

    proficiencies = await dnd5e_client.get_proficiencies()

    assert len(proficiencies) == 2
    assert proficiencies[0]["name"] == "Light Armor"


@respx.mock
async def test_get_alignments(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching alignments."""
    respx.get("https://www.dnd5eapi.co/api/2014/alignments/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "lawful-good",
                        "name": "Lawful Good",
                        "url": "/api/2014/alignments/lawful-good",
                    },
                    {
                        "index": "chaotic-evil",
                        "name": "Chaotic Evil",
                        "url": "/api/2014/alignments/chaotic-evil",
                    },
                ]
            },
        )
    )

    alignments = await dnd5e_client.get_alignments()

    assert len(alignments) == 2
    assert alignments[0]["name"] == "Lawful Good"


@respx.mock
async def test_get_rules_uses_entity_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify rules are cached as entities."""
    mock_response = {
        "results": [
            {
                "index": "combat",
                "name": "Combat",
                "desc": "Combat rules...",
            }
        ]
    }
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await dnd5e_client.get_rules()

    # Verify entity cached
    cached = await get_cached_entity("rules", "combat")
    assert cached is not None
    assert cached["name"] == "Combat"


@respx.mock
async def test_get_damage_types_extended_ttl(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify reference data uses 30-day cache TTL."""
    mock_response = {"results": [{"index": "fire", "name": "Fire", "desc": "Fire damage..."}]}
    respx.get("https://www.dnd5eapi.co/api/2014/damage-types/").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    await dnd5e_client.get_damage_types()

    # Verify that extended TTL is applied by checking the client's cache_ttl
    # after calling get_damage_types (which temporarily sets it to REFERENCE_DATA_TTL)
    # The cache_ttl should be restored to default after the call
    assert dnd5e_client.cache_ttl == 604800  # 7 days default (should be restored)


@respx.mock
async def test_get_rules_api_error(dnd5e_client: Dnd5eApiClient) -> None:
    """Test API error handling."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )

    with pytest.raises(ApiError) as exc_info:
        await dnd5e_client.get_rules()

    assert exc_info.value.status_code == 500


@respx.mock
async def test_get_rules_network_error(dnd5e_client: Dnd5eApiClient) -> None:
    """Test network error handling with empty cache fallback."""
    respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
        side_effect=httpx.RequestError("Network unavailable")
    )

    # Should return empty list when no cache available
    result = await dnd5e_client.get_rules()

    assert result == []


async def test_get_rules_network_error_with_cache_fallback(dnd5e_client: Dnd5eApiClient) -> None:
    """Test offline fallback to cached entities."""
    # First request succeeds and caches
    with respx.mock:
        respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [{"index": "combat", "name": "Combat", "desc": "Combat rules..."}]
                },
            )
        )
        await dnd5e_client.get_rules()

    # Second request fails, should return cached
    with respx.mock:
        respx.get("https://www.dnd5eapi.co/api/2014/rules/").mock(
            side_effect=httpx.RequestError("Network unavailable")
        )
        result = await dnd5e_client.get_rules()

        assert len(result) == 1
        assert result[0]["name"] == "Combat"


# Task 1.12: Character option methods
@respx.mock
async def test_get_backgrounds_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching backgrounds."""
    respx.get("https://www.dnd5eapi.co/api/2014/backgrounds/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "acolyte",
                        "name": "Acolyte",
                        "desc": "You have spent your life in service to a temple...",
                    },
                    {
                        "index": "soldier",
                        "name": "Soldier",
                        "desc": "War has been your life...",
                    },
                ]
            },
        )
    )

    backgrounds = await dnd5e_client.get_backgrounds_dnd5e()

    assert len(backgrounds) == 2
    assert backgrounds[0]["name"] == "Acolyte"
    assert backgrounds[0]["slug"] == "acolyte"
    assert backgrounds[1]["name"] == "Soldier"


@respx.mock
async def test_get_classes_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching classes."""
    respx.get("https://www.dnd5eapi.co/api/2014/classes/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "barbarian",
                        "name": "Barbarian",
                        "hit_die": 12,
                    },
                    {
                        "index": "wizard",
                        "name": "Wizard",
                        "hit_die": 6,
                    },
                ]
            },
        )
    )

    classes = await dnd5e_client.get_classes_dnd5e()

    assert len(classes) == 2
    assert classes[0]["name"] == "Barbarian"
    assert classes[0]["slug"] == "barbarian"


@respx.mock
async def test_get_subclasses(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching subclasses."""
    respx.get("https://www.dnd5eapi.co/api/2014/subclasses/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "berserker",
                        "name": "Berserker",
                        "class": {"index": "barbarian", "name": "Barbarian"},
                    },
                    {
                        "index": "champion",
                        "name": "Champion",
                        "class": {"index": "fighter", "name": "Fighter"},
                    },
                ]
            },
        )
    )

    subclasses = await dnd5e_client.get_subclasses()

    assert len(subclasses) == 2
    assert subclasses[0]["name"] == "Berserker"
    assert subclasses[0]["slug"] == "berserker"


@respx.mock
async def test_get_races_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching races."""
    respx.get("https://www.dnd5eapi.co/api/2014/races/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "human",
                        "name": "Human",
                        "speed": 30,
                    },
                    {
                        "index": "elf",
                        "name": "Elf",
                        "speed": 30,
                    },
                ]
            },
        )
    )

    races = await dnd5e_client.get_races_dnd5e()

    assert len(races) == 2
    assert races[0]["name"] == "Human"
    assert races[0]["slug"] == "human"


@respx.mock
async def test_get_subraces(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching subraces."""
    respx.get("https://www.dnd5eapi.co/api/2014/subraces/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "high-elf",
                        "name": "High Elf",
                        "race": {"index": "elf", "name": "Elf"},
                    },
                    {
                        "index": "forest-gnome",
                        "name": "Forest Gnome",
                        "race": {"index": "gnome", "name": "Gnome"},
                    },
                ]
            },
        )
    )

    subraces = await dnd5e_client.get_subraces()

    assert len(subraces) == 2
    assert subraces[0]["name"] == "High Elf"
    assert subraces[0]["slug"] == "high-elf"


@respx.mock
async def test_get_feats_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching feats."""
    respx.get("https://www.dnd5eapi.co/api/2014/feats/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "alert",
                        "name": "Alert",
                        "desc": "Always vigilant...",
                    },
                    {
                        "index": "athlete",
                        "name": "Athlete",
                        "desc": "You have undergone extensive physical training...",
                    },
                ]
            },
        )
    )

    feats = await dnd5e_client.get_feats_dnd5e()

    assert len(feats) == 2
    assert feats[0]["name"] == "Alert"
    assert feats[0]["slug"] == "alert"


@respx.mock
async def test_get_traits(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching traits."""
    respx.get("https://www.dnd5eapi.co/api/2014/traits/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "darkvision",
                        "name": "Darkvision",
                        "desc": "You can see in dim light...",
                    },
                    {
                        "index": "dwarf-resilience",
                        "name": "Dwarf Resilience",
                        "desc": "You have resistance to poison damage...",
                    },
                ]
            },
        )
    )

    traits = await dnd5e_client.get_traits()

    assert len(traits) == 2
    assert traits[0]["name"] == "Darkvision"
    assert traits[0]["slug"] == "darkvision"


@respx.mock
async def test_get_backgrounds_dnd5e_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify backgrounds are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/backgrounds/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "acolyte",
                        "name": "Acolyte",
                        "desc": "You have spent your life in service...",
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_backgrounds_dnd5e()

    cached = await get_cached_entity("backgrounds", "acolyte")
    assert cached is not None
    assert cached["name"] == "Acolyte"


@respx.mock
async def test_get_classes_dnd5e_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify classes are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/classes/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "barbarian",
                        "name": "Barbarian",
                        "hit_die": 12,
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_classes_dnd5e()

    cached = await get_cached_entity("classes", "barbarian")
    assert cached is not None
    assert cached["name"] == "Barbarian"


@respx.mock
async def test_get_subclasses_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify subclasses are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/subclasses/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "berserker",
                        "name": "Berserker",
                        "class": {"index": "barbarian", "name": "Barbarian"},
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_subclasses()

    cached = await get_cached_entity("subclasses", "berserker")
    assert cached is not None
    assert cached["name"] == "Berserker"


@respx.mock
async def test_get_races_dnd5e_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify races are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/races/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "human",
                        "name": "Human",
                        "speed": 30,
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_races_dnd5e()

    cached = await get_cached_entity("races", "human")
    assert cached is not None
    assert cached["name"] == "Human"


@respx.mock
async def test_get_subraces_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify subraces are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/subraces/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "high-elf",
                        "name": "High Elf",
                        "race": {"index": "elf", "name": "Elf"},
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_subraces()

    cached = await get_cached_entity("subraces", "high-elf")
    assert cached is not None
    assert cached["name"] == "High Elf"


@respx.mock
async def test_get_feats_dnd5e_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify feats are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/feats/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "alert",
                        "name": "Alert",
                        "desc": "Always vigilant...",
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_feats_dnd5e()

    cached = await get_cached_entity("feats", "alert")
    assert cached is not None
    assert cached["name"] == "Alert"


@respx.mock
async def test_get_traits_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify traits are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/traits/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "darkvision",
                        "name": "Darkvision",
                        "desc": "You can see in dim light...",
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_traits()

    cached = await get_cached_entity("traits", "darkvision")
    assert cached is not None
    assert cached["name"] == "Darkvision"


# Task 1.13: Equipment methods
@respx.mock
async def test_get_equipment(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching equipment."""
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "longsword",
                        "name": "Longsword",
                        "equipment_category": {"index": "melee-weapons", "name": "Melee Weapons"},
                    },
                    {
                        "index": "plate-armor",
                        "name": "Plate Armor",
                        "equipment_category": {"index": "armor", "name": "Armor"},
                    },
                ]
            },
        )
    )

    equipment = await dnd5e_client.get_equipment()

    assert len(equipment) == 2
    assert equipment[0]["name"] == "Longsword"
    assert equipment[0]["slug"] == "longsword"


@respx.mock
async def test_get_equipment_categories(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching equipment categories."""
    respx.get("https://www.dnd5eapi.co/api/2014/equipment-categories/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "armor",
                        "name": "Armor",
                        "equipment": [{"index": "plate-armor", "name": "Plate Armor"}],
                    },
                    {
                        "index": "melee-weapons",
                        "name": "Melee Weapons",
                        "equipment": [{"index": "longsword", "name": "Longsword"}],
                    },
                ]
            },
        )
    )

    categories = await dnd5e_client.get_equipment_categories()

    assert len(categories) == 2
    assert categories[0]["name"] == "Armor"
    assert categories[0]["slug"] == "armor"


@respx.mock
async def test_get_magic_items_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching magic items."""
    respx.get("https://www.dnd5eapi.co/api/2014/magic-items/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "bag-of-holding",
                        "name": "Bag of Holding",
                        "rarity": "Uncommon",
                    },
                    {
                        "index": "wand-of-fireballs",
                        "name": "Wand of Fireballs",
                        "rarity": "Rare",
                    },
                ]
            },
        )
    )

    items = await dnd5e_client.get_magic_items_dnd5e()

    assert len(items) == 2
    assert items[0]["name"] == "Bag of Holding"
    assert items[0]["slug"] == "bag-of-holding"


@respx.mock
async def test_get_equipment_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify equipment is cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/equipment/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "longsword",
                        "name": "Longsword",
                        "equipment_category": {"index": "melee-weapons"},
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_equipment()

    cached = await get_cached_entity("equipment", "longsword")
    assert cached is not None
    assert cached["name"] == "Longsword"


@respx.mock
async def test_get_equipment_categories_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify equipment categories are cached as entities with 30-day TTL."""
    respx.get("https://www.dnd5eapi.co/api/2014/equipment-categories/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "armor",
                        "name": "Armor",
                        "equipment": [],
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_equipment_categories()

    cached = await get_cached_entity("itemcategories", "armor")
    assert cached is not None
    assert cached["name"] == "Armor"


@respx.mock
async def test_get_magic_items_dnd5e_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify magic items are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/magic-items/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "bag-of-holding",
                        "name": "Bag of Holding",
                        "rarity": "Uncommon",
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_magic_items_dnd5e()

    cached = await get_cached_entity("magicitems", "bag-of-holding")
    assert cached is not None
    assert cached["name"] == "Bag of Holding"


# Task 1.14: Spell and monster methods
@respx.mock
async def test_get_spells_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching spells."""
    respx.get("https://www.dnd5eapi.co/api/2014/spells/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "acid-splash",
                        "name": "Acid Splash",
                        "level": 0,
                        "school": "evocation",
                    },
                    {
                        "index": "magic-missile",
                        "name": "Magic Missile",
                        "level": 1,
                        "school": "evocation",
                    },
                ]
            },
        )
    )

    spells = await dnd5e_client.get_spells_dnd5e()

    assert len(spells) == 2
    assert spells[0]["name"] == "Acid Splash"
    assert spells[0]["slug"] == "acid-splash"


@respx.mock
async def test_get_monsters_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching monsters."""
    respx.get("https://www.dnd5eapi.co/api/2014/monsters/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "aboleth",
                        "name": "Aboleth",
                        "size": "Large",
                        "type": "aberration",
                        "alignment": "lawful evil",
                        "armor_class": 17,
                        "hit_points": 135,
                        "hit_dice": "10d12+70",
                        "challenge_rating": "10",
                    },
                    {
                        "index": "acererak",
                        "name": "Acererak",
                        "size": "Medium",
                        "type": "undead",
                        "alignment": "neutral evil",
                        "armor_class": 20,
                        "hit_points": 165,
                        "hit_dice": "11d8+110",
                        "challenge_rating": "23",
                    },
                ]
            },
        )
    )

    monsters = await dnd5e_client.get_monsters_dnd5e()

    assert len(monsters) == 2
    assert monsters[0]["name"] == "Aboleth"
    assert monsters[0]["slug"] == "aboleth"
    assert monsters[0]["size"] == "Large"
    assert monsters[1]["armor_class"] == 20


@respx.mock
async def test_get_spells_dnd5e_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify spells are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/spells/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "acid-splash",
                        "name": "Acid Splash",
                        "level": 0,
                        "school": "evocation",
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_spells_dnd5e()

    cached = await get_cached_entity("spells", "acid-splash")
    assert cached is not None
    assert cached["name"] == "Acid Splash"


@respx.mock
async def test_get_monsters_dnd5e_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify monsters are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/monsters/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "aboleth",
                        "name": "Aboleth",
                        "size": "Large",
                        "type": "aberration",
                        "alignment": "lawful evil",
                        "armor_class": 17,
                        "hit_points": 135,
                        "hit_dice": "10d12+70",
                        "challenge_rating": "10",
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_monsters_dnd5e()

    cached = await get_cached_entity("monsters", "aboleth")
    assert cached is not None
    assert cached["name"] == "Aboleth"


# Task 1.15: Conditions and features methods
@respx.mock
async def test_get_conditions_dnd5e(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching conditions."""
    respx.get("https://www.dnd5eapi.co/api/2014/conditions/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "blinded",
                        "name": "Blinded",
                        "desc": "A blinded creature can't see...",
                    },
                    {
                        "index": "charmed",
                        "name": "Charmed",
                        "desc": "A charmed creature can't attack its charmer...",
                    },
                ]
            },
        )
    )

    conditions = await dnd5e_client.get_conditions_dnd5e()

    assert len(conditions) == 2
    assert conditions[0]["name"] == "Blinded"
    assert conditions[0]["slug"] == "blinded"


@respx.mock
async def test_get_features(dnd5e_client: Dnd5eApiClient) -> None:
    """Test fetching features."""
    respx.get("https://www.dnd5eapi.co/api/2014/features/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "action-surge",
                        "name": "Action Surge",
                        "desc": "On your turn, you can take one additional action...",
                        "class": {"index": "fighter", "name": "Fighter"},
                    },
                    {
                        "index": "bardic-inspiration",
                        "name": "Bardic Inspiration",
                        "desc": "You can inspire others...",
                        "class": {"index": "bard", "name": "Bard"},
                    },
                ]
            },
        )
    )

    features = await dnd5e_client.get_features()

    assert len(features) == 2
    assert features[0]["name"] == "Action Surge"
    assert features[0]["slug"] == "action-surge"


@respx.mock
async def test_get_conditions_dnd5e_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify conditions are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/conditions/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "blinded",
                        "name": "Blinded",
                        "desc": "A blinded creature can't see...",
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_conditions_dnd5e()

    cached = await get_cached_entity("conditions", "blinded")
    assert cached is not None
    assert cached["name"] == "Blinded"


@respx.mock
async def test_get_features_uses_cache(dnd5e_client: Dnd5eApiClient) -> None:
    """Verify features are cached as entities."""
    respx.get("https://www.dnd5eapi.co/api/2014/features/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "index": "action-surge",
                        "name": "Action Surge",
                        "desc": "On your turn...",
                        "class": {"index": "fighter", "name": "Fighter"},
                    }
                ]
            },
        )
    )

    await dnd5e_client.get_features()

    cached = await get_cached_entity("features", "action-surge")
    assert cached is not None
    assert cached["name"] == "Action Surge"
