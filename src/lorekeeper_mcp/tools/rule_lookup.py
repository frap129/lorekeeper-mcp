"""Rule lookup tool using the repository pattern for caching.

This module provides comprehensive D&D 5e game rules, conditions, and reference
information with automatic database caching through the repository pattern. The
repository abstracts away cache management and handles multi-type rule routing.

Architecture:
    - Uses RuleRepository for cache-aside pattern with rule-type routing
    - Repository manages SQLite cache automatically
    - Supports dependency injection for testing
    - Handles rule, condition, damage-type, skill, and other reference data filtering

Examples:
    Default usage (automatically creates repository):
        conditions = await lookup_rule(rule_type="condition")
        skills = await lookup_rule(rule_type="skill", name="stealth")

    With custom repository (dependency injection):
        from lorekeeper_mcp.repositories.rule import RuleRepository
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        cache = SQLiteCache(db_path="/path/to/cache.db")
        repository = RuleRepository(cache=cache)
        rules = await lookup_rule(rule_type="rule", repository=repository)

    Reference data queries:
        abilities = await lookup_rule(rule_type="ability-score")
        damage_types = await lookup_rule(rule_type="damage-type")
        alignments = await lookup_rule(rule_type="alignment")"""

from typing import Any, Literal, cast

from lorekeeper_mcp.repositories.factory import RepositoryFactory
from lorekeeper_mcp.repositories.rule import RuleRepository

# Module-level context for test repository injection
_repository_context: dict[str, Any] = {}


def _get_repository() -> RuleRepository:
    """Get rule repository, respecting test context.

    Returns the repository from _repository_context if set, otherwise creates
    a default RuleRepository using RepositoryFactory.

    Returns:
        RuleRepository instance for rule lookups.
    """
    if "repository" in _repository_context:
        return cast(RuleRepository, _repository_context["repository"])
    return RepositoryFactory.create_rule_repository()


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
    Uses the repository pattern with database caching for improved performance.

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

    # Get repository from context or create default
    repository = _get_repository()

    # Build query parameters for repository search
    params: dict[str, Any] = {"rule_type": rule_type}
    if name is not None:
        params["name"] = name
    if limit is not None:
        params["limit"] = limit
    if rule_type == "rule" and section is not None:
        params["section"] = section

    # Fetch rules from repository with routing
    return await repository.search(**params)
