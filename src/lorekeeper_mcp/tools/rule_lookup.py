"""Rule lookup tool."""

from typing import Any, Literal, assert_never

from lorekeeper_mcp.api_clients.dnd5e_api import Dnd5eApiClient
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

RuleType = Literal[
    "rule",
    "condition",
    "damage-type",
    "weapon-property",
    "skill",
    "ability-score",
    "magic-school",
    "language",
    "proficiency",
    "alignment",
]


async def lookup_rule(
    rule_type: RuleType,
    name: str | None = None,
    section: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Look up game rules, conditions, and reference information.

    Args:
        rule_type: Rule type (rule, condition, damage-type, etc.) - REQUIRED
        name: Name or partial name search
        section: For rules - section name (combat, spellcasting, etc.)
        limit: Maximum number of results (default 20)

    Returns:
        List of rule/reference dictionaries

    Raises:
        ValueError: If rule_type is not valid
        APIError: If the API request fails
    """
    valid_types = {
        "rule",
        "condition",
        "damage-type",
        "weapon-property",
        "skill",
        "ability-score",
        "magic-school",
        "language",
        "proficiency",
        "alignment",
    }
    if rule_type not in valid_types:
        raise ValueError(
            f"Invalid type '{rule_type}'. Must be one of: {', '.join(sorted(valid_types))}"
        )

    params: dict[str, Any] = {}
    if name is not None:
        params["name"] = name
    if limit is not None:
        params["limit"] = limit

    # Route to appropriate client and endpoint
    if rule_type == "condition":
        client = Open5eV2Client()
        return await client.get_conditions(**params)

    # All other types use D&D 5e API
    dnd5e_client = Dnd5eApiClient()

    # Add section parameter for rules
    if rule_type == "rule" and section is not None:
        params["section"] = section

    # Call appropriate method
    if rule_type == "rule":
        return await dnd5e_client.get_rules(**params)
    if rule_type == "damage-type":
        return await dnd5e_client.get_damage_types(**params)
    if rule_type == "weapon-property":
        return await dnd5e_client.get_weapon_properties(**params)
    if rule_type == "skill":
        return await dnd5e_client.get_skills(**params)
    if rule_type == "ability-score":
        return await dnd5e_client.get_ability_scores(**params)
    if rule_type == "magic-school":
        return await dnd5e_client.get_magic_schools(**params)
    if rule_type == "language":
        return await dnd5e_client.get_languages(**params)
    if rule_type == "proficiency":
        return await dnd5e_client.get_proficiencies(**params)
    if rule_type == "alignment":
        return await dnd5e_client.get_alignments(**params)

    assert_never(rule_type)
