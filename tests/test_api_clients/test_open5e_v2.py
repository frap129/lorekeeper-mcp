"""Tests for Open5eV2Client."""

import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
import respx

import lorekeeper_mcp.config
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.cache.db import get_cached_entity
from lorekeeper_mcp.cache.schema import init_entity_cache


@pytest.fixture
async def v2_client(test_db) -> AsyncGenerator[Open5eV2Client]:
    """Create Open5eV2Client for testing."""
    client = Open5eV2Client()
    yield client
    await client.close()


@respx.mock
async def test_get_spells_basic(v2_client: Open5eV2Client) -> None:
    """Test basic spell lookup."""
    respx.get("https://api.open5e.com/v2/spells/?name=fireball").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Fireball",
                        "slug": "fireball",
                        "level": 3,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "150 feet",
                        "components": "V, S, M",
                        "duration": "Instantaneous",
                        "desc": "A bright streak...",
                    }
                ]
            },
        )
    )

    spells = await v2_client.get_spells(name="fireball")

    assert len(spells) == 1
    assert spells[0].name == "Fireball"
    assert spells[0].level == 3


@respx.mock
async def test_get_spells_with_filters(v2_client: Open5eV2Client) -> None:
    """Test spell lookup with level and school filters.

    School filtering is done client-side (not supported by API),
    so only level is sent to the API.
    """
    respx.get("https://api.open5e.com/v2/spells/?level=3").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    spells = await v2_client.get_spells(level=3, school="Evocation")

    assert isinstance(spells, list)


@respx.mock
async def test_get_weapons(v2_client: Open5eV2Client) -> None:
    """Test weapon lookup."""
    respx.get("https://api.open5e.com/v2/weapons/?name=longsword").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "url": "https://api.open5e.com/v2/weapons/srd-2024_longsword/",
                        "key": "srd-2024_longsword",
                        "name": "Longsword",
                        "slug": "longsword",
                        "damage_dice": "1d8",
                        "damage_type": {
                            "name": "Slashing",
                            "key": "slashing",
                            "url": "https://api.open5e.com/v2/damagetypes/slashing/",
                        },
                        "properties": [
                            {
                                "property": {
                                    "name": "Versatile",
                                    "type": None,
                                    "url": "/v2/weaponproperties/versatile-wp/",
                                },
                                "detail": "1d10",
                            }
                        ],
                        "range": 0.0,
                        "long_range": 0.0,
                        "distance_unit": "feet",
                        "is_simple": False,
                        "is_improvised": False,
                    }
                ]
            },
        )
    )

    weapons = await v2_client.get_weapons(name="longsword")

    assert len(weapons) == 1
    assert weapons[0].name == "Longsword"
    assert weapons[0].damage_dice == "1d8"


@respx.mock
async def test_get_armor(v2_client: Open5eV2Client) -> None:
    """Test armor lookup."""
    respx.get("https://api.open5e.com/v2/armor/?name=chain-mail").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Chain Mail",
                        "slug": "chain-mail",
                        "category": "Heavy",
                        "base_ac": 16,
                        "cost": "75 gp",
                        "weight": 55.0,
                        "stealth_disadvantage": True,
                    }
                ]
            },
        )
    )

    armors = await v2_client.get_armor(name="chain-mail")

    assert len(armors) == 1
    assert armors[0].name == "Chain Mail"
    assert armors[0].base_ac == 16


@pytest.fixture
async def v2_client_with_cache() -> AsyncGenerator[Open5eV2Client]:
    """Create V2 client with test cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        await init_entity_cache(str(db_path))

        original = lorekeeper_mcp.config.settings.db_path
        lorekeeper_mcp.config.settings.db_path = db_path

        client = Open5eV2Client()
        yield client

        lorekeeper_mcp.config.settings.db_path = original
        await client.close()


@respx.mock
async def test_get_spells_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get spells caches entities."""
    respx.get("https://api.open5e.com/v2/spells/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "fireball",
                        "name": "Fireball",
                        "level": 3,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "150 feet",
                        "components": "V, S, M",
                        "duration": "Instantaneous",
                    }
                ]
            },
        )
    )

    spells = await v2_client_with_cache.get_spells()
    # Verify we got Pydantic models
    assert len(spells) == 1
    assert spells[0].name == "Fireball"
    assert spells[0].level == 3

    # Verify caching worked
    cached = await get_cached_entity("spells", "fireball")
    assert cached is not None
    assert cached["level"] == 3


@respx.mock
@pytest.mark.asyncio
async def test_get_weapons_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get weapons caches entities and returns Pydantic models."""
    respx.get("https://api.open5e.com/v2/weapons/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "url": "https://api.open5e.com/v2/weapons/srd-2024_longsword/",
                        "key": "srd-2024_longsword",
                        "slug": "longsword",
                        "name": "Longsword",
                        "damage_dice": "1d8",
                        "damage_type": {
                            "name": "Slashing",
                            "key": "slashing",
                            "url": "https://api.open5e.com/v2/damagetypes/slashing/",
                        },
                        "properties": [],
                        "range": 0.0,
                        "long_range": 0.0,
                        "distance_unit": "feet",
                        "is_simple": False,
                        "is_improvised": False,
                    }
                ]
            },
        )
    )

    weapons = await v2_client_with_cache.get_weapons()
    assert len(weapons) == 1
    assert weapons[0].name == "Longsword"

    cached = await get_cached_entity("weapons", "longsword")
    assert cached is not None


@respx.mock
@pytest.mark.asyncio
async def test_get_armor_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get armor caches entities and returns Pydantic models."""
    respx.get("https://api.open5e.com/v2/armor/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "plate-armor",
                        "name": "Plate Armor",
                        "category": "Heavy",
                        "base_ac": 18,
                        "cost": "1500 gp",
                        "weight": 65.0,
                    }
                ]
            },
        )
    )

    armors = await v2_client_with_cache.get_armor()
    assert len(armors) == 1
    assert armors[0].name == "Plate Armor"

    cached = await get_cached_entity("armor", "plate-armor")
    assert cached is not None


@respx.mock
@pytest.mark.asyncio
async def test_get_backgrounds_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get backgrounds caches entities."""
    respx.get("https://api.open5e.com/v2/backgrounds/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"slug": "acolyte", "name": "Acolyte", "desc": "You have always been..."}
                ]
            },
        )
    )

    backgrounds = await v2_client_with_cache.get_backgrounds()
    assert len(backgrounds) == 1
    assert backgrounds[0]["name"] == "Acolyte"

    cached = await get_cached_entity("backgrounds", "acolyte")
    assert cached is not None


@respx.mock
@pytest.mark.asyncio
async def test_get_feats_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get feats caches entities."""
    respx.get("https://api.open5e.com/v2/feats/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "alert", "name": "Alert", "desc": "Always vigilant..."}]},
        )
    )

    feats = await v2_client_with_cache.get_feats()
    assert len(feats) == 1
    assert feats[0]["name"] == "Alert"

    cached = await get_cached_entity("feats", "alert")
    assert cached is not None


@respx.mock
@pytest.mark.asyncio
async def test_get_conditions_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get conditions caches entities."""
    respx.get("https://api.open5e.com/v2/conditions/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "blinded", "name": "Blinded", "desc": "A blinded..."}]},
        )
    )

    conditions = await v2_client_with_cache.get_conditions()
    assert len(conditions) == 1
    assert conditions[0]["name"] == "Blinded"

    cached = await get_cached_entity("conditions", "blinded")
    assert cached is not None


@respx.mock
async def test_spell_school_filtering(v2_client: Open5eV2Client) -> None:
    """Test that get_spells filters by school on client side.

    Open5e v2 API doesn't support server-side school filtering, so
    client must filter results after retrieval.
    """
    # Mock the API call without school parameter - API returns all spells
    respx.get("https://api.open5e.com/v2/spells/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Fireball",
                        "slug": "fireball",
                        "level": 3,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "150 feet",
                        "components": "V, S, M",
                        "duration": "Instantaneous",
                        "desc": "A bright streak...",
                    },
                    {
                        "name": "Magic Missile",
                        "slug": "magic-missile",
                        "level": 1,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "120 feet",
                        "components": "V, S",
                        "duration": "Instantaneous",
                        "desc": "A missile of magical force...",
                    },
                    {
                        "name": "Detect Magic",
                        "slug": "detect-magic",
                        "level": 1,
                        "school": "Divination",
                        "casting_time": "1 action",
                        "range": "Self",
                        "components": "V, S",
                        "duration": "Concentration, up to 10 minutes",
                        "desc": "For the spell's duration...",
                    },
                ]
            },
        )
    )

    # Request spells filtered by school
    spells = await v2_client.get_spells(school="Evocation")

    # Should only return evocation spells
    assert len(spells) == 2
    assert all(spell.school == "Evocation" for spell in spells)
    assert {spell.name for spell in spells} == {"Fireball", "Magic Missile"}


@respx.mock
async def test_spell_school_filtering_case_insensitive(
    v2_client: Open5eV2Client,
) -> None:
    """Test that school filtering is case-insensitive.

    The filtering should match spells regardless of the case of the
    school parameter provided by the user.
    """
    respx.get("https://api.open5e.com/v2/spells/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Fireball",
                        "slug": "fireball",
                        "level": 3,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "150 feet",
                        "components": "V, S, M",
                        "duration": "Instantaneous",
                        "desc": "A bright streak...",
                    },
                    {
                        "name": "Detect Magic",
                        "slug": "detect-magic",
                        "level": 1,
                        "school": "Divination",
                        "casting_time": "1 action",
                        "range": "Self",
                        "components": "V, S",
                        "duration": "Concentration, up to 10 minutes",
                        "desc": "For the spell's duration...",
                    },
                ]
            },
        )
    )

    # Test with lowercase input
    spells = await v2_client.get_spells(school="evocation")
    assert len(spells) == 1
    assert spells[0].name == "Fireball"

    # Test with uppercase input
    spells = await v2_client.get_spells(school="EVOCATION")
    assert len(spells) == 1
    assert spells[0].name == "Fireball"

    # Test with mixed case input
    spells = await v2_client.get_spells(school="EvOcAtIoN")
    assert len(spells) == 1
    assert spells[0].name == "Fireball"


# Task 1.6: Item-related methods
@respx.mock
async def test_get_items(v2_client: Open5eV2Client) -> None:
    """Test get_items returns list of items."""
    respx.get("https://api.open5e.com/v2/items/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "potion-of-healing",
                        "name": "Potion of Healing",
                        "desc": "You regain 4d4+4...",
                    }
                ]
            },
        )
    )

    items = await v2_client.get_items()

    assert len(items) == 1
    assert items[0]["name"] == "Potion of Healing"
    assert items[0]["slug"] == "potion-of-healing"


@respx.mock
async def test_get_item_sets(v2_client: Open5eV2Client) -> None:
    """Test get_item_sets returns list of item sets."""
    respx.get("https://api.open5e.com/v2/itemsets/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "core-rulebook", "name": "Core Rulebook"}]},
        )
    )

    item_sets = await v2_client.get_item_sets()

    assert len(item_sets) == 1
    assert item_sets[0]["name"] == "Core Rulebook"


@respx.mock
async def test_get_item_categories(v2_client: Open5eV2Client) -> None:
    """Test get_item_categories returns list of item categories."""
    respx.get("https://api.open5e.com/v2/itemcategories/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "wondrous-item", "name": "Wondrous Item"}]},
        )
    )

    categories = await v2_client.get_item_categories()

    assert len(categories) == 1
    assert categories[0]["name"] == "Wondrous Item"


# Task 1.7: Creature methods
@respx.mock
async def test_get_creatures(v2_client: Open5eV2Client) -> None:
    """Test get_creatures returns list of Monster models."""
    respx.get("https://api.open5e.com/v2/creatures/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "goblin",
                        "name": "Goblin",
                        "desc": "A common humanoid...",
                        "size": "Small",
                        "type": "humanoid",
                        "alignment": "Neutral Evil",
                        "armor_class": 15,
                        "hit_points": 7,
                        "hit_dice": "2d6",
                        "challenge_rating": "1/4",
                    }
                ]
            },
        )
    )

    creatures = await v2_client.get_creatures()

    assert len(creatures) == 1
    assert creatures[0].name == "Goblin"
    assert creatures[0].size == "Small"


@respx.mock
async def test_get_creature_types(v2_client: Open5eV2Client) -> None:
    """Test get_creature_types returns list of creature types."""
    respx.get("https://api.open5e.com/v2/creaturetypes/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "humanoid", "name": "Humanoid"}]},
        )
    )

    creature_types = await v2_client.get_creature_types()

    assert len(creature_types) == 1
    assert creature_types[0]["name"] == "Humanoid"


@respx.mock
async def test_get_creature_sets(v2_client: Open5eV2Client) -> None:
    """Test get_creature_sets returns list of creature sets."""
    respx.get("https://api.open5e.com/v2/creaturesets/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "srd-5e", "name": "SRD 5e"}]},
        )
    )

    creature_sets = await v2_client.get_creature_sets()

    assert len(creature_sets) == 1
    assert creature_sets[0]["name"] == "SRD 5e"


# Task 1.8: Reference data methods
@respx.mock
async def test_get_damage_types_v2(v2_client: Open5eV2Client) -> None:
    """Test get_damage_types_v2 returns damage types."""
    respx.get("https://api.open5e.com/v2/damagetypes/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "slashing", "name": "Slashing"}]},
        )
    )

    damage_types = await v2_client.get_damage_types_v2()

    assert len(damage_types) == 1
    assert damage_types[0]["name"] == "Slashing"


@respx.mock
async def test_get_languages_v2(v2_client: Open5eV2Client) -> None:
    """Test get_languages_v2 returns languages."""
    respx.get("https://api.open5e.com/v2/languages/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "common", "name": "Common"}]},
        )
    )

    languages = await v2_client.get_languages_v2()

    assert len(languages) == 1
    assert languages[0]["name"] == "Common"


@respx.mock
async def test_get_alignments_v2(v2_client: Open5eV2Client) -> None:
    """Test get_alignments_v2 returns alignments."""
    respx.get("https://api.open5e.com/v2/alignments/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "chaotic-evil", "name": "Chaotic Evil"}]},
        )
    )

    alignments = await v2_client.get_alignments_v2()

    assert len(alignments) == 1
    assert alignments[0]["name"] == "Chaotic Evil"


@respx.mock
async def test_get_spell_schools_v2(v2_client: Open5eV2Client) -> None:
    """Test get_spell_schools_v2 returns spell schools."""
    respx.get("https://api.open5e.com/v2/spellschools/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "evocation", "name": "Evocation"}]},
        )
    )

    schools = await v2_client.get_spell_schools_v2()

    assert len(schools) == 1
    assert schools[0]["name"] == "Evocation"


@respx.mock
async def test_get_sizes(v2_client: Open5eV2Client) -> None:
    """Test get_sizes returns creature sizes."""
    respx.get("https://api.open5e.com/v2/sizes/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "medium", "name": "Medium"}]},
        )
    )

    sizes = await v2_client.get_sizes()

    assert len(sizes) == 1
    assert sizes[0]["name"] == "Medium"


@respx.mock
async def test_get_item_rarities(v2_client: Open5eV2Client) -> None:
    """Test get_item_rarities returns item rarity levels."""
    respx.get("https://api.open5e.com/v2/itemrarities/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "rare", "name": "Rare"}]},
        )
    )

    rarities = await v2_client.get_item_rarities()

    assert len(rarities) == 1
    assert rarities[0]["name"] == "Rare"


@respx.mock
async def test_get_environments(v2_client: Open5eV2Client) -> None:
    """Test get_environments returns encounter environments."""
    respx.get("https://api.open5e.com/v2/environments/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "forest", "name": "Forest"}]},
        )
    )

    environments = await v2_client.get_environments()

    assert len(environments) == 1
    assert environments[0]["name"] == "Forest"


@respx.mock
async def test_get_abilities(v2_client: Open5eV2Client) -> None:
    """Test get_abilities returns ability scores."""
    respx.get("https://api.open5e.com/v2/abilities/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "strength", "name": "Strength"}]},
        )
    )

    abilities = await v2_client.get_abilities()

    assert len(abilities) == 1
    assert abilities[0]["name"] == "Strength"


@respx.mock
async def test_get_skills_v2(v2_client: Open5eV2Client) -> None:
    """Test get_skills_v2 returns skill list."""
    respx.get("https://api.open5e.com/v2/skills/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "acrobatics", "name": "Acrobatics"}]},
        )
    )

    skills = await v2_client.get_skills_v2()

    assert len(skills) == 1
    assert skills[0]["name"] == "Acrobatics"


# Task 1.9: Character option methods
@respx.mock
async def test_get_species(v2_client: Open5eV2Client) -> None:
    """Test get_species returns character species/races."""
    respx.get("https://api.open5e.com/v2/species/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "human", "name": "Human"}]},
        )
    )

    species = await v2_client.get_species()

    assert len(species) == 1
    assert species[0]["name"] == "Human"


@respx.mock
async def test_get_classes_v2(v2_client: Open5eV2Client) -> None:
    """Test get_classes_v2 returns character classes."""
    respx.get("https://api.open5e.com/v2/classes/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "wizard", "name": "Wizard"}]},
        )
    )

    classes = await v2_client.get_classes_v2()

    assert len(classes) == 1
    assert classes[0]["name"] == "Wizard"


# Task 1.10: Rules and metadata methods
@respx.mock
async def test_get_rules_v2(v2_client: Open5eV2Client) -> None:
    """Test get_rules_v2 returns game rules."""
    respx.get("https://api.open5e.com/v2/rules/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "action", "name": "Action"}]},
        )
    )

    rules = await v2_client.get_rules_v2()

    assert len(rules) == 1
    assert rules[0]["name"] == "Action"


@respx.mock
async def test_get_rulesets(v2_client: Open5eV2Client) -> None:
    """Test get_rulesets returns ruleset definitions."""
    respx.get("https://api.open5e.com/v2/rulesets/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "5e", "name": "D&D 5e"}]},
        )
    )

    rulesets = await v2_client.get_rulesets()

    assert len(rulesets) == 1
    assert rulesets[0]["name"] == "D&D 5e"


@respx.mock
async def test_get_documents(v2_client: Open5eV2Client) -> None:
    """Test get_documents returns game documents."""
    respx.get("https://api.open5e.com/v2/documents/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "phb", "name": "Player's Handbook"}]},
        )
    )

    documents = await v2_client.get_documents()

    assert len(documents) == 1
    assert documents[0]["name"] == "Player's Handbook"


@respx.mock
async def test_get_licenses(v2_client: Open5eV2Client) -> None:
    """Test get_licenses returns license information."""
    respx.get("https://api.open5e.com/v2/licenses/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "ogl", "name": "Open Game License"}]},
        )
    )

    licenses = await v2_client.get_licenses()

    assert len(licenses) == 1
    assert licenses[0]["name"] == "Open Game License"


@respx.mock
async def test_get_publishers(v2_client: Open5eV2Client) -> None:
    """Test get_publishers returns publisher information."""
    respx.get("https://api.open5e.com/v2/publishers/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "wotc", "name": "Wizards of the Coast"}]},
        )
    )

    publishers = await v2_client.get_publishers()

    assert len(publishers) == 1
    assert publishers[0]["name"] == "Wizards of the Coast"


@respx.mock
async def test_get_game_systems(v2_client: Open5eV2Client) -> None:
    """Test get_game_systems returns game system information."""
    respx.get("https://api.open5e.com/v2/gamesystems/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "dnd5e", "name": "D&D 5e"}]},
        )
    )

    systems = await v2_client.get_game_systems()

    assert len(systems) == 1
    assert systems[0]["name"] == "D&D 5e"


# Task 1.11: Additional content methods
@respx.mock
async def test_get_images(v2_client: Open5eV2Client) -> None:
    """Test get_images returns image resources."""
    respx.get("https://api.open5e.com/v2/images/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "goblin", "name": "Goblin"}]},
        )
    )

    images = await v2_client.get_images()

    assert len(images) == 1
    assert images[0]["name"] == "Goblin"


@respx.mock
async def test_get_weapon_properties_v2(v2_client: Open5eV2Client) -> None:
    """Test get_weapon_properties_v2 returns weapon properties."""
    respx.get("https://api.open5e.com/v2/weaponproperties/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "finesse", "name": "Finesse"}]},
        )
    )

    properties = await v2_client.get_weapon_properties_v2()

    assert len(properties) == 1
    assert properties[0]["name"] == "Finesse"


@respx.mock
async def test_get_services(v2_client: Open5eV2Client) -> None:
    """Test get_services returns service information."""
    respx.get("https://api.open5e.com/v2/services/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "compendium", "name": "Compendium"}]},
        )
    )

    services = await v2_client.get_services()

    assert len(services) == 1
    assert services[0]["name"] == "Compendium"


# Cache verification tests for Task 1.6: Item-related methods
@respx.mock
async def test_get_items_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get items caches entities."""
    respx.get("https://api.open5e.com/v2/items/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "potion-of-healing",
                        "name": "Potion of Healing",
                        "desc": "You regain 4d4+4...",
                    }
                ]
            },
        )
    )

    items = await v2_client_with_cache.get_items()
    assert len(items) == 1
    assert items[0]["name"] == "Potion of Healing"

    cached = await get_cached_entity("items", "potion-of-healing")
    assert cached is not None
    assert cached["name"] == "Potion of Healing"


@respx.mock
async def test_get_item_sets_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get item sets caches entities."""
    respx.get("https://api.open5e.com/v2/itemsets/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "core-rulebook", "name": "Core Rulebook"}]},
        )
    )

    item_sets = await v2_client_with_cache.get_item_sets()
    assert len(item_sets) == 1
    assert item_sets[0]["name"] == "Core Rulebook"

    cached = await get_cached_entity("itemsets", "core-rulebook")
    assert cached is not None
    assert cached["name"] == "Core Rulebook"


@respx.mock
async def test_get_item_categories_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get item categories caches entities."""
    respx.get("https://api.open5e.com/v2/itemcategories/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "wondrous-item", "name": "Wondrous Item"}]},
        )
    )

    categories = await v2_client_with_cache.get_item_categories()
    assert len(categories) == 1
    assert categories[0]["name"] == "Wondrous Item"

    cached = await get_cached_entity("itemcategories", "wondrous-item")
    assert cached is not None
    assert cached["name"] == "Wondrous Item"


# Cache verification tests for Task 1.7: Creature methods
@respx.mock
async def test_get_creatures_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get creatures caches entities."""
    respx.get("https://api.open5e.com/v2/creatures/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "goblin",
                        "name": "Goblin",
                        "desc": "A common humanoid...",
                        "size": "Small",
                        "type": "humanoid",
                        "alignment": "Neutral Evil",
                        "armor_class": 15,
                        "hit_points": 7,
                        "hit_dice": "2d6",
                        "challenge_rating": "1/4",
                    }
                ]
            },
        )
    )

    creatures = await v2_client_with_cache.get_creatures()
    assert len(creatures) == 1
    assert creatures[0].name == "Goblin"

    cached = await get_cached_entity("creatures", "goblin")
    assert cached is not None
    assert cached["name"] == "Goblin"


@respx.mock
async def test_get_creature_types_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get creature types caches entities."""
    respx.get("https://api.open5e.com/v2/creaturetypes/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "humanoid", "name": "Humanoid"}]},
        )
    )

    creature_types = await v2_client_with_cache.get_creature_types()
    assert len(creature_types) == 1
    assert creature_types[0]["name"] == "Humanoid"

    cached = await get_cached_entity("creaturetypes", "humanoid")
    assert cached is not None
    assert cached["name"] == "Humanoid"


@respx.mock
async def test_get_creature_sets_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get creature sets caches entities."""
    respx.get("https://api.open5e.com/v2/creaturesets/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "srd-5e", "name": "SRD 5e"}]},
        )
    )

    creature_sets = await v2_client_with_cache.get_creature_sets()
    assert len(creature_sets) == 1
    assert creature_sets[0]["name"] == "SRD 5e"

    cached = await get_cached_entity("creaturesets", "srd-5e")
    assert cached is not None
    assert cached["name"] == "SRD 5e"


# Cache verification tests for Task 1.8: Reference data methods
@respx.mock
async def test_get_damage_types_v2_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get damage types caches entities."""
    respx.get("https://api.open5e.com/v2/damagetypes/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "slashing", "name": "Slashing"}]},
        )
    )

    damage_types = await v2_client_with_cache.get_damage_types_v2()
    assert len(damage_types) == 1
    assert damage_types[0]["name"] == "Slashing"

    cached = await get_cached_entity("damagetypes", "slashing")
    assert cached is not None
    assert cached["name"] == "Slashing"


@respx.mock
async def test_get_languages_v2_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get languages caches entities."""
    respx.get("https://api.open5e.com/v2/languages/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "common", "name": "Common"}]},
        )
    )

    languages = await v2_client_with_cache.get_languages_v2()
    assert len(languages) == 1
    assert languages[0]["name"] == "Common"

    cached = await get_cached_entity("languages", "common")
    assert cached is not None
    assert cached["name"] == "Common"


@respx.mock
async def test_get_alignments_v2_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get alignments caches entities."""
    respx.get("https://api.open5e.com/v2/alignments/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "chaotic-evil", "name": "Chaotic Evil"}]},
        )
    )

    alignments = await v2_client_with_cache.get_alignments_v2()
    assert len(alignments) == 1
    assert alignments[0]["name"] == "Chaotic Evil"

    cached = await get_cached_entity("alignments", "chaotic-evil")
    assert cached is not None
    assert cached["name"] == "Chaotic Evil"


@respx.mock
async def test_get_spell_schools_v2_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get spell schools caches entities."""
    respx.get("https://api.open5e.com/v2/spellschools/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "evocation", "name": "Evocation"}]},
        )
    )

    schools = await v2_client_with_cache.get_spell_schools_v2()
    assert len(schools) == 1
    assert schools[0]["name"] == "Evocation"

    cached = await get_cached_entity("spellschools", "evocation")
    assert cached is not None
    assert cached["name"] == "Evocation"


@respx.mock
async def test_get_sizes_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get sizes caches entities."""
    respx.get("https://api.open5e.com/v2/sizes/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "medium", "name": "Medium"}]},
        )
    )

    sizes = await v2_client_with_cache.get_sizes()
    assert len(sizes) == 1
    assert sizes[0]["name"] == "Medium"

    cached = await get_cached_entity("sizes", "medium")
    assert cached is not None
    assert cached["name"] == "Medium"


@respx.mock
async def test_get_item_rarities_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get item rarities caches entities."""
    respx.get("https://api.open5e.com/v2/itemrarities/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "rare", "name": "Rare"}]},
        )
    )

    rarities = await v2_client_with_cache.get_item_rarities()
    assert len(rarities) == 1
    assert rarities[0]["name"] == "Rare"

    cached = await get_cached_entity("itemrarities", "rare")
    assert cached is not None
    assert cached["name"] == "Rare"


@respx.mock
async def test_get_environments_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get environments caches entities."""
    respx.get("https://api.open5e.com/v2/environments/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "forest", "name": "Forest"}]},
        )
    )

    environments = await v2_client_with_cache.get_environments()
    assert len(environments) == 1
    assert environments[0]["name"] == "Forest"

    cached = await get_cached_entity("environments", "forest")
    assert cached is not None
    assert cached["name"] == "Forest"


@respx.mock
async def test_get_abilities_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get abilities caches entities."""
    respx.get("https://api.open5e.com/v2/abilities/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "strength", "name": "Strength"}]},
        )
    )

    abilities = await v2_client_with_cache.get_abilities()
    assert len(abilities) == 1
    assert abilities[0]["name"] == "Strength"

    cached = await get_cached_entity("abilities", "strength")
    assert cached is not None
    assert cached["name"] == "Strength"


@respx.mock
async def test_get_skills_v2_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get skills caches entities."""
    respx.get("https://api.open5e.com/v2/skills/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "acrobatics", "name": "Acrobatics"}]},
        )
    )

    skills = await v2_client_with_cache.get_skills_v2()
    assert len(skills) == 1
    assert skills[0]["name"] == "Acrobatics"

    cached = await get_cached_entity("skills", "acrobatics")
    assert cached is not None
    assert cached["name"] == "Acrobatics"


# Cache verification tests for Task 1.9: Character option methods
@respx.mock
async def test_get_species_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get species caches entities."""
    respx.get("https://api.open5e.com/v2/species/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "human", "name": "Human"}]},
        )
    )

    species = await v2_client_with_cache.get_species()
    assert len(species) == 1
    assert species[0]["name"] == "Human"

    cached = await get_cached_entity("species", "human")
    assert cached is not None
    assert cached["name"] == "Human"


@respx.mock
async def test_get_classes_v2_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get classes caches entities."""
    respx.get("https://api.open5e.com/v2/classes/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "wizard", "name": "Wizard"}]},
        )
    )

    classes = await v2_client_with_cache.get_classes_v2()
    assert len(classes) == 1
    assert classes[0]["name"] == "Wizard"

    cached = await get_cached_entity("classes", "wizard")
    assert cached is not None
    assert cached["name"] == "Wizard"


# Cache verification tests for Task 1.10: Rules and metadata methods
@respx.mock
async def test_get_rules_v2_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get rules caches entities."""
    respx.get("https://api.open5e.com/v2/rules/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "action", "name": "Action"}]},
        )
    )

    rules = await v2_client_with_cache.get_rules_v2()
    assert len(rules) == 1
    assert rules[0]["name"] == "Action"

    cached = await get_cached_entity("rules", "action")
    assert cached is not None
    assert cached["name"] == "Action"


@respx.mock
async def test_get_rulesets_uses_entity_cache(v2_client_with_cache: Open5eV2Client) -> None:
    """Get rulesets caches entities."""
    respx.get("https://api.open5e.com/v2/rulesets/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "5e", "name": "D&D 5e"}]},
        )
    )

    rulesets = await v2_client_with_cache.get_rulesets()
    assert len(rulesets) == 1
    assert rulesets[0]["name"] == "D&D 5e"

    cached = await get_cached_entity("rulesets", "5e")
    assert cached is not None
    assert cached["name"] == "D&D 5e"


@respx.mock
async def test_get_documents_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get documents caches entities."""
    respx.get("https://api.open5e.com/v2/documents/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "phb", "name": "Player's Handbook"}]},
        )
    )

    documents = await v2_client_with_cache.get_documents()
    assert len(documents) == 1
    assert documents[0]["name"] == "Player's Handbook"

    cached = await get_cached_entity("documents", "phb")
    assert cached is not None
    assert cached["name"] == "Player's Handbook"


@respx.mock
async def test_get_licenses_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get licenses caches entities."""
    respx.get("https://api.open5e.com/v2/licenses/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "ogl", "name": "Open Game License"}]},
        )
    )

    licenses = await v2_client_with_cache.get_licenses()
    assert len(licenses) == 1
    assert licenses[0]["name"] == "Open Game License"

    cached = await get_cached_entity("licenses", "ogl")
    assert cached is not None
    assert cached["name"] == "Open Game License"


@respx.mock
async def test_get_publishers_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get publishers caches entities."""
    respx.get("https://api.open5e.com/v2/publishers/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "wotc", "name": "Wizards of the Coast"}]},
        )
    )

    publishers = await v2_client_with_cache.get_publishers()
    assert len(publishers) == 1
    assert publishers[0]["name"] == "Wizards of the Coast"

    cached = await get_cached_entity("publishers", "wotc")
    assert cached is not None
    assert cached["name"] == "Wizards of the Coast"


@respx.mock
async def test_get_game_systems_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get game systems caches entities."""
    respx.get("https://api.open5e.com/v2/gamesystems/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "dnd5e", "name": "D&D 5e"}]},
        )
    )

    systems = await v2_client_with_cache.get_game_systems()
    assert len(systems) == 1
    assert systems[0]["name"] == "D&D 5e"

    cached = await get_cached_entity("gamesystems", "dnd5e")
    assert cached is not None
    assert cached["name"] == "D&D 5e"


# Cache verification tests for Task 1.11: Additional content methods
@respx.mock
async def test_get_images_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get images caches entities."""
    respx.get("https://api.open5e.com/v2/images/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "goblin", "name": "Goblin"}]},
        )
    )

    images = await v2_client_with_cache.get_images()
    assert len(images) == 1
    assert images[0]["name"] == "Goblin"

    cached = await get_cached_entity("images", "goblin")
    assert cached is not None
    assert cached["name"] == "Goblin"


@respx.mock
async def test_get_weapon_properties_v2_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get weapon properties caches entities."""
    respx.get("https://api.open5e.com/v2/weaponproperties/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "finesse", "name": "Finesse"}]},
        )
    )

    properties = await v2_client_with_cache.get_weapon_properties_v2()
    assert len(properties) == 1
    assert properties[0]["name"] == "Finesse"

    cached = await get_cached_entity("weaponproperties", "finesse")
    assert cached is not None
    assert cached["name"] == "Finesse"


@respx.mock
async def test_get_services_uses_entity_cache(
    v2_client_with_cache: Open5eV2Client,
) -> None:
    """Get services caches entities."""
    respx.get("https://api.open5e.com/v2/services/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"slug": "compendium", "name": "Compendium"}]},
        )
    )

    services = await v2_client_with_cache.get_services()
    assert len(services) == 1
    assert services[0]["name"] == "Compendium"

    cached = await get_cached_entity("services", "compendium")
    assert cached is not None
    assert cached["name"] == "Compendium"
