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
    Look up weapons, armor, and magic items.

    Args:
        type: Equipment type (weapon, armor, magic-item, all)
        name: Item name or partial name search
        rarity: Magic item rarity (common, uncommon, rare, very rare, legendary, artifact)
        damage_dice: Weapon damage dice filter (e.g., "1d8", "2d6")
        is_simple: Filter for simple weapons only
        requires_attunement: Attunement requirement filter
        limit: Maximum number of results per type (default 20)

    Returns:
        List of equipment dictionaries (structure varies by type)

    Raises:
        APIError: If the API request fails
    """
    results: list[dict[str, Any]] = []

    # Build base params
    base_params: dict[str, Any] = {"limit": limit}
    if name is not None:
        base_params["name"] = name

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
