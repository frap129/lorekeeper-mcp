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
    Search and retrieve D&D 5e spells from the Open5e v2 API.

    This tool provides comprehensive spell lookup functionality with support for filtering
    by multiple criteria. Results include complete spell descriptions, components, damage,
    effects, and availability information. Automatically caches responses for improved performance.

    Examples:
        - lookup_spell(name="fireball") - Find spells by name
        - lookup_spell(level=3, school="evocation") - Find all 3rd level evocation spells
        - lookup_spell(class_key="wizard", concentration=True, limit=10) - Find concentration spells for wizards
        - lookup_spell(level=0) - Find all cantrips
        - lookup_spell(ritual=True) - Find all ritual spells

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
    client = Open5eV2Client()

    # Build query parameters
    params: dict[str, Any] = {"limit": limit}
    if name is not None:
        params["search"] = name
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
