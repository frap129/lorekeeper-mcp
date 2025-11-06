"""Character option lookup tool."""

from typing import Any, Literal

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

OptionType = Literal["class", "race", "background", "feat"]


async def lookup_character_option(
    type: OptionType,  # noqa: A002
    name: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Retrieve D&D 5e character creation and advancement options.

    This tool provides access to classes, races, backgrounds, and feats for character
    creation and level-up decisions. Each option type provides different information
    relevant to character building. Results are cached for faster repeated lookups.

    Examples:
        - lookup_character_option(type="class", name="wizard") - Find wizard class details
        - lookup_character_option(type="race", name="elf") - Find elf racial bonuses
        - lookup_character_option(type="background", name="soldier") - Find soldier background
        - lookup_character_option(type="feat", name="great") - Find feats with "great" in name
        - lookup_character_option(type="class") - Get all available classes

    Args:
        type: **REQUIRED.** Character option type. Must be one of:
            - "class": Player classes (Barbarian, Bard, Cleric, Druid, Fighter, Monk,
              Paladin, Ranger, Rogue, Sorcerer, Warlock, Wizard)
            - "race": Playable races (Human, Elf, Dwarf, Halfling, Dragonborn, Gnome,
              Half-Orc, Half-Elf, Tiefling, etc.)
            - "background": Character backgrounds (Acolyte, Criminal, Entertainer, Soldier,
              Folk Hero, Sage, etc.)
            - "feat": Character feats (Ability Score Improvement, Great Weapon Master,
              Magic Initiate, etc.) - typically chosen at levels 4, 8, 12, 16, 19
        name: Optional name or partial name search. Filters options containing this substring.
            Examples: "ranger" for classes, "dragon" for feats, "noble" for backgrounds
            Case-insensitive matching.
        limit: Maximum number of results to return. Default 20, useful for limiting
            output or pagination. Examples: 1, 5, 50

    Returns:
        List of option dictionaries. Structure varies by type:

        For type="class":
            - name: Class name
            - hit_dice: Hit die value (1d8, 1d10, 1d12)
            - class_levels: Progression table
            - spellcasting: Spell slots if applicable
            - features: Class features by level

        For type="race":
            - name: Race name
            - ability_score_increase: Ability score bonuses
            - age: Aging information
            - alignment: Typical alignments
            - size: Size category
            - speed: Movement speed
            - languages: Known languages
            - traits: Racial traits and special abilities

        For type="background":
            - name: Background name
            - skill_proficiencies: Skill choices
            - tool_proficiencies: Tools (if any)
            - feature: Special background feature
            - personality_traits: Suggested personality options
            - ideals: Suggested ideals
            - bonds: Suggested character bonds
            - flaws: Suggested character flaws

        For type="feat":
            - name: Feat name
            - description: Feat benefits and requirements
            - ability_score_increase: Ability bonuses (if any)
            - prerequisites: Requirements to take feat

    Raises:
        ValueError: If type parameter is not one of the valid options
        APIError: If the API request fails due to network issues or server errors
    """
    valid_types = {"class", "race", "background", "feat"}
    if type not in valid_types:
        raise ValueError(f"Invalid type '{type}'. Must be one of: {', '.join(valid_types)}")

    params: dict[str, Any] = {"limit": limit}
    if name is not None:
        params["name"] = name

    # Route to appropriate client and endpoint
    if type == "class":
        v1_client = Open5eV1Client()
        response = await v1_client.get_classes(**params)
    elif type == "race":
        v1_client = Open5eV1Client()
        response = await v1_client.get_races(**params)
    elif type == "background":
        v2_client = Open5eV2Client()
        response = await v2_client.get_backgrounds(**params)
    else:  # type == "feat"
        v2_client = Open5eV2Client()
        response = await v2_client.get_feats(**params)

    return response
