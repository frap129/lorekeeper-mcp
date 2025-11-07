"""Creature lookup tool."""

from typing import Any

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client

# Simple in-memory cache for creature lookups (max 128 entries)
_creature_cache: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
_creature_cache_maxsize = 128


def clear_creature_cache() -> None:
    """Clear the in-memory creature cache."""
    _creature_cache.clear()


async def lookup_creature(
    name: str | None = None,
    cr: float | None = None,
    cr_min: float | None = None,
    cr_max: float | None = None,
    type: str | None = None,  # noqa: A002
    size: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search and retrieve D&D 5e creatures/monsters from the Open5e v1 API.

    This tool provides comprehensive creature lookup including full stat blocks, combat
    statistics, abilities, and special features. Perfect for finding NPCs, monsters,
    and encounters of specific difficulty levels. Results are cached for better performance.

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
        limit: Maximum number of results to return. Default 20 for pagination
            and performance. Examples: 5, 50, 100

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
            - saving_throws: Saving throw bonuses if any
            - skills: Skill bonuses if any
            - senses: Senses available (darkvision, passive perception, etc.)
            - challenge_rating: CR value for encounter building
            - traits: Special traits and features
            - actions: Possible actions in combat
            - reactions: Reaction abilities
            - legendary_actions: Legendary action options (if applicable)
            - document__slug: Source document reference

    Raises:
        APIError: If the API request fails due to network issues or server errors
    """
    # Check in-memory cache first
    cache_key = (name, cr, cr_min, cr_max, type, size, limit)
    if cache_key in _creature_cache:
        return _creature_cache[cache_key]

    client = Open5eV1Client()

    # Build query parameters
    params: dict[str, Any] = {"limit": limit}
    if name is not None:
        params["search"] = name
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

    response = await client.get_monsters(**params)

    # Convert Monster objects to dictionaries
    result = [creature.model_dump() for creature in response]

    # Cache the result in memory
    if len(_creature_cache) >= _creature_cache_maxsize:
        # Simple FIFO eviction
        _creature_cache.pop(next(iter(_creature_cache)))
    _creature_cache[cache_key] = result

    return result
