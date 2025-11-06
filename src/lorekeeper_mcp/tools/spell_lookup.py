"""Spell lookup tool."""

from typing import Any

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client


async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    school: str | None = None,
    class_key: str | None = None,
    concentration: bool | None = None,
    ritual: bool | None = None,
    casting_time: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Look up D&D 5e spells using Open5e v2 API.

    Args:
        name: Spell name or partial name search
        level: Spell level (0-9, where 0 is cantrips)
        school: Magic school (abjuration, conjuration, etc.)
        class_key: Filter by class (wizard, cleric, etc.)
        concentration: Filter for concentration spells
        ritual: Filter for ritual spells
        casting_time: Casting time filter (e.g., "1 action")
        limit: Maximum number of results (default 20)

    Returns:
        List of spell dictionaries with full spell data

    Raises:
        ApiError: If the API request fails
    """
    client = Open5eV2Client()

    # Build query parameters
    params: dict[str, Any] = {"limit": limit}
    if name is not None:
        params["name"] = name
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

    spells = await client.get_spells(**params)
    return [spell.model_dump() for spell in spells]
