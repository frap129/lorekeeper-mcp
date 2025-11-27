"""Entity type mapper for OrcBrew to LoreKeeper entity types."""

import logging
from typing import Any

from pydantic import ValidationError

from lorekeeper_mcp.models.orcbrew import OrcBrewCreature, OrcBrewSpell

logger = logging.getLogger(__name__)

# Mapping of OrcBrew entity type keys to LoreKeeper entity types
ORCBREW_TO_LOREKEEPER: dict[str, str | None] = {
    "orcpub.dnd.e5/spells": "spells",
    "orcpub.dnd.e5/monsters": "creatures",  # Note: using 'creatures' not 'monsters'
    "orcpub.dnd.e5/classes": "classes",
    "orcpub.dnd.e5/subclasses": "subclasses",
    "orcpub.dnd.e5/races": "species",  # Map to 'species' for consistency
    "orcpub.dnd.e5/subraces": "subraces",
    "orcpub.dnd.e5/backgrounds": "backgrounds",
    "orcpub.dnd.e5/feats": "feats",
    "orcpub.dnd.e5/languages": "languages",
    "orcpub.dnd.e5/weapons": "weapons",
    "orcpub.dnd.e5/armor": "armor",
    "orcpub.dnd.e5/magic-items": "magicitems",
    # Unsupported types (return None to skip)
    "orcpub.dnd.e5/invocations": None,
    "orcpub.dnd.e5/selections": None,
}


def map_entity_type(orcbrew_type: str) -> str | None:
    """Map OrcBrew entity type to LoreKeeper entity type.

    Args:
        orcbrew_type: OrcBrew entity type key (e.g., "orcpub.dnd.e5/spells")

    Returns:
        LoreKeeper entity type (e.g., "spells") or None if unsupported
    """
    return ORCBREW_TO_LOREKEEPER.get(orcbrew_type)


def normalize_entity(
    entity: dict[str, Any],
    orcbrew_type: str,
) -> dict[str, Any]:
    """Normalize OrcBrew entity to LoreKeeper format.

    Args:
        entity: OrcBrew entity dictionary
        orcbrew_type: OrcBrew entity type key

    Returns:
        Normalized entity dictionary with LoreKeeper schema

    Raises:
        ValueError: If entity is missing required fields

    Note:
        Validates entities through OrcBrew Pydantic models after normalization.
        Validation errors are logged as warnings since OrcBrew data is often
        incomplete but still usable.
    """
    # Extract or generate slug
    slug = entity.get("key")
    if not slug:
        # Try to generate from name
        name = entity.get("name", "")
        if not name:
            raise ValueError("Entity missing both 'key' and 'name' fields")
        slug = name.lower().replace(" ", "-").replace("'", "")

    # Extract name
    name = entity.get("name", slug.replace("-", " ").title())

    # Extract source book
    source = entity.get("_source_book", "Unknown")
    if "option-pack" in entity:
        source = entity["option-pack"]

    # Extract document name (book name is the document)
    document = entity.get("option-pack") or entity.get("_source_book", "Unknown")

    # Build base normalized entity with ALL fields from OrcBrew (not just indexed)
    normalized: dict[str, Any] = {
        "slug": slug,
        "name": name,
        "source": source,
        "source_api": "orcbrew",
        "document": document,
        "data": {k: v for k, v in entity.items() if not k.startswith("_")},
    }

    # Extract ALL OrcBrew fields to top level (comprehensive extraction)
    # This ensures fields like concentration, ritual, components are available
    for key, value in entity.items():
        if not key.startswith("_") and key not in normalized:
            # Convert kebab-case to snake_case
            snake_key = key.replace("-", "_")
            normalized[snake_key] = value

    # Copy indexed fields to top level for filtering (may override some above)
    lorekeeper_type = map_entity_type(orcbrew_type)
    if lorekeeper_type:
        normalized.update(_extract_indexed_fields(entity, lorekeeper_type))

    # Validate through OrcBrew Pydantic models
    _validate_through_model(normalized, lorekeeper_type)

    return normalized


def _validate_through_model(normalized: dict[str, Any], entity_type: str | None) -> None:
    """Validate normalized entity through appropriate OrcBrew Pydantic model.

    Args:
        normalized: Normalized entity data
        entity_type: LoreKeeper entity type

    Note:
        Validation errors are logged as warnings rather than raised,
        since OrcBrew data is often incomplete but still usable.
    """
    try:
        if entity_type == "spells":
            OrcBrewSpell.model_validate(normalized)
        elif entity_type == "creatures":
            OrcBrewCreature.model_validate(normalized)
        # Other types don't have OrcBrew models yet - pass through
    except ValidationError as e:
        logger.warning(
            "OrcBrew entity '%s' failed validation: %s",
            normalized.get("name", normalized.get("slug", "unknown")),
            e,
        )


def _extract_indexed_fields(
    entity: dict[str, Any],
    entity_type: str,
) -> dict[str, Any]:
    """Extract indexed fields for an entity type.

    Args:
        entity: OrcBrew entity data
        entity_type: LoreKeeper entity type

    Returns:
        Dictionary of indexed field values
    """
    indexed: dict[str, Any] = {}

    if entity_type == "spells":
        if "level" in entity:
            indexed["level"] = entity["level"]
        if "school" in entity:
            indexed["school"] = entity["school"]
        if "concentration" in entity:
            indexed["concentration"] = entity["concentration"]
        if "ritual" in entity:
            indexed["ritual"] = entity["ritual"]

    elif entity_type == "creatures":
        # Note: 'challenge' is NOT copied here - let OrcBrewCreature model handle
        # the conversion from challenge -> challenge_rating
        if "type" in entity:
            indexed["type"] = entity["type"]
        if "size" in entity:
            indexed["size"] = entity["size"]

    elif entity_type == "weapons":
        if "category" in entity:
            indexed["category"] = entity["category"]
        if "damage-type" in entity:
            indexed["damage_type"] = entity["damage-type"]

    elif entity_type == "armor":
        if "category" in entity:
            indexed["category"] = entity["category"]
        if "armor-class" in entity:
            indexed["armor_class"] = entity["armor-class"]

    elif entity_type == "magicitems":
        if "type" in entity:
            indexed["type"] = entity["type"]
        if "rarity" in entity:
            indexed["rarity"] = entity["rarity"]
        if "requires-attunement" in entity:
            indexed["requires_attunement"] = entity["requires-attunement"]

    return indexed
