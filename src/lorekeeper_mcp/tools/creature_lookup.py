"""Creature lookup tool using the repository pattern for caching.

This module provides creature/monster lookup functionality with automatic database
caching through the repository pattern. The repository abstracts away cache management,
allowing you to focus on creature searching. Cache misses automatically fetch from
multiple D&D 5e sources and store results for future queries.

Architecture:
    - Uses MonsterRepository for cache-aside pattern with multi-source support
    - Repository manages SQLite cache automatically
    - Supports test context-based repository injection
    - Handles Open5e v1 and D&D 5e API data normalization

Examples:
    Default usage (automatically creates repository):
        creatures = await lookup_creature(cr=5)
        dragons = await lookup_creature(type="dragon")

    With context-based injection (testing):
        from lorekeeper_mcp.tools.creature_lookup import _repository_context
        from lorekeeper_mcp.repositories.monster import MonsterRepository

        repository = MonsterRepository(cache=my_cache)
        _repository_context["repository"] = repository
        creatures = await lookup_creature(cr_min=1, cr_max=3)

    Challenge rating queries:
        low_level = await lookup_creature(cr_max=2)
        bosses = await lookup_creature(cr_min=10)"""

from typing import Any, cast

from lorekeeper_mcp.repositories.factory import RepositoryFactory
from lorekeeper_mcp.repositories.monster import MonsterRepository

# Module-level context for test repository injection
_repository_context: dict[str, Any] = {}


def _get_repository() -> MonsterRepository:
    """Get monster repository, respecting test context.

    Returns the repository from _repository_context if set, otherwise creates
    a default MonsterRepository using RepositoryFactory.

    Returns:
        MonsterRepository instance for creature lookups.
    """
    if "repository" in _repository_context:
        return cast(MonsterRepository, _repository_context["repository"])
    return RepositoryFactory.create_monster_repository()


def clear_creature_cache() -> None:
    """Clear the creature cache (deprecated).

    This function is deprecated and kept for backward compatibility.
    Cache management is now handled by the repository pattern with
    database-backed persistence.
    """
    # No-op: in-memory caching is no longer used


async def lookup_creature(
    name: str | None = None,
    cr: float | None = None,
    cr_min: float | None = None,
    cr_max: float | None = None,
    type: str | None = None,  # noqa: A002
    size: str | None = None,
    armor_class_min: int | None = None,
    hit_points_min: int | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search and retrieve D&D 5e creatures/monsters using the repository pattern.

    This tool provides comprehensive creature lookup including full stat blocks, combat
    statistics, abilities, and special features. Results include complete creature data
    and are cached through the repository for improved performance.

    Examples:
        Basic creature lookup:
            creatures = await lookup_creature(name="dragon")
            creatures = await lookup_creature(cr=5)
            medium_creatures = await lookup_creature(size="Medium")

        Using challenge rating ranges:
            low_cr_creatures = await lookup_creature(cr_max=2)
            mid_level_threats = await lookup_creature(cr_min=3, cr_max=5)
            deadly_bosses = await lookup_creature(cr_min=10)

        Filtering by type and size:
            undead_creatures = await lookup_creature(type="undead")
            humanoids = await lookup_creature(type="humanoid", cr_max=2)
            large_creatures = await lookup_creature(size="Large", limit=10)

        Using armor class and hit points filters (NEW in Phase 3):
            well_armored_creatures = await lookup_creature(armor_class_min=15)
            heavily_armored = await lookup_creature(armor_class_min=18)
            tanky_creatures = await lookup_creature(hit_points_min=100)
            deadly_tanky = await lookup_creature(
                armor_class_min=16, hit_points_min=75, cr_min=5
            )

        With test context injection (testing):
            from lorekeeper_mcp.tools.creature_lookup import _repository_context
            custom_repo = MonsterRepository(cache=my_cache)
            _repository_context["repository"] = custom_repo
            creatures = await lookup_creature(size="Tiny")

    Args:
        name: Creature name or partial name search. Matches creatures containing this substring.
            Examples: "dragon", "goblin", "lich", "red dragon"
        cr: Exact Challenge Rating to search for. Supports fractional values including
            0.125, 0.25, 0.5 for weak creatures. Range: 0.125 to 30
            Examples: 0.125 (weak minion), 5 (party challenge), 20 (deadly boss)
        cr_min: Minimum Challenge Rating for range-based searches. Use with cr_max to find
            creatures in a difficulty band. Examples: 1, 5, 10
        cr_max: Maximum Challenge Rating for range-based searches. Together with cr_min,
            defines the encounter difficulty band. Examples: 3, 10, 15
        type: Creature type filter. Valid values include: aberration, beast, celestial,
            construct, dragon, elemental, fey, fiend, giant, goblinoid, humanoid, monstrosity,
            ooze, reptile, undead, plant. Examples: "dragon", "undead", "humanoid"
        size: Size category filter. Valid values: Tiny, Small, Medium, Large, Huge, Gargantuan
            Examples: "Large" for major encounters, "Tiny" for swarms
        armor_class_min: Minimum Armor Class filter. Returns creatures with AC at or above
            this value. Useful for finding well-armored threats. Examples: 15, 18, 20
        hit_points_min: Minimum Hit Points filter. Returns creatures with HP at or above
            this value. Useful for finding creatures with significant endurance. Examples: 50, 100,
            200
        limit: Maximum number of results to return. Default 20, useful for pagination
            or limiting large result sets. Example: 5

    Returns:
        List of creature stat block dictionaries, each containing:
            - name: Creature name
            - size: Size category
            - type: Creature type
            - alignment: Alignment (e.g., "chaotic evil")
            - armor_class: AC (Armor Class)
            - hit_points: Hit points
            - hit_dice: Hit dice expression (e.g., "10d10+20")
            - speed: Movement speeds (walk, fly, swim, burrow, climb)
            - strength/dexterity/constitution/intelligence/wisdom/charisma: Ability scores
            - challenge_rating: CR value for encounter building
            - actions: Possible actions in combat
            - legendary_actions: Legendary action options (if applicable)
            - special_abilities: Special abilities and traits
            - document_url: Source document reference

    Raises:
        ApiError: If the API request fails due to network issues or server errors
    """
    # Get repository from context or create default
    repository = _get_repository()

    # Build query parameters for repository search
    # Note: name/search filtering happens client-side since the API doesn't filter by search
    params: dict[str, Any] = {}
    if cr is not None:
        # Map 'cr' parameter to 'challenge_rating' for cache compatibility
        # Convert to float to match database schema (REAL type)
        params["challenge_rating"] = float(cr)
    if cr_min is not None:
        params["cr_min"] = cr_min
    if cr_max is not None:
        params["cr_max"] = cr_max
    if type is not None:
        params["type"] = type
    if size is not None:
        params["size"] = size
    if armor_class_min is not None:
        params["armor_class_min"] = armor_class_min
    if hit_points_min is not None:
        params["hit_points_min"] = hit_points_min

    # Fetch creatures from repository with filters
    # When searching by name, fetch more results to ensure we find matches
    # Use multiplier of 11 to balance finding matches with performance
    fetch_limit = limit * 11 if name else limit
    creatures = await repository.search(limit=fetch_limit, **params)

    # Client-side filtering by name (the API search parameter doesn't actually filter)
    if name:
        name_lower = name.lower()
        creatures = [creature for creature in creatures if name_lower in creature.name.lower()]

    # Limit results to requested count
    creatures = creatures[:limit]

    return [creature.model_dump() for creature in creatures]
