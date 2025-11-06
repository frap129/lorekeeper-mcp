"""Character option lookup tool."""

from typing import Any, Literal

from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

OptionType = Literal["class", "race", "background", "feat"]


async def lookup_character_option(
    type: OptionType,  # noqa: A002
    name: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Look up character creation and advancement options.

    Args:
        type: Option type (class, race, background, feat) - REQUIRED
        name: Name or partial name search
        limit: Maximum number of results (default 20)

    Returns:
        List of option dictionaries (structure varies by type)

    Raises:
        ValueError: If type is not valid
        APIError: If the API request fails
    """
    valid_types = {"class", "race", "background", "feat"}
    if type not in valid_types:
        raise ValueError(f"Invalid type '{type}'. Must be one of: {', '.join(valid_types)}")

    params: dict[str, Any] = {"limit": limit}
    if name is not None:
        params["name"] = name

    # Route to appropriate client and endpoint
    if type == "class":
        v1_client = Open5eV1Client()
        response = await v1_client.get_classes(**params)
    elif type == "race":
        v1_client = Open5eV1Client()
        response = await v1_client.get_races(**params)
    elif type == "background":
        v2_client = Open5eV2Client()
        response = await v2_client.get_backgrounds(**params)
    else:  # type == "feat"
        v2_client = Open5eV2Client()
        response = await v2_client.get_feats(**params)

    return response
