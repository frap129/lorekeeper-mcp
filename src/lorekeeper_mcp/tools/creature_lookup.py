"""Creature lookup tool."""

from typing import Any

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client


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
    Look up D&D 5e creatures/monsters using Open5e v1 API.

    Args:
        name: Creature name or partial name search
        cr: Exact challenge rating (supports 0.125, 0.25, 0.5, 1-30)
        cr_min: Minimum CR for range searches
        cr_max: Maximum CR for range searches
        type: Creature type (aberration, beast, dragon, undead, etc.)
        size: Size category (Tiny, Small, Medium, Large, Huge, Gargantuan)
        limit: Maximum number of results (default 20)

    Returns:
        List of creature stat block dictionaries

    Raises:
        APIError: If the API request fails
    """
    client = Open5eV1Client()

    # Build query parameters
    params: dict[str, Any] = {"limit": limit}
    if name is not None:
        params["name"] = name
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
    return [creature.model_dump() for creature in response]
