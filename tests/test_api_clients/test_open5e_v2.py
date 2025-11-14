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
    respx.get("https://api.open5e.com/v2/spells/?name__icontains=fireball").mock(
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

    Both level and school are sent as server-side parameters.
    """
    respx.get("https://api.open5e.com/v2/spells/?level=3&school__key=evocation").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    spells = await v2_client.get_spells(level=3, school="Evocation")

    assert isinstance(spells, list)


@respx.mock
async def test_get_weapons(v2_client: Open5eV2Client) -> None:
    """Test weapon lookup."""
    respx.get("https://api.open5e.com/v2/weapons/?name__icontains=longsword").mock(
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
    respx.get("https://api.open5e.com/v2/armor/?name__icontains=chain-mail").mock(
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
async def test_school_server_side_filtering(v2_client: Open5eV2Client) -> None:
    """Test that get_spells uses server-side school__key parameter filtering.

    The school parameter should be converted to school__key and sent to the API.
    The API handles the filtering, not the client.
    """
    # Mock the API call WITH school__key parameter - API returns filtered spells
    respx.get("https://api.open5e.com/v2/spells/?school__key=evocation").mock(
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
                ]
            },
        )
    )

    # Request spells filtered by school - uses school__key parameter
    spells = await v2_client.get_spells(school="Evocation")

    # Should return only evocation spells from server
    assert len(spells) == 2
    assert all(spell.school == "Evocation" for spell in spells)
    assert {spell.name for spell in spells} == {"Fireball", "Magic Missile"}


@respx.mock
async def test_no_client_side_filtering(v2_client: Open5eV2Client) -> None:
    """Test that no client-side filtering occurs when school parameter is used.

    If the API properly filters server-side, we should get exactly what the
    API returns without any additional filtering in the client.
    """
    # Mock API that returns filtered results
    respx.get("https://api.open5e.com/v2/spells/?school__key=evocation").mock(
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
                ]
            },
        )
    )

    spells = await v2_client.get_spells(school="Evocation")

    # The spell count must be exactly what the API returned (no client filtering)
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
async def test_get_creatures_transforms_v2_response_to_monster_model(
    v2_client: Open5eV2Client,
) -> None:
    """Test get_creatures transforms Open5e v2 API response to Monster model.

    This test verifies that the Open5eV2Client properly transforms the v2 API
    response format to match the Monster model expectations.

    Key transformations needed:
    1. API `key` → Monster `slug`
    2. API `type` object {"name": "Humanoid", "key": "humanoid"} → Monster string "Humanoid"
    3. API `size` object {"name": "Small", "key": "small"} → Monster string "Small"
    4. API `challenge_rating_text` + `challenge_rating_decimal` → Monster fields
    5. API `speed` with `unit` → Monster speed dict without unit
    6. API `ability_scores` nested → Monster flat ability fields
    7. API `traits` → Monster `special_abilities`
    8. API nested `document` → Monster `document_url`
    """
    respx.get("https://api.open5e.com/v2/creatures/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        # API v2 format - what the API actually returns
                        "key": "goblin",
                        "name": "Goblin",
                        "desc": "A small, cunning creature that often serves as fodder for larger threats.",
                        "type": {
                            "name": "Humanoid",
                            "key": "humanoid",
                            "url": "https://api.open5e.com/v2/creaturetypes/humanoid/",
                        },
                        "size": {
                            "name": "Small",
                            "key": "small",
                            "url": "https://api.open5e.com/v2/sizes/small/",
                        },
                        "alignment": "neutral evil",
                        "armor_class": [{"type": "armor", "value": 15}],
                        "hit_points": 7,
                        "hit_dice": "2d6",
                        "challenge_rating_text": "1/4",
                        "challenge_rating_decimal": "0.250",
                        "speed": {"walk": 30.0, "unit": "feet"},
                        "ability_scores": {
                            "strength": 8,
                            "dexterity": 14,
                            "constitution": 10,
                            "intelligence": 10,
                            "wisdom": 8,
                            "charisma": 6,
                        },
                        "traits": [
                            {
                                "name": "Nimble Escape",
                                "desc": "The goblin can take the Disengage or Hide action as a bonus action on each of its turns.",
                            }
                        ],
                        "document": {
                            "key": "srd-5e",
                            "name": "Systems Reference Document 5.1",
                            "url": "https://api.open5e.com/v2/documents/srd-5e/",
                        },
                    }
                ]
            },
        )
    )

    creatures = await v2_client.get_creatures()

    assert len(creatures) == 1
    creature = creatures[0]

    # Verify basic fields
    assert creature.name == "Goblin"
    assert creature.slug == "goblin"  # Transformed from API `key`
    assert creature.size == "Small"  # Extracted from API `size.name`
    assert creature.type == "Humanoid"  # Extracted from API `type.name`
    assert creature.alignment == "neutral evil"
    assert creature.armor_class == 15
    assert creature.hit_points == 7
    assert creature.hit_dice == "2d6"

    # Verify challenge rating transformation
    assert creature.challenge_rating == "1/4"  # From API `challenge_rating_text`
    assert (
        creature.challenge_rating_decimal == 0.25
    )  # From API `challenge_rating_decimal` string to float

    # Verify speed transformation (unit removed)
    assert creature.speed == {"walk": 30}

    # Verify ability scores transformation (nested to flat)
    assert creature.strength == 8
    assert creature.dexterity == 14
    assert creature.constitution == 10
    assert creature.intelligence == 10
    assert creature.wisdom == 8
    assert creature.charisma == 6

    # Verify traits transformation to special_abilities
    assert creature.special_abilities is not None
    assert len(creature.special_abilities) == 1
    assert creature.special_abilities[0]["name"] == "Nimble Escape"


@respx.mock
async def test_get_creatures_handles_missing_optional_fields(v2_client: Open5eV2Client) -> None:
    """Test get_creatures handles missing optional fields gracefully."""
    respx.get("https://api.open5e.com/v2/creatures/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        # Minimal v2 creature data
                        "key": "basic-creature",
                        "name": "Basic Creature",
                        "desc": "A simple creature.",
                        "type": {"name": "Beast", "key": "beast"},
                        "size": {"name": "Medium", "key": "medium"},
                        "alignment": "unaligned",
                        "armor_class": [{"type": "natural", "value": 10}],
                        "hit_points": 10,
                        "hit_dice": "2d10",
                        "challenge_rating_text": "1/8",
                        "challenge_rating_decimal": "0.125",
                        # Missing: speed, ability_scores, traits, document
                    }
                ]
            },
        )
    )

    creatures = await v2_client.get_creatures()

    assert len(creatures) == 1
    creature = creatures[0]

    assert creature.name == "Basic Creature"
    assert creature.slug == "basic-creature"
    assert creature.size == "Medium"
    assert creature.type == "Beast"
    assert creature.challenge_rating == "1/8"
    assert creature.challenge_rating_decimal == 0.125

    # Optional fields should be None when missing
    assert creature.speed is None
    assert creature.strength is None
    assert creature.special_abilities is None


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


# Task 1.2: Implement Name Partial Matching
@respx.mock
async def test_name_icontains_usage(v2_client: Open5eV2Client) -> None:
    """Test that get_spells uses server-side name__icontains parameter filtering.

    The name parameter should be converted to name__icontains and sent to the API.
    This enables partial name matching server-side (e.g., "fire" matches "Fireball").
    """
    # Mock the API call WITH name__icontains parameter - API returns filtered spells
    respx.get("https://api.open5e.com/v2/spells/?name__icontains=fire").mock(
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
                        "name": "Fire Storm",
                        "slug": "fire-storm",
                        "level": 7,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "150 feet",
                        "components": "V, S",
                        "duration": "Instantaneous",
                        "desc": "A storm of fire...",
                    },
                ]
            },
        )
    )

    # Request spells with name filter - uses name__icontains parameter
    spells = await v2_client.get_spells(name="fire")

    # Should return all spells matching partial name
    assert len(spells) == 2
    assert {spell.name for spell in spells} == {"Fireball", "Fire Storm"}
    # Verify both spells have "Fire" in their name
    assert all("Fire" in spell.name for spell in spells)


@respx.mock
async def test_partial_name_match(v2_client: Open5eV2Client) -> None:
    """Test that partial name searches work server-side via name__icontains.

    This test verifies that the client properly implements name partial matching
    for common search patterns like searching for "missile" to find "Magic Missile".
    """
    # Mock API that returns spells matching partial name
    respx.get("https://api.open5e.com/v2/spells/?name__icontains=missile").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
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
                    }
                ]
            },
        )
    )

    spells = await v2_client.get_spells(name="missile")

    # Should find "Magic Missile" when searching for "missile"
    assert len(spells) == 1
    assert spells[0].name == "Magic Missile"
    assert "missile" in spells[0].name.lower()


# Task 1.3: Add Range Filter Operators
@respx.mock
async def test_level_range_filtering(v2_client: Open5eV2Client) -> None:
    """Test that get_spells supports level__gte and level__lte range operators.

    Range queries should use server-side filtering with level__gte and level__lte
    parameters instead of client-side filtering.
    """
    # Mock API with level__gte filter for level >= 4
    respx.get("https://api.open5e.com/v2/spells/?level__gte=4").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Polymorph",
                        "slug": "polymorph",
                        "level": 4,
                        "school": "Transmutation",
                        "casting_time": "1 action",
                        "range": "60 feet",
                        "components": "V, S, M",
                        "duration": "Concentration, up to 1 hour",
                        "desc": "This spell transforms a creature...",
                    },
                    {
                        "name": "Cone of Cold",
                        "slug": "cone-of-cold",
                        "level": 5,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "60 feet",
                        "components": "V, S, M",
                        "duration": "Instantaneous",
                        "desc": "A blast of cold...",
                    },
                ]
            },
        )
    )

    spells = await v2_client.get_spells(level_gte=4)

    # Should return spells at level 4 or higher from server
    assert len(spells) == 2
    assert all(spell.level >= 4 for spell in spells)


@respx.mock
async def test_level_range_filtering_lte(v2_client: Open5eV2Client) -> None:
    """Test that get_spells supports level__lte range operator."""
    # Mock API with level__lte filter for level <= 2
    respx.get("https://api.open5e.com/v2/spells/?level__lte=2").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
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
                        "name": "Scorching Ray",
                        "slug": "scorching-ray",
                        "level": 2,
                        "school": "Evocation",
                        "casting_time": "1 action",
                        "range": "120 feet",
                        "components": "V, S",
                        "duration": "Instantaneous",
                        "desc": "A line of fire...",
                    },
                ]
            },
        )
    )

    spells = await v2_client.get_spells(level_lte=2)

    # Should return spells at level 2 or lower from server
    assert len(spells) == 2
    assert all(spell.level <= 2 for spell in spells)


@respx.mock
async def test_cr_range_filtering(v2_client: Open5eV2Client) -> None:
    """Test that get_creatures supports challenge_rating_decimal range operators.

    Challenge rating should support challenge_rating_decimal__gte and
    challenge_rating_decimal__lte for range filtering server-side.
    """
    # Mock API with challenge_rating_decimal__gte filter for CR >= 2.0
    respx.get("https://api.open5e.com/v2/creatures/?challenge_rating_decimal__gte=2.0").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "ogre",
                        "name": "Ogre",
                        "desc": "A large brutish creature...",
                        "size": "Large",
                        "type": "giant",
                        "alignment": "Chaotic Evil",
                        "armor_class": 11,
                        "hit_points": 59,
                        "hit_dice": "7d10+21",
                        "challenge_rating": "2",
                        "challenge_rating_decimal": 2.0,
                    },
                    {
                        "slug": "bugbear",
                        "name": "Bugbear",
                        "desc": "A large goblinoid creature...",
                        "size": "Large",
                        "type": "humanoid",
                        "alignment": "Chaotic Evil",
                        "armor_class": 13,
                        "hit_points": 27,
                        "hit_dice": "5d10+5",
                        "challenge_rating": "3",
                        "challenge_rating_decimal": 3.0,
                    },
                ]
            },
        )
    )

    creatures = await v2_client.get_creatures(challenge_rating_decimal_gte=2.0)

    # Should return creatures with CR >= 2.0 from server
    assert len(creatures) == 2
    for creature in creatures:
        assert creature.challenge_rating_decimal is not None
        assert creature.challenge_rating_decimal >= 2.0


@respx.mock
async def test_cr_range_filtering_lte(v2_client: Open5eV2Client) -> None:
    """Test that get_creatures supports challenge_rating_decimal__lte."""
    # Mock API with challenge_rating_decimal__lte filter for CR <= 1.0
    respx.get("https://api.open5e.com/v2/creatures/?challenge_rating_decimal__lte=1.0").mock(
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
                        "challenge_rating_decimal": 0.25,
                    },
                    {
                        "slug": "orc",
                        "name": "Orc",
                        "desc": "A warrior of the wilds...",
                        "size": "Medium",
                        "type": "humanoid",
                        "alignment": "Chaotic Evil",
                        "armor_class": 13,
                        "hit_points": 15,
                        "hit_dice": "2d8",
                        "challenge_rating": "1/2",
                        "challenge_rating_decimal": 0.5,
                    },
                ]
            },
        )
    )

    creatures = await v2_client.get_creatures(challenge_rating_decimal_lte=1.0)

    # Should return creatures with CR <= 1.0 from server
    assert len(creatures) == 2
    for creature in creatures:
        assert creature.challenge_rating_decimal is not None
        assert creature.challenge_rating_decimal <= 1.0


@respx.mock
async def test_cost_range_filtering(v2_client: Open5eV2Client) -> None:
    """Test that get_weapons/get_armor support cost__gte and cost__lte.

    Cost filtering should support cost__gte and cost__lte for range filtering
    server-side on weapons and armor.
    """
    # Mock API with cost__gte filter for weapons costing >= 50 gp
    respx.get("https://api.open5e.com/v2/weapons/?cost__gte=50").mock(
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
                        "properties": [],
                        "range": 0.0,
                        "long_range": 0.0,
                        "distance_unit": "feet",
                        "is_simple": False,
                        "is_improvised": False,
                        "cost": "15 gp",
                    },
                    {
                        "url": "https://api.open5e.com/v2/weapons/srd-2024_greatsword/",
                        "key": "srd-2024_greatsword",
                        "name": "Greatsword",
                        "slug": "greatsword",
                        "damage_dice": "2d6",
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
                        "cost": "50 gp",
                    },
                ]
            },
        )
    )

    weapons = await v2_client.get_weapons(cost_gte=50)

    # Should return weapons with cost >= 50 gp from server
    assert len(weapons) == 2


@respx.mock
async def test_cost_range_filtering_lte(v2_client: Open5eV2Client) -> None:
    """Test that get_armor supports cost__lte range operator."""
    # Mock API with cost__lte filter for armor costing <= 50 gp
    respx.get("https://api.open5e.com/v2/armor/?cost__lte=50").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Leather",
                        "slug": "leather",
                        "key": "leather",
                        "category": "Light",
                        "base_ac": 11,
                        "cost": "5 gp",
                        "weight": 10.0,
                        "stealth_disadvantage": False,
                    },
                    {
                        "name": "Hide",
                        "slug": "hide",
                        "key": "hide",
                        "category": "Medium",
                        "base_ac": 12,
                        "cost": "10 gp",
                        "weight": 15.0,
                        "stealth_disadvantage": False,
                    },
                ]
            },
        )
    )

    armors = await v2_client.get_armor(cost_lte=50)

    # Should return armor with cost <= 50 gp from server
    assert len(armors) == 2


# Task 3: Document name extraction
@respx.mock
async def test_spell_includes_document_name(v2_client: Open5eV2Client) -> None:
    """Test that spells include document name from API."""
    respx.get("https://api.open5e.com/v2/spells/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "slug": "fireball",
                        "name": "Fireball",
                        "level": 3,
                        "school": {"key": "evocation", "name": "Evocation"},
                        "casting_time": "1 action",
                        "range": "150 feet",
                        "components": "V, S, M",
                        "duration": "Instantaneous",
                        "document": {
                            "key": "srd-2014",
                            "name": "System Reference Document 5.1",
                            "publisher": "Wizards of the Coast",
                        },
                    }
                ]
            },
        )
    )

    spells = await v2_client.get_spells()

    assert len(spells) == 1
    spell_dict = spells[0].model_dump()

    # Verify document name is extracted
    assert spell_dict["document"] == "System Reference Document 5.1"


@respx.mock
async def test_weapon_includes_document_name(v2_client: Open5eV2Client) -> None:
    """Test that weapons include document name from API."""
    respx.get("https://api.open5e.com/v2/weapons/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "key": "srd-2024_longsword",
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
                        "document": {
                            "key": "srd-2024",
                            "name": "System Reference Document 5.2",
                            "publisher": "Wizards of the Coast",
                        },
                    }
                ]
            },
        )
    )

    weapons = await v2_client.get_weapons()

    assert len(weapons) == 1
    weapon_dict = weapons[0].model_dump()

    # Verify document name is extracted
    assert weapon_dict["document"] == "System Reference Document 5.2"


@respx.mock
async def test_armor_includes_document_name(v2_client: Open5eV2Client) -> None:
    """Test that armor includes document name from API."""
    respx.get("https://api.open5e.com/v2/armor/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "key": "leather",
                        "name": "Leather",
                        "category": "Light",
                        "base_ac": 11,
                        "document": {
                            "key": "srd-2024",
                            "name": "System Reference Document 5.2",
                            "publisher": "Wizards of the Coast",
                        },
                    }
                ]
            },
        )
    )

    armors = await v2_client.get_armor()

    assert len(armors) == 1
    armor_dict = armors[0].model_dump()

    # Verify document name is extracted
    assert armor_dict["document"] == "System Reference Document 5.2"


@respx.mock
async def test_creature_includes_document_name(v2_client: Open5eV2Client) -> None:
    """Test that creatures include document name from API."""
    respx.get("https://api.open5e.com/v2/creatures/").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "key": "goblin",
                        "name": "Goblin",
                        "desc": "A small, cunning creature.",
                        "type": {
                            "name": "Humanoid",
                            "key": "humanoid",
                        },
                        "size": {
                            "name": "Small",
                            "key": "small",
                        },
                        "alignment": "neutral evil",
                        "armor_class": [{"type": "armor", "value": 15}],
                        "hit_points": 7,
                        "hit_dice": "2d6",
                        "challenge_rating_text": "1/4",
                        "challenge_rating_decimal": "0.250",
                        "document": {
                            "key": "srd-5e",
                            "name": "Systems Reference Document 5.1",
                            "url": "https://api.open5e.com/v2/documents/srd-5e/",
                        },
                    }
                ]
            },
        )
    )

    creatures = await v2_client.get_creatures()

    assert len(creatures) == 1
    creature_dict = creatures[0].model_dump()

    # Verify document name is extracted
    assert creature_dict["document"] == "Systems Reference Document 5.1"


# Task 2.2: Unified Search Implementation
@respx.mock
async def test_unified_search_method(v2_client: Open5eV2Client) -> None:
    """Test unified_search() method with basic query parameter.

    The unified_search method should call the /v2/search/ endpoint with
    the query parameter and return a list of search results.
    """
    respx.get("https://api.open5e.com/v2/search/?query=fireball").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "document": {"key": "fireball", "name": "Fireball"},
                    "object_pk": "spell-fireball",
                    "object_name": "Fireball",
                    "object": {"level": 3, "school": "Evocation"},
                    "object_model": "Spell",
                    "schema_version": "v2",
                    "route": "v2/spells/",
                    "text": "A bright streak...",
                    "highlighted": "A <em>fireball</em> is...",
                    "match_type": "exact",
                    "matched_term": "fireball",
                    "match_score": 1.0,
                },
                {
                    "document": {
                        "key": "delayed-blast-fireball",
                        "name": "Delayed Blast Fireball",
                    },
                    "object_pk": "spell-delayed-blast-fireball",
                    "object_name": "Delayed Blast Fireball",
                    "object": {"level": 7, "school": "Evocation"},
                    "object_model": "Spell",
                    "schema_version": "v2",
                    "route": "v2/spells/",
                    "text": "A delayed version...",
                    "highlighted": "A delayed <em>fireball</em>...",
                    "match_type": "exact",
                    "matched_term": "fireball",
                    "match_score": 0.95,
                },
            ],
        )
    )

    results = await v2_client.unified_search(query="fireball")

    assert len(results) == 2
    assert results[0]["object_name"] == "Fireball"
    assert results[0]["object_model"] == "Spell"
    assert results[0]["match_type"] == "exact"
    assert results[1]["object_name"] == "Delayed Blast Fireball"


@respx.mock
async def test_fuzzy_parameter(v2_client: Open5eV2Client) -> None:
    """Test unified_search() with fuzzy parameter for typo-tolerant matching.

    The fuzzy parameter should be passed to the API and enable fuzzy matching.
    """
    respx.get("https://api.open5e.com/v2/search/?query=firbal&fuzzy=true").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "document": {"key": "fireball", "name": "Fireball"},
                    "object_pk": "spell-fireball",
                    "object_name": "Fireball",
                    "object": {"level": 3, "school": "Evocation"},
                    "object_model": "Spell",
                    "schema_version": "v2",
                    "route": "v2/spells/",
                    "text": "A bright streak...",
                    "highlighted": "A <em>fireball</em> is...",
                    "match_type": "fuzzy",
                    "matched_term": "firbal",
                    "match_score": 0.857,
                }
            ],
        )
    )

    results = await v2_client.unified_search(query="firbal", fuzzy=True)

    assert len(results) == 1
    assert results[0]["match_type"] == "fuzzy"
    assert results[0]["match_score"] == 0.857


@respx.mock
async def test_vector_parameter(v2_client: Open5eV2Client) -> None:
    """Test unified_search() with vector parameter for semantic search.

    The vector parameter should be passed to the API and enable semantic
    similarity matching for concept-based searching.
    """
    respx.get("https://api.open5e.com/v2/search/?query=healing+magic&vector=true").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "document": {"key": "potion-of-healing", "name": "Potion of Healing"},
                    "object_pk": "item-potion-of-healing",
                    "object_name": "Potion of Healing",
                    "object": {"rarity": "common"},
                    "object_model": "Item",
                    "schema_version": "v2",
                    "route": "v2/items/",
                    "text": "You regain 4d4+4 HP...",
                    "highlighted": "<em>Healing</em> potion",
                    "match_type": "vector",
                    "matched_term": "healing magic",
                    "match_score": 0.92,
                },
                {
                    "document": {"key": "cure-wounds", "name": "Cure Wounds"},
                    "object_pk": "spell-cure-wounds",
                    "object_name": "Cure Wounds",
                    "object": {"level": 1, "school": "Evocation"},
                    "object_model": "Spell",
                    "schema_version": "v2",
                    "route": "v2/spells/",
                    "text": "A spell to cure wounds...",
                    "highlighted": "<em>Cure</em> wounds spell",
                    "match_type": "vector",
                    "matched_term": "healing magic",
                    "match_score": 0.88,
                },
            ],
        )
    )

    results = await v2_client.unified_search(query="healing magic", vector=True)

    assert len(results) == 2
    assert all(r["match_type"] == "vector" for r in results)
    assert results[0]["object_model"] == "Item"
    assert results[1]["object_model"] == "Spell"


@respx.mock
async def test_object_model_filter(v2_client: Open5eV2Client) -> None:
    """Test unified_search() with object_model parameter to filter by content type.

    The object_model parameter should filter results to only the specified
    content type (e.g., "Spell", "Creature", "Item").
    """
    respx.get("https://api.open5e.com/v2/search/?query=dragon&object_model=Creature").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "document": {"key": "dragon-prismatic", "name": "Dragon Prismatic"},
                    "object_pk": "creature-dragon-prismatic",
                    "object_name": "Dragon Prismatic",
                    "object": {"size": "Huge", "challenge_rating": "20"},
                    "object_model": "Creature",
                    "schema_version": "v2",
                    "route": "v2/creatures/",
                    "text": "A majestic dragon...",
                    "highlighted": "A dragon with all colors",
                    "match_type": "exact",
                    "matched_term": "dragon",
                    "match_score": 1.0,
                },
                {
                    "document": {"key": "dragon-green", "name": "Dragon Green"},
                    "object_pk": "creature-dragon-green",
                    "object_name": "Dragon Green",
                    "object": {"size": "Huge", "challenge_rating": "18"},
                    "object_model": "Creature",
                    "schema_version": "v2",
                    "route": "v2/creatures/",
                    "text": "A green colored dragon...",
                    "highlighted": "A green <em>dragon</em>",
                    "match_type": "exact",
                    "matched_term": "dragon",
                    "match_score": 0.98,
                },
            ],
        )
    )

    results = await v2_client.unified_search(query="dragon", object_model="Creature")

    assert len(results) == 2
    assert all(r["object_model"] == "Creature" for r in results)
    assert results[0]["object_name"] == "Dragon Prismatic"
    assert results[1]["object_name"] == "Dragon Green"
