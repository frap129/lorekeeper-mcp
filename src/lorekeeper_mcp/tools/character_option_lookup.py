"""Character option lookup tool using the repository pattern for caching.

This module provides character creation and advancement options (classes, races,
backgrounds, feats) with automatic database caching through the repository pattern.
The repository abstracts away cache management and handles multi-source data routing.

Architecture:
    - Uses CharacterOptionRepository for cache-aside pattern with option-type routing
    - Repository manages SQLite cache automatically
    - Supports dependency injection for testing
    - Handles class, race, background, and feat filtering across sources

Examples:
    Default usage (automatically creates repository):
        classes = await lookup_character_option(type="class")
        elves = await lookup_character_option(type="race", name="elf")

    With context-based injection (testing):
        from lorekeeper_mcp.tools.character_option_lookup import _repository_context
        from lorekeeper_mcp.repositories.character_option import CharacterOptionRepository

        repository = CharacterOptionRepository(cache=my_cache)
        _repository_context["repository"] = repository
        feats = await lookup_character_option(type="feat")

    Character building queries:
        all_classes = await lookup_character_option(type="class")
        backgrounds = await lookup_character_option(type="background", name="soldier")"""

from typing import Any, Literal, cast

from lorekeeper_mcp.repositories.character_option import CharacterOptionRepository
from lorekeeper_mcp.repositories.factory import RepositoryFactory

OptionType = Literal["class", "race", "background", "feat"]

# Module-level context for test repository injection
_repository_context: dict[str, Any] = {}


def _get_repository() -> CharacterOptionRepository:
    """Get character option repository, respecting test context.

    Returns the repository from _repository_context if set, otherwise creates
    a default CharacterOptionRepository using RepositoryFactory.

    Returns:
        CharacterOptionRepository instance for character option lookups.
    """
    if "repository" in _repository_context:
        return cast(CharacterOptionRepository, _repository_context["repository"])
    return RepositoryFactory.create_character_option_repository()


async def lookup_character_option(
    type: OptionType,  # noqa: A002
    name: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Retrieve D&D 5e character creation and advancement options.

    This tool provides access to classes, races, backgrounds, and feats for character
    creation and level-up decisions. Each option type provides different information
    relevant to character building. Results are cached for faster repeated lookups
    through the repository pattern.

    The repository pattern handles caching transparently:
    - First call: Fetches from API and caches in database
    - Subsequent calls: Returns cached results if available
    - Supports test context-based repository injection via _repository_context

    Examples:
        Default usage (automatic repository creation):
            classes = await lookup_character_option(type="class")
            elves = await lookup_character_option(type="race", name="elf")
            backgrounds = await lookup_character_option(type="background", name="soldier")
            feats = await lookup_character_option(type="feat", name="great")

        With test context injection (testing):
            from lorekeeper_mcp.tools.character_option_lookup import _repository_context
            custom_repo = CharacterOptionRepository(cache=my_cache)
            _repository_context["repository"] = custom_repo
            classes = await lookup_character_option(type="class")

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
        ApiError: If the API request fails due to network issues or server errors
    """
    valid_types = {"class", "race", "background", "feat"}
    if type not in valid_types:
        raise ValueError(f"Invalid type '{type}'. Must be one of: {', '.join(valid_types)}")

    # Get repository from context or create default
    repository = _get_repository()

    # Build query parameters for repository search
    params: dict[str, Any] = {
        "option_type": type,
        "limit": limit,
    }
    # Note: search/name filtering is done client-side, not passed to cache
    # The cache layer doesn't support filtering by name

    # Fetch options from repository
    results: list[dict[str, Any]] = await repository.search(**params)

    # Client-side name filtering if requested
    if name is not None and results:
        name_lower = name.lower()
        results = [r for r in results if name_lower in r.get("name", "").lower()]

    return results
