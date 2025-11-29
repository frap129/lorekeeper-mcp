"""Creature search tool with hybrid semantic and structured filtering.

This module provides creature lookup functionality using both semantic/vector search
and structured filtering through the repository pattern.

Architecture:
    - Uses CreatureRepository for cache-aside pattern with multi-source support
    - Repository manages cache automatically
    - Supports test context-based repository injection
    - Handles Open5e v1 and D&D 5e API data normalization
    - Returns canonical Creature models from lorekeeper_mcp.models

Examples:
    Default usage (automatically creates repository):
        creatures = await search_creature(cr=5)
        dragons = await search_creature(type="dragon")

    With context-based injection (testing):
        from lorekeeper_mcp.tools.search_creature import _repository_context
        from lorekeeper_mcp.repositories.creature import CreatureRepository

        repository = CreatureRepository(cache=my_cache)
        _repository_context["repository"] = repository
        creatures = await search_creature(cr_min=1, cr_max=3)

    Challenge rating queries:
        low_level = await search_creature(cr_max=2)
        bosses = await search_creature(cr_min=10)"""

from typing import Any, cast

from lorekeeper_mcp.repositories.creature import CreatureRepository
from lorekeeper_mcp.repositories.factory import RepositoryFactory

_repository_context: dict[str, Any] = {}


def _get_repository() -> CreatureRepository:
    """Get creature repository, respecting test context.

    Returns the repository from _repository_context if set, otherwise creates
    a default creature repository using RepositoryFactory.

    Returns:
        CreatureRepository instance for creature lookups.
    """
    if "repository" in _repository_context:
        return cast(CreatureRepository, _repository_context["repository"])
    return RepositoryFactory.create_creature_repository()


async def search_creature(
    name: str | None = None,
    cr: float | None = None,
    cr_min: float | None = None,
    cr_max: float | None = None,
    type: str | None = None,  # noqa: A002
    size: str | None = None,
    armor_class_min: int | None = None,
    hit_points_min: int | None = None,
    documents: list[str] | None = None,
    semantic_query: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search and retrieve D&D 5e creatures using the repository pattern.

    This tool provides comprehensive creature lookup including full stat blocks, combat
    statistics, abilities, and special features. Results include complete creature data
    and are cached through the repository for improved performance.

    Examples:
        Basic creature lookup:
            creatures = await search_creature(name="dragon")
            creatures = await search_creature(cr=5)
            medium_creatures = await search_creature(size="Medium")

        Using challenge rating ranges:
            low_cr_creatures = await search_creature(cr_max=2)
            mid_level_threats = await search_creature(cr_min=3, cr_max=5)
            deadly_bosses = await search_creature(cr_min=10)

        Filtering by type and size:
            undead_creatures = await search_creature(type="undead")
            humanoids = await search_creature(type="humanoid", cr_max=2)
            large_creatures = await search_creature(size="Large", limit=10)

        Using armor class and hit points filters:
            well_armored_creatures = await search_creature(armor_class_min=15)
            heavily_armored = await search_creature(armor_class_min=18)
            tanky_creatures = await search_creature(hit_points_min=100)
            deadly_tanky = await search_creature(
                armor_class_min=16, hit_points_min=75, cr_min=5
            )

        With document filtering:
            srd_only = await search_creature(documents=["srd-5e"])
            tasha_creatures = await search_creature(
                documents=["srd-5e", "tce"]
            )
            phb_and_dmg = await search_creature(
                documents=["phb", "dmg"], cr_min=5
            )

        Semantic search (natural language queries):
            fire_creatures = await search_creature(
                semantic_query="fire breathing flying beast"
            )
            undead_minions = await search_creature(
                semantic_query="shambling corpse horde"
            )
            intelligent_foes = await search_creature(
                semantic_query="cunning spellcaster manipulator"
            )

        Hybrid search (semantic + filters):
            fire_dragons = await search_creature(
                semantic_query="fire breathing", type="dragon", cr_min=10
            )
            weak_undead = await search_creature(
                semantic_query="shambling minion", type="undead", cr_max=2
            )

        With test context injection (testing):
            from lorekeeper_mcp.tools.search_creature import _repository_context
            custom_repo = CreatureRepository(cache=my_cache)
            _repository_context["repository"] = custom_repo
            creatures = await search_creature(size="Tiny")

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
          documents: Filter to specific source documents. Provide a list of
              document names/identifiers from list_documents() tool. Examples:
              ["srd-5e"] for SRD only, ["srd-5e", "tce"] for SRD and Tasha's.
              Use list_documents() to see available documents.
          semantic_query: Natural language search query for semantic/vector search.
              When provided, uses vector similarity to find creatures matching the
              conceptual meaning rather than exact text matches. Can be combined
              with other filters for hybrid search. Examples: "fire breathing dragon",
              "undead horde minion", "intelligent spellcaster"
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
    repository = _get_repository()

    params: dict[str, Any] = {}
    if name is not None:
        params["name"] = name
    if cr is not None:
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
    if documents is not None:
        params["document"] = documents
    if semantic_query is not None:
        params["semantic_query"] = semantic_query

    creatures = await repository.search(limit=limit, **params)

    creatures = creatures[:limit]

    return [creature.model_dump() for creature in creatures]
