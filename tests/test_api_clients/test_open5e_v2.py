"""Tests for Open5eV2Client."""

from collections.abc import AsyncGenerator

import httpx
import pytest
import respx

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


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
            json={"results": [{"slug": "service-1", "name": "Service 1"}]},
        )
    )

    services = await v2_client.get_services()

    assert len(services) == 1
    assert services[0]["name"] == "Service 1"
