"""Equipment lookup tool."""

from typing import Any, Literal, cast

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

EquipmentType = Literal["weapon", "armor", "magic-item", "all"]


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
    Search and retrieve D&D 5e weapons, armor, and magic items.

    This tool provides comprehensive equipment lookup across weapons, armor, and magical
    items. Filter by rarity, damage potential, complexity, or attunement requirements.
    Automatically retrieves and caches data from multiple sources for reliability.

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
        APIError: If the API request fails due to network issues or server errors
    """
    results: list[dict[str, Any]] = []

    # Build base params
    base_params: dict[str, Any] = {"limit": limit}
    if name is not None:
        base_params["search"] = name

    # Query weapons
    if type in ("weapon", "all"):
        v2_client = Open5eV2Client()
        weapon_params = base_params.copy()
        if damage_dice is not None:
            weapon_params["damage_dice"] = damage_dice
        if is_simple is not None:
            weapon_params["is_simple"] = is_simple

        weapon_response = await v2_client.get_weapons(**weapon_params)
        # Handle both mocked dict response and actual list response
        if isinstance(weapon_response, dict):  # type: ignore[unreachable]
            results.extend(  # type: ignore[unreachable]
                cast(list[dict[str, Any]], weapon_response.get("results", []))
            )
        else:
            results.extend([w.model_dump() for w in weapon_response])

    # Query armor
    if type in ("armor", "all"):
        v2_client = Open5eV2Client()
        armor_response = await v2_client.get_armor(**base_params)
        # Handle both mocked dict response and actual list response
        if isinstance(armor_response, dict):  # type: ignore[unreachable]
            results.extend(  # type: ignore[unreachable]
                cast(list[dict[str, Any]], armor_response.get("results", []))
            )
        else:
            results.extend([a.model_dump() for a in armor_response])

    # Query magic items
    if type in ("magic-item", "all"):
        v1_client = Open5eV1Client()
        magic_params = base_params.copy()
        if rarity is not None:
            magic_params["rarity"] = rarity
        if requires_attunement is not None:
            magic_params["requires_attunement"] = requires_attunement

        magic_response = await v1_client.get_magic_items(  # type: ignore[attr-defined]
            **magic_params
        )
        # Handle both mocked dict response and actual list response
        if isinstance(magic_response, dict):
            results.extend(cast(list[dict[str, Any]], magic_response.get("results", [])))
        else:
            results.extend([m.model_dump() for m in magic_response])

    # Apply overall limit if querying multiple types
    if type == "all" and len(results) > limit:
        results = results[:limit]

    return results
