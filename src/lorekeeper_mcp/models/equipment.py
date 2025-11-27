"""Equipment models for weapons, armor, and magic items."""

from typing import Any

from pydantic import Field, model_validator

from lorekeeper_mcp.models.base import BaseEntity


class Weapon(BaseEntity):
    """Model representing a D&D 5e weapon.

    Simplified model that stores damage_type as string (not nested object).
    """

    damage_dice: str = Field(..., description="Damage dice (e.g., 1d8)")
    damage_type: str = Field(..., description="Damage type name (e.g., Piercing)")
    properties: list[str] = Field(
        default_factory=list,
        description="Weapon properties (Finesse, Light, etc.)",
    )
    range: float = Field(..., ge=0, description="Normal range in distance units")
    long_range: float = Field(..., ge=0, description="Long range in distance units")
    distance_unit: str = Field(..., description="Unit of distance measurement")
    is_simple: bool = Field(..., description="Whether weapon is Simple (vs Martial)")
    is_improvised: bool = Field(..., description="Whether weapon is improvised")

    # Optional fields
    category: str | None = Field(None, description="Weapon category (derived)")
    cost: str | None = Field(None, description="Cost in gold pieces")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")
    range_normal: int | None = Field(None, description="Normal range (legacy name)")
    range_long: int | None = Field(None, description="Long range (legacy name)")
    versatile_dice: str | None = Field(None, description="Versatile damage dice")

    @model_validator(mode="before")
    @classmethod
    def normalize_weapon_fields(cls, data: Any) -> Any:
        """Normalize weapon-specific fields from API format."""
        if not isinstance(data, dict):
            return data

        # Extract damage_type name from nested object
        if isinstance(data.get("damage_type"), dict):
            data["damage_type"] = data["damage_type"].get("name", str(data["damage_type"]))

        # Extract property names from complex structure
        if "properties" in data and isinstance(data["properties"], list):
            normalized_props: list[str] = []
            for prop in data["properties"]:
                if isinstance(prop, str):
                    normalized_props.append(prop)
                elif isinstance(prop, dict):
                    # Handle nested property object
                    if "property" in prop and isinstance(prop["property"], dict):
                        normalized_props.append(prop["property"].get("name", str(prop)))
                    elif "name" in prop:
                        normalized_props.append(prop["name"])
            data["properties"] = normalized_props

        return data


class Armor(BaseEntity):
    """Model representing D&D 5e armor."""

    category: str = Field(..., description="Armor category (Light, Medium, Heavy, Shield)")
    base_ac: int | None = Field(None, ge=0, description="Base armor class")
    cost: str | None = Field(None, description="Cost in gold pieces")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")

    dex_bonus: bool | None = Field(None, description="Can add Dex bonus to AC")
    max_dex_bonus: int | None = Field(None, description="Maximum Dex bonus")
    strength_required: int | None = Field(None, description="Minimum Strength required")
    stealth_disadvantage: bool = Field(False, description="Imposes disadvantage on Stealth")


class MagicItem(BaseEntity):
    """Model representing a D&D 5e magic item."""

    rarity: str | None = Field(None, description="Rarity level (common to artifact)")
    requires_attunement: bool | None = Field(None, description="Whether item requires attunement")
    type: str | None = Field(None, description="Type of item (wondrous, wand, ring, etc.)")
    wondrous: bool | None = Field(None, description="Whether item is wondrous")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")
    armor_class: int | None = Field(None, ge=0, description="AC bonus if armor")
    damage: str | None = Field(None, description="Damage if weapon")
