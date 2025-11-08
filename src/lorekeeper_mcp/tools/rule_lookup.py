"""Rule lookup tool."""

from typing import Any, Literal

try:
    from typing import assert_never
except ImportError:
    from typing import assert_never

from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

RuleType = Literal[
    "rule",
    "condition",
    "damage-type",
    "weapon-property",
    "skill",
    "ability-score",
    "magic-school",
    "language",
    "proficiency",
    "alignment",
]


async def lookup_rule(
    rule_type: RuleType,
    name: str | None = None,
    section: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Look up D&D 5e game rules, conditions, and reference information.

    This comprehensive reference tool provides access to core rules, special conditions,
    damage types, skills, and game mechanics. Essential for resolving rules questions
    during play or character building. All data is sourced from official D&D 5e materials.

    Examples:
        - lookup_rule(rule_type="condition", name="grappled") - Find grappled condition rules
        - lookup_rule(rule_type="skill", name="stealth") - Find stealth skill details
        - lookup_rule(rule_type="damage-type", name="fire") - Find fire damage rules
        - lookup_rule(rule_type="rule", section="combat") - Find all combat rules
        - lookup_rule(rule_type="ability-score") - Get all ability score info
        - lookup_rule(rule_type="alignment") - Find alignment descriptions
        - lookup_rule(rule_type="magic-school", name="evocation") - Find evocation school info

    Args:
        rule_type: **REQUIRED.** Type of game reference to lookup. Must be one of:
            - "rule": Core game rules and mechanics (combat, spellcasting, movement, etc.)
            - "condition": Status effects (grappled, stunned, poisoned, unconscious, etc.)
            - "damage-type": Damage categories (acid, bludgeoning, cold, fire, force,
              lightning, necrotic, piercing, poison, psychic, radiant, slashing, thunder)
            - "weapon-property": Weapon special properties (finesse, heavy, light, reach,
              two-handed, versatile, ammunition, loading, thrown, etc.)
            - "skill": Ability-based skills (Acrobatics, Animal Handling, Arcana, Athletics,
              Deception, History, Insight, Intimidation, Investigation, Medicine, Nature,
              Perception, Performance, Persuasion, Religion, Sleight of Hand, Stealth, Survival)
            - "ability-score": Core abilities (Strength, Dexterity, Constitution, Intelligence,
              Wisdom, Charisma) and their uses
            - "magic-school": Schools of magic (Abjuration, Conjuration, Divination, Enchantment,
              Evocation, Illusion, Necromancy, Transmutation)
            - "language": Languages available in D&D (Common, Dwarvish, Elvish, Giant, Gnomish,
              Goblin, Orc, Primordial, Sylvan, Undercommon, Celestial, Draconic, Deep Speech, Infernal)
            - "proficiency": Character proficiency types (armor, weapon, tool, saving throw, skill)
            - "alignment": Character alignment axes (Lawful/Chaotic, Good/Evil, Neutral options)
        name: Optional name or partial name search for filtering results. Matches entries
            containing this substring. Case-insensitive matching.
            Examples: "grappled" for conditions, "fire" for damage types, "stealth" for skills
        section: For rule_type="rule" only. Filter rules by section/chapter.
            Examples: "combat", "spellcasting", "movement", "actions-in-combat"
            Ignored for other rule types.
        limit: Maximum number of results to return. Default 20 for performance.
            Examples: 1, 10, 50

    Returns:
        List of rule/reference dictionaries. Structure varies by rule_type:

        For rule_type="rule":
            - name: Rule name/title
            - desc: Full rule description and examples
            - section: Section/chapter this rule belongs to

        For rule_type="condition":
            - name: Condition name
            - desc: Effects and duration of this condition

        For rule_type="damage-type":
            - name: Damage type name
            - desc: Description of damage type and uses

        For rule_type="weapon-property":
            - name: Property name
            - desc: How the property affects weapon use

        For rule_type="skill":
            - name: Skill name
            - ability_score: Associated ability (STR, DEX, CON, INT, WIS, CHA)
            - desc: How skill is used and common checks

        For rule_type="ability-score":
            - name: Ability name
            - desc: What ability represents and how it's used
            - skills: Related skills

        For rule_type="magic-school":
            - name: School name
            - desc: Philosophy and types of spells in this school

        For rule_type="language":
            - name: Language name
            - type: Language type (common, exotic, etc.)
            - script: Writing system if any

        For rule_type="proficiency":
            - name: Proficiency type
            - class: What type of proficiency (class, background, race)
            - desc: Details about this proficiency type

        For rule_type="alignment":
            - name: Alignment
            - desc: Alignment description and common character types

    Raises:
        ValueError: If rule_type is not one of the valid options
        APIError: If the API request fails due to network issues or server errors
    """
    valid_types = {
        "rule",
        "condition",
        "damage-type",
        "weapon-property",
        "skill",
        "ability-score",
        "magic-school",
        "language",
        "proficiency",
        "alignment",
    }
    if rule_type not in valid_types:
        raise ValueError(
            f"Invalid type '{rule_type}'. Must be one of: {', '.join(sorted(valid_types))}"
        )

    params: dict[str, Any] = {}
    if name is not None:
        params["name"] = name
    if limit is not None:
        params["limit"] = limit

    # Route to appropriate client and endpoint
    if rule_type == "condition":
        client = Open5eV2Client()
        return await client.get_conditions(**params)

    # All other types use D&D 5e API
    dnd5e_client = Dnd5eApiClient()

    # Add section parameter for rules
    if rule_type == "rule" and section is not None:
        params["section"] = section

    # Call appropriate method
    if rule_type == "rule":
        return await dnd5e_client.get_rules(**params)
    if rule_type == "damage-type":
        return await dnd5e_client.get_damage_types(**params)
    if rule_type == "weapon-property":
        return await dnd5e_client.get_weapon_properties(**params)
    if rule_type == "skill":
        return await dnd5e_client.get_skills(**params)
    if rule_type == "ability-score":
        return await dnd5e_client.get_ability_scores(**params)
    if rule_type == "magic-school":
        return await dnd5e_client.get_magic_schools(**params)
    if rule_type == "language":
        return await dnd5e_client.get_languages(**params)
    if rule_type == "proficiency":
        return await dnd5e_client.get_proficiencies(**params)
    if rule_type == "alignment":
        return await dnd5e_client.get_alignments(**params)

    assert_never(rule_type)
