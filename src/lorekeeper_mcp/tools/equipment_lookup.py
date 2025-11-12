"""Equipment lookup tool using the repository pattern for caching.

This module provides comprehensive equipment lookup for weapons, armor, and magic
items with automatic database caching through the repository pattern. The repository
abstracts away cache management and allows filtering across multiple equipment types.

Architecture:
    - Uses EquipmentRepository for cache-aside pattern with item-type routing
    - Repository manages SQLite cache automatically
    - Supports test context-based repository injection
    - Handles weapon, armor, and magic item filtering

Examples:
    Default usage (automatically creates repository):
        weapons = await lookup_equipment(type="weapon", damage_dice="1d8")
        items = await lookup_equipment(type="magic-item", rarity="rare")

    With context-based injection (testing):
        from lorekeeper_mcp.tools.equipment_lookup import _repository_context
        from lorekeeper_mcp.repositories.equipment import EquipmentRepository

        repository = EquipmentRepository(cache=my_cache)
        _repository_context["repository"] = repository
        armor = await lookup_equipment(type="armor")

    Item type filtering:
        all_items = await lookup_equipment(type="all", name="chain")
        simple_weapons = await lookup_equipment(type="weapon", is_simple=True)"""

from typing import Any, Literal, cast

from lorekeeper_mcp.repositories.equipment import EquipmentRepository
from lorekeeper_mcp.repositories.factory import RepositoryFactory

# Module-level context for test repository injection
_repository_context: dict[str, Any] = {}

EquipmentType = Literal["weapon", "armor", "magic-item", "all"]


def _get_repository() -> EquipmentRepository:
    """Get equipment repository, respecting test context.

    Returns the repository from _repository_context if set, otherwise creates
    a default EquipmentRepository using RepositoryFactory.

    Returns:
        EquipmentRepository instance for equipment lookups.
    """
    if "repository" in _repository_context:
        return cast(EquipmentRepository, _repository_context["repository"])
    return RepositoryFactory.create_equipment_repository()


async def lookup_equipment(
    type: EquipmentType = "all",  # noqa: A002
    name: str | None = None,
    rarity: str | None = None,
    damage_dice: str | None = None,
    is_simple: bool | None = None,
    requires_attunement: str | None = None,
    cost_min: int | float | None = None,
    cost_max: int | float | None = None,
    weight_max: float | None = None,
    is_finesse: bool | None = None,
    is_light: bool | None = None,
    is_magic: bool | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search and retrieve D&D 5e weapons, armor, and magic items using the repository pattern.

    This tool provides comprehensive equipment lookup across weapons, armor, and magical
    items. Filter by rarity, damage potential, complexity, or attunement requirements.
    Automatically uses the database cache through the repository for improved performance.

    Examples:
        Basic equipment lookup:
            longswords = await lookup_equipment(type="weapon", name="longsword")
            rare_items = await lookup_equipment(type="magic-item", rarity="rare")
            light_armor = await lookup_equipment(type="armor", is_simple=True)

        Using cost ranges (NEW in Phase 3):
            affordable_weapons = await lookup_equipment(
                type="weapon", cost_max=25
            )
            expensive_items = await lookup_equipment(
                type="weapon", cost_min=50, cost_max=100
            )

        Using weight and properties (NEW in Phase 3):
            lightweight_weapons = await lookup_equipment(
                type="weapon", weight_max=3
            )
            finesse_weapons = await lookup_equipment(
                type="weapon", is_finesse=True
            )
            light_dual_wield_weapons = await lookup_equipment(
                type="weapon", is_light=True
            )
            magical_weapons = await lookup_equipment(
                type="weapon", is_magic=True
            )

        Complex equipment queries:
            affordable_simple_weapons = await lookup_equipment(
                type="weapon", is_simple=True, cost_max=10
            )
            light_finesse_weapons = await lookup_equipment(
                type="weapon", is_light=True, is_finesse=True, limit=10
            )
            expensive_magical_weapons = await lookup_equipment(
                type="weapon", is_magic=True, cost_min=100
            )

        Searching all types:
            all_chain_items = await lookup_equipment(
                type="all", name="chain"
            )

    Args:
        type: Equipment type to search. Default "all" searches all types. Options:
            - "weapon": Melee weapons (longsword, dagger, etc.) and ranged weapons (bow, crossbow)
            - "armor": Protective gear (leather armor, chain mail, plate, etc.)
            - "magic-item": Magical items (Bag of Holding, Wand of Fireballs, etc.)
            - "all": Search all equipment types simultaneously (may return many results)
        name: Item name or partial name search. Matches items containing this substring.
            Case-insensitive. Examples: "longsword", "chain", "bag", "wand"
        rarity: Magic item rarity filter (weapon/armor types don't use this).
            Valid values: common, uncommon, rare, very rare, legendary, artifact
            Example: "rare" for high-value magical items
        damage_dice: Weapon damage dice filter to find weapons dealing specific damage.
            Examples: "1d4" (dagger), "1d8" (longsword), "2d6" (greataxe), "1d12" (greatsword)
        is_simple: Filter for simple weapons (True) or martial weapons (False).
            Simple weapons: club, dagger, greatclub, handaxe, javelin, light hammer, mace,
            quarterstaff, sickle, spear
            Martial weapons: all other melee and ranged weapons
            Example: True for low-complexity options
        requires_attunement: Magic item attunement filter. Some powerful items require
            attunement to a character. Examples: "yes", "no", or specific requirements
        cost_min: Minimum cost in gold pieces (weapons and armor). Filters items costing
            at least this amount. Example: 10 for items costing 10+ gp
        cost_max: Maximum cost in gold pieces (weapons and armor). Filters items costing
            at most this amount. Example: 25 for items costing 25 gp or less
        weight_max: Maximum weight in pounds (weapons). Filters weapons weighing at most
            this amount. Example: 3 for lightweight weapons
        is_finesse: Finesse property filter (weapons). When True, returns only weapons
            with the finesse property (can use STR or DEX modifier). Example: True
        is_light: Light property filter (weapons). When True, returns only light weapons
            suitable for dual-wielding. Example: True
        is_magic: Magic property filter (weapons). When True, returns only magical weapons.
            Example: True
        limit: Maximum number of results to return. Default 20. For type="all" with many
            matches, limit applies to total results. Examples: 5, 20, 100

    Returns:
        List of equipment dictionaries. Structure varies by type:

        For type="weapon":
            - name: Weapon name
            - damage_dice: Damage expression (e.g., "1d8")
            - damage_type: Type of damage (slashing, piercing, bludgeoning)
            - weight: Weight in pounds
            - is_simple: Whether this is a simple weapon
            - range: Range for ranged weapons (e.g., "20/60 feet")
            - properties: Weapon properties (finesse, heavy, reach, two-handed, etc.)
            - rarity: Equipment rarity

        For type="armor":
            - name: Armor name
            - armor_class: AC provided by this armor
            - armor_class_dex: Whether DEX bonus applies (light/medium)
            - armor_class_strength: Whether STR requirement applies (heavy)
            - weight: Weight in pounds
            - armor_category: Light/Medium/Heavy classification
            - rarity: Equipment rarity

        For type="magic-item":
            - name: Item name
            - description: What the item does and its powers
            - rarity: Rarity level (common through artifact)
            - requires_attunement: Attunement requirements
            - wondrous: Whether item is wondrous (non-weapon/armor)
            - weight: Weight if applicable
            - armor_class: AC bonus if armor
            - damage: Damage if weapon

    Raises:
        ApiError: If the API request fails due to network issues or server errors
    """
    # Get repository from context or create default
    repository = _get_repository()

    results: list[dict[str, Any]] = []

    # Query weapons
    if type in ("weapon", "all"):
        # Build weapon filters
        weapon_filters: dict[str, Any] = {"item_type": "weapon"}
        if name is not None:
            weapon_filters["name"] = name
        if damage_dice is not None:
            weapon_filters["damage_dice"] = damage_dice
        if is_simple is not None:
            weapon_filters["is_simple"] = is_simple
        if cost_min is not None:
            weapon_filters["cost_min"] = cost_min
        if cost_max is not None:
            weapon_filters["cost_max"] = cost_max
        if weight_max is not None:
            weapon_filters["weight_max"] = weight_max
        if is_finesse is not None:
            weapon_filters["is_finesse"] = is_finesse
        if is_light is not None:
            weapon_filters["is_light"] = is_light
        if is_magic is not None:
            weapon_filters["is_magic"] = is_magic

        # Fetch weapons with server-side filters
        weapons = await repository.search(limit=limit, **weapon_filters)

        # Convert to dicts
        weapon_dicts = [w.model_dump() for w in weapons]
        results.extend(weapon_dicts)

    # Query armor
    if type in ("armor", "all"):
        # Build armor filters
        armor_filters: dict[str, Any] = {"item_type": "armor"}
        if name is not None:
            armor_filters["name"] = name
        if cost_min is not None:
            armor_filters["cost_min"] = cost_min
        if cost_max is not None:
            armor_filters["cost_max"] = cost_max

        # Fetch armor with server-side filters
        armors = await repository.search(limit=limit, **armor_filters)

        # Convert to dicts
        armor_dicts = [a.model_dump() for a in armors]
        results.extend(armor_dicts)

    # Query magic items
    if type in ("magic-item", "all"):
        # Build magic item filters
        magic_item_filters: dict[str, Any] = {"item_type": "magic-item"}
        if name is not None:
            magic_item_filters["name"] = name
        if rarity is not None:
            magic_item_filters["rarity"] = rarity
        if requires_attunement is not None:
            # Convert string "yes"/"no" to boolean for API
            if requires_attunement.lower() in ("yes", "true", "1"):
                magic_item_filters["requires_attunement"] = True
            else:
                magic_item_filters["requires_attunement"] = False

        # Fetch magic items with server-side filters
        magic_items = await repository.search(limit=limit, **magic_item_filters)

        # Convert to dicts
        magic_item_dicts = [m.model_dump() for m in magic_items]
        results.extend(magic_item_dicts)

    # Apply overall limit if querying multiple types
    if type == "all" and len(results) > limit:
        results = results[:limit]

    return results
