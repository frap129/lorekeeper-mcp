"""Creature lookup tool with repository pattern."""

from typing import Any

from lorekeeper_mcp.repositories.factory import RepositoryFactory


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
    limit: int = 20,
    repository: Any = None,
) -> list[dict[str, Any]]:
    """
    Search and retrieve D&D 5e creatures/monsters using the repository pattern.

    This tool provides comprehensive creature lookup including full stat blocks, combat
    statistics, abilities, and special features. Results include complete creature data
    and are cached through the repository for improved performance.

    Examples:
        - lookup_creature(name="dragon") - Find all creatures with "dragon" in name
        - lookup_creature(cr=5) - Find all creatures with CR 5 (encounter challenge level)
        - lookup_creature(cr_min=1, cr_max=3, type="undead") - Find undead creatures CR 1-3
        - lookup_creature(size="Tiny") - Find all tiny creatures for swarms
        - lookup_creature(type="humanoid", cr_max=2) - Find low-level humanoid NPCs

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
        limit: Maximum number of results to return. Default 20, useful for pagination
            or limiting large result sets. Example: 5
        repository: Optional MonsterRepository instance for dependency injection.
            Defaults to RepositoryFactory.create_monster_repository()

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
    # Use provided repository or create default
    if repository is None:
        repository = RepositoryFactory.create_monster_repository()

    # Build query parameters for repository search
    # Note: name/search filtering happens client-side since the API doesn't filter by search
    params: dict[str, Any] = {}
    if cr is not None:
        params["cr"] = cr
    if cr_min is not None:
        params["cr_min"] = cr_min
    if cr_max is not None:
        params["cr_max"] = cr_max
    if type is not None:
        params["type"] = type
    if size is not None:
        params["size"] = size

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
