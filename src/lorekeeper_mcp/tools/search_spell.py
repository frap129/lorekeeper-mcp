"""Spell search tool with hybrid semantic and structured filtering.

This module provides spell lookup functionality using both semantic/vector search
and structured filtering through the repository pattern.

Architecture:
    - Uses SpellRepository for cache-aside pattern
    - Repository manages Milvus cache automatically
    - Supports test context-based repository injection

Examples:
    Default usage (automatically creates repository):
        spells = await search_spell(level=3, school="evocation")

    With context-based injection (testing):
        from lorekeeper_mcp.tools.search_spell import _repository_context
        from lorekeeper_mcp.repositories.spell import SpellRepository

        repository = SpellRepository(cache=my_cache)
        _repository_context["repository"] = repository
        spells = await search_spell(level=3)

    Name search with filtering:
        spells = await search_spell(search="fireball", limit=5)

    Advanced filtering:
        spells = await search_spell(level=0, class_key="wizard")"""

from typing import Any, cast

from lorekeeper_mcp.repositories.factory import RepositoryFactory
from lorekeeper_mcp.repositories.spell import SpellRepository

_repository_context: dict[str, Any] = {}


def _get_repository() -> SpellRepository:
    """Get spell repository, respecting test context.

    Returns the repository from _repository_context if set, otherwise creates
    a default SpellRepository using RepositoryFactory.

    Returns:
        SpellRepository instance for spell lookups.
    """
    if "repository" in _repository_context:
        return cast(SpellRepository, _repository_context["repository"])
    return RepositoryFactory.create_spell_repository()


async def search_spell(
    level: int | None = None,
    level_min: int | None = None,
    level_max: int | None = None,
    school: str | None = None,
    class_key: str | None = None,
    concentration: bool | None = None,
    ritual: bool | None = None,
    casting_time: str | None = None,
    damage_type: str | None = None,
    documents: list[str] | None = None,
    search: str | None = None,
    limit: int = 20,
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
    - Supports test context-based repository injection via _repository_context

    Examples:
        Search for spells:
            spells = await search_spell(search="fireball")
            spells = await search_spell(search="healing restoration")

        Filtering by level:
            cantrips = await search_spell(level=0)
            high_level_spells = await search_spell(level=5)

        Using level ranges:
            mid_level_spells = await search_spell(level_min=3, level_max=5)
            powerful_spells = await search_spell(level_min=5)
            beginner_spells = await search_spell(level_max=2)

        Filtering by school and other properties:
            evocation_spells = await search_spell(school="evocation")
            wizard_spells = await search_spell(class_key="wizard")
            ritual_spells = await search_spell(ritual=True)
            concentration_spells = await search_spell(concentration=True)

        Filtering by damage type:
            fire_spells = await search_spell(damage_type="fire")
            cold_spells = await search_spell(damage_type="cold")
            necrotic_spells = await search_spell(damage_type="necrotic")

        Filtering by document:
            srd_only = await search_spell(documents=["srd-5e"])
            srd_and_tasha = await search_spell(documents=["srd-5e", "tce"])

        Complex queries combining multiple filters:
            evocation_fire_spells = await search_spell(
                school="evocation", damage_type="fire"
            )
            cleric_rituals = await search_spell(
                class_key="cleric", ritual=True, level_min=1
            )
            mid_level_wizard_spells = await search_spell(
                class_key="wizard", level_min=3, level_max=5, limit=10
            )

        Semantic search (natural language queries):
            fire_spells = await search_spell(search="fire damage explosion")
            healing_spells = await search_spell(search="restore health allies")
            protection = await search_spell(search="defensive barrier ward")

        Hybrid search (search + filters):
            fire_evocation = await search_spell(
                search="fire explosion", school="evocation"
            )
            low_level_healing = await search_spell(
                search="heal wounds", level_max=3
            )

        With test context injection (testing):
            from lorekeeper_mcp.tools.search_spell import _repository_context
            custom_repo = SpellRepository(cache=my_cache)
            _repository_context["repository"] = custom_repo
            spells = await search_spell(level=0)

    Args:
        level: Exact spell level ranging from 0-9. 0 represents cantrips/0-level spells,
            9 represents 9th level spells. Example: 3 for exactly 3rd level spells
        level_min: Minimum spell level (inclusive) for range-based searches. Use with
            level_max to find spells in a range. Returns spells at this level or higher.
            Examples: 1 for 1st level and above, 5 for 5th level and above
        level_max: Maximum spell level (inclusive) for range-based searches. Use with
            level_min to find spells in a range. Returns spells at this level or lower.
            Examples: 3 for up to 3rd level spells, 5 for up to 5th level spells
        school: Magic school filter for spell type. Valid values: abjuration, conjuration,
            divination, enchantment, evocation, illusion, necromancy, transmutation.
            Each school has distinct characteristics. Example: "evocation" for
            damage-dealing spells, "abjuration" for protective spells
        class_key: Filter spells available to a specific class. Valid values: wizard, cleric,
            druid, bard, paladin, ranger, sorcerer, warlock, artificer. Each class has
            access to different spell lists. Example: "wizard" for spells in wizard spell list
        concentration: Filter for spells requiring concentration. True returns only
            concentration spells, False returns only non-concentration spells. Concentration
            is a key resource in combat. Example: True
        ritual: Filter for ritual spells. Returns only spells that can be cast as rituals,
            allowing casting without expending spell slots. Example: True
        casting_time: Casting time filter to find spells with specific casting times.
            Examples: "1 action" (most common), "1 bonus action" (quick casts),
            "1 reaction" (reaction spells), "1 minute" (extended preparation)
        damage_type: Filter spells by damage type dealt. Examples: "fire" (fire damage),
            "cold" (cold damage), "necrotic" (necrotic damage), "poison" (poison damage),
            "psychic" (psychic damage). NEW in Phase 3.
        documents: Filter to specific source documents. Provide a list of
            document names/identifiers from list_documents() tool. Examples:
            ["srd-5e"] for SRD only, ["srd-5e", "tce"] for SRD and Tasha's.
            Use list_documents() to see available documents.
        search: Natural language search query for semantic/vector search.
            When provided, uses vector similarity to find spells matching the
            conceptual meaning rather than exact text matches. Can be combined
            with other filters for hybrid search. Examples: "fire damage explosion",
            "healing allies", "protection from evil creatures"
        limit: Maximum number of results to return. Default 20. Useful for pagination
            or limiting large result sets. Examples: 5 for small sets, 20 for standard,
            100 for comprehensive results

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
            - damage_type: Damage types dealt by the spell (if applicable)

    Raises:
        ApiError: If the API request fails due to network issues or server errors
    """
    repository = _get_repository()

    params: dict[str, Any] = {}
    if level is not None:
        params["level"] = level
    if level_min is not None:
        params["level_min"] = level_min
    if level_max is not None:
        params["level_max"] = level_max
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
    if damage_type is not None:
        params["damage_type"] = damage_type
    if documents is not None:
        params["document"] = documents
    if search is not None:
        params["search"] = search

    spells = await repository.search(limit=limit, **params)

    spells = spells[:limit]

    return [spell.model_dump() for spell in spells]
