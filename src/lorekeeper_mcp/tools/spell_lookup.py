"""Spell lookup tool using the repository pattern for caching.

This module provides spell lookup functionality with automatic database caching
through the repository pattern. The repository abstracts away cache management,
allowing you to focus on spell searching. Cache misses automatically fetch from
the D&D 5e API and store results for future queries.

Architecture:
    - Uses SpellRepository for cache-aside pattern
    - Repository manages SQLite cache automatically
    - Supports dependency injection for testing

Examples:
    Default usage (automatically creates repository):
        spells = await lookup_spell(level=3, school="evocation")

    With custom repository (dependency injection):
        from lorekeeper_mcp.repositories.spell import SpellRepository
        from lorekeeper_mcp.cache.sqlite import SQLiteCache

        cache = SQLiteCache(db_path="/path/to/cache.db")
        repository = SpellRepository(cache=cache)
        spells = await lookup_spell(level=3, repository=repository)

    Name search with filtering:
        spells = await lookup_spell(name="fireball", limit=5)

    Advanced filtering:
        spells = await lookup_spell(level=0, class_key="wizard")"""

from typing import Any

from lorekeeper_mcp.repositories.factory import RepositoryFactory


def clear_spell_cache() -> None:
    """Clear the spell cache (deprecated).

    This function is deprecated and kept for backward compatibility.
    Cache management is now handled by the repository pattern with
    database-backed persistence.
    """
    # No-op: in-memory caching is no longer used


async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    school: str | None = None,
    class_key: str | None = None,
    concentration: bool | None = None,
    ritual: bool | None = None,
    casting_time: str | None = None,
    limit: int = 20,
    repository: Any = None,
) -> list[dict[str, Any]]:
    """
    Search and retrieve D&D 5e spells using the repository pattern.

    This tool provides comprehensive spell lookup functionality with support for filtering
    by multiple criteria. Results include complete spell descriptions, components, damage,
    effects, and availability information. Automatically uses the database cache through
    the repository for improved performance.

    The repository pattern handles caching transparently:
    - First call: Fetches from API and caches in database
    - Subsequent calls: Returns cached results if available
    - Supports dependency injection for testing with custom repositories

    Examples:
        Default usage (automatic repository creation):
            spells = await lookup_spell(name="fireball")
            spells = await lookup_spell(level=3, school="evocation")
            spells = await lookup_spell(class_key="wizard", concentration=True)

        With dependency injection (custom repository):
            from lorekeeper_mcp.repositories.spell import SpellRepository
            custom_repo = SpellRepository(cache=my_cache)
            spells = await lookup_spell(level=0, repository=custom_repo)

        Finding specific spell types:
            cantrips = await lookup_spell(level=0)
            ritual_spells = await lookup_spell(ritual=True)
            action_spells = await lookup_spell(casting_time="1 action")

    Args:
        name: Spell name or partial name search. Matches spells containing this substring.
            Example: "fireball", "magic", "shield"
        level: Spell level ranging from 0-9, where 0 represents cantrips/0-level spells
            and 9 represents 9th level spells. Example: 3 for 3rd level spells
        school: Magic school filter. Valid values: abjuration, conjuration, divination,
            enchantment, evocation, illusion, necromancy, transmutation
            Example: "evocation" for damage-dealing spells
        class_key: Filter spells available to a specific class. Valid values: wizard, cleric,
            druid, bard, paladin, ranger, sorcerer, warlock, artificer
            Example: "wizard" for spells in the wizard spell list
        concentration: Filter for spells requiring concentration. True returns only concentration
            spells, False returns only non-concentration spells. Example: True
        ritual: Filter for ritual spells. True returns spells that can be cast as rituals.
            Example: True
        casting_time: Casting time filter for spells. Examples: "1 action", "1 bonus action",
            "1 reaction", "1 minute", "10 minutes"
        limit: Maximum number of results to return. Default 20, useful for pagination
            or limiting large result sets. Example: 5
        repository: Optional SpellRepository instance for dependency injection.
            If not provided, RepositoryFactory.create_spell_repository() creates a default
            instance with automatic database cache management. Useful for testing with
            mocked repositories or custom cache configurations.

    Returns:
        List of spell dictionaries, each containing:
            - name: Spell name
            - level: Spell level (0-9)
            - school: Magic school
            - casting_time: How long the spell takes to cast
            - range: Spell range/area of effect
            - components: Required components (V/S/M)
            - material: Material component description (if applicable)
            - duration: How long the spell lasts
            - concentration: Whether spell requires concentration
            - ritual: Whether spell can be cast as a ritual
            - desc: Full spell description and effects
            - higher_level: Effect when cast at higher levels
            - classes: List of classes that can learn this spell
            - document__slug: Source document reference

    Raises:
        ApiError: If the API request fails due to network issues or server errors
    """
    # Use provided repository or create default
    if repository is None:
        repository = RepositoryFactory.create_spell_repository()

    # Build query parameters for repository search
    # Note: name/search filtering happens client-side since the API doesn't filter by search
    params: dict[str, Any] = {}
    if level is not None:
        params["level"] = level
    if school is not None:
        params["school"] = school
    if class_key is not None:
        params["class_key"] = class_key
    if concentration is not None:
        params["concentration"] = concentration
    if ritual is not None:
        params["ritual"] = ritual
    if casting_time is not None:
        params["casting_time"] = casting_time

    # Fetch spells from repository with filters
    # When searching by name, fetch more results to ensure we find matches
    # Use multiplier of 11 to balance finding matches with performance (~2.5s for 220 results)
    fetch_limit = limit * 11 if name else limit
    spells = await repository.search(limit=fetch_limit, **params)

    # Client-side filtering by name (the API search parameter doesn't actually filter)
    if name:
        name_lower = name.lower()
        spells = [spell for spell in spells if name_lower in spell.name.lower()]

    # Limit results to requested count
    spells = spells[:limit]

    return [spell.model_dump() for spell in spells]
