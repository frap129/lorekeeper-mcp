"""Entity type mapper for OrcBrew to LoreKeeper entity types."""

import logging
from typing import Any

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

    # Build normalized entity
    normalized: dict[str, Any] = {
        "slug": slug,
        "name": name,
        "source": source,
        "source_api": "orcbrew",
        "data": {k: v for k, v in entity.items() if not k.startswith("_")},
    }

    # Copy indexed fields to top level for filtering
    lorekeeper_type = map_entity_type(orcbrew_type)
    if lorekeeper_type:
        normalized.update(_extract_indexed_fields(entity, lorekeeper_type))

    return normalized


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
        if "challenge" in entity:
            # OrcBrew uses 'challenge', LoreKeeper uses 'challenge_rating'
            indexed["challenge_rating"] = entity["challenge"]
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
