"""Equipment models for weapons and armor."""

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from lorekeeper_mcp.api_clients.models.base import BaseModel


class DamageType(PydanticBaseModel):
    """Damage type with metadata."""

    name: str = Field(..., description="Damage type name (e.g., Piercing)")
    key: str = Field(..., description="Damage type key (e.g., piercing)")
    url: str = Field(..., description="API endpoint URL for damage type")


class PropertyDetail(PydanticBaseModel):
    """Weapon property metadata."""

    name: str = Field(..., description="Property name (e.g., Finesse)")
    type: str | None = Field(None, description="Property type (e.g., Mastery)")
    url: str = Field(..., description="API endpoint URL for property")


class WeaponProperty(PydanticBaseModel):
    """Weapon property with optional detail."""

    property: PropertyDetail = Field(..., description="Property metadata")
    detail: str | None = Field(None, description="Property detail (e.g., versatile dice)")


class Weapon(BaseModel):
    """Model representing a D&D 5e weapon."""

    # slug maps to "key" from the API
    slug: str = Field(..., alias="key", description="Unique identifier for the weapon")
    damage_dice: str = Field(..., description="Damage dice (e.g., 1d8)")
    damage_type: DamageType = Field(..., description="Damage type object")
    properties: list[WeaponProperty] = Field(
        default_factory=list,
        description="Weapon properties (complex objects)",
    )
    range: float = Field(..., ge=0, description="Normal range in distance units")
    long_range: float = Field(..., ge=0, description="Long range in distance units")
    distance_unit: str = Field(..., description="Unit of distance measurement")
    is_simple: bool = Field(..., description="Whether weapon is Simple (vs Martial)")
    is_improvised: bool = Field(..., description="Whether weapon is improvised")

    # Legacy/optional fields (not in API v2 but kept for compatibility)
    category: str | None = Field(None, description="Weapon category (derived)")
    cost: str | None = Field(None, description="Cost in gold pieces")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")
    range_normal: int | None = Field(None, description="Normal range (legacy name)")
    range_long: int | None = Field(None, description="Long range (legacy name)")
    versatile_dice: str | None = Field(None, description="Versatile damage dice")


class Armor(BaseModel):
    """Model representing D&D 5e armor."""

    # slug maps to "key" from the API
    slug: str = Field(..., alias="key", description="Unique identifier for the armor")
    category: str = Field(..., description="Armor category (Light, Medium, Heavy, Shield)")
    base_ac: int | None = Field(None, ge=0, description="Base armor class")
    cost: str | None = Field(None, description="Cost in gold pieces")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")

    dex_bonus: bool | None = Field(None, description="Can add Dex bonus to AC")
    max_dex_bonus: int | None = Field(None, description="Maximum Dex bonus")
    strength_required: int | None = Field(None, description="Minimum Strength required")
    stealth_disadvantage: bool = Field(False, description="Imposes disadvantage on Stealth")


class MagicItem(BaseModel):
    """Model representing a D&D 5e magic item."""

    # slug maps to "key" or "slug" from the API
    slug: str = Field(..., alias="key", description="Unique identifier for the magic item")
    desc: str = Field(..., description="Description of the magic item")
    rarity: str | None = Field(None, description="Rarity level (common to artifact)")
    requires_attunement: bool | None = Field(None, description="Whether item requires attunement")
    document_url: str | None = Field(None, description="URL to official documentation")
    type: str | None = Field(None, description="Type of item (wondrous, wand, ring, etc.)")
    wondrous: bool | None = Field(None, description="Whether item is wondrous")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")
    armor_class: int | None = Field(None, ge=0, description="AC bonus if armor")
    damage: str | None = Field(None, description="Damage if weapon")
