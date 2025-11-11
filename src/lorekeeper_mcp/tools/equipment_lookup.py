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
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search and retrieve D&D 5e weapons, armor, and magic items using the repository pattern.

    This tool provides comprehensive equipment lookup across weapons, armor, and magical
    items. Filter by rarity, damage potential, complexity, or attunement requirements.
    Automatically uses the database cache through the repository for improved performance.

    Examples:
        - lookup_equipment(type="weapon", name="longsword") - Find longsword variants
        - lookup_equipment(type="armor", is_simple=True) - Find light/medium armor
        - lookup_equipment(type="magic-item", rarity="rare") - Find rare magical items
        - lookup_equipment(type="all", name="chain") - Find chain weapons, armor, and items
        - lookup_equipment(type="weapon", damage_dice="1d8", is_simple=True) - Find simple 1d8 weapons

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
        if damage_dice is not None:
            weapon_filters["damage_dice"] = damage_dice
        if is_simple is not None:
            weapon_filters["is_simple"] = is_simple

        # Fetch weapons with filters
        # When searching by name, fetch more results to ensure we find matches
        # Use multiplier of 11 to balance finding matches with performance
        fetch_limit = limit * 11 if name else limit
        weapons = await repository.search(limit=fetch_limit, **weapon_filters)

        # Client-side filtering by name
        if name:
            name_lower = name.lower()
            weapons = [w for w in weapons if name_lower in w.name.lower()]

        # Limit results to requested count
        weapons = weapons[:limit]
        # Convert to dicts
        weapon_dicts = [w.model_dump() for w in weapons]
        results.extend(weapon_dicts)

    # Query armor
    if type in ("armor", "all"):
        # Build armor filters
        armor_filters: dict[str, Any] = {"item_type": "armor"}

        # Fetch armor with filters
        # When searching by name, fetch more results to ensure we find matches
        fetch_limit = limit * 11 if name else limit
        armors = await repository.search(limit=fetch_limit, **armor_filters)

        # Client-side filtering by name
        if name:
            name_lower = name.lower()
            armors = [a for a in armors if name_lower in a.name.lower()]

        # Limit results to requested count
        armors = armors[:limit]
        # Convert to dicts
        armor_dicts = [a.model_dump() for a in armors]
        results.extend(armor_dicts)

    # Query magic items
    if type in ("magic-item", "all"):
        # Build magic item filters
        magic_item_filters: dict[str, Any] = {"item_type": "magic-item"}
        if rarity is not None:
            magic_item_filters["rarity"] = rarity
        if requires_attunement is not None:
            # Convert string "yes"/"no" to boolean for API
            if requires_attunement.lower() in ("yes", "true", "1"):
                magic_item_filters["requires_attunement"] = True
            else:
                magic_item_filters["requires_attunement"] = False

        # Fetch magic items with filters
        # When searching by name, fetch more results to ensure we find matches
        fetch_limit = limit * 11 if name else limit
        magic_items = await repository.search(limit=fetch_limit, **magic_item_filters)

        # Client-side filtering by name
        if name:
            name_lower = name.lower()
            magic_items = [m for m in magic_items if name_lower in m.name.lower()]

        # Limit results to requested count
        magic_items = magic_items[:limit]
        # Convert to dicts
        magic_item_dicts = [m.model_dump() for m in magic_items]
        results.extend(magic_item_dicts)

    # Apply overall limit if querying multiple types
    if type == "all" and len(results) > limit:
        results = results[:limit]

    return results
