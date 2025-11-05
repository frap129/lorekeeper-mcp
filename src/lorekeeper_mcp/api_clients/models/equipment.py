"""Equipment models for weapons and armor."""

from pydantic import Field

from lorekeeper_mcp.api_clients.models.base import BaseModel


class Weapon(BaseModel):
    """Model representing a D&D 5e weapon."""

    category: str = Field(..., description="Weapon category (Simple/Martial, Melee/Ranged)")
    damage_dice: str = Field(..., description="Damage dice (e.g., 1d8)")
    damage_type: str = Field(..., description="Damage type (slashing, piercing, bludgeoning)")
    cost: str = Field(..., description="Cost in gold pieces")
    weight: float = Field(..., ge=0, description="Weight in pounds")

    properties: list[str] | None = Field(None, description="Weapon properties")
    range_normal: int | None = Field(None, description="Normal range in feet")
    range_long: int | None = Field(None, description="Long range in feet")
    versatile_dice: str | None = Field(None, description="Versatile damage dice")


class Armor(BaseModel):
    """Model representing D&D 5e armor."""

    category: str = Field(..., description="Armor category (Light, Medium, Heavy, Shield)")
    base_ac: int = Field(..., ge=0, description="Base armor class")
    cost: str = Field(..., description="Cost in gold pieces")
    weight: float = Field(..., ge=0, description="Weight in pounds")

    dex_bonus: bool | None = Field(None, description="Can add Dex bonus to AC")
    max_dex_bonus: int | None = Field(None, description="Maximum Dex bonus")
    strength_required: int | None = Field(None, description="Minimum Strength required")
    stealth_disadvantage: bool = Field(False, description="Imposes disadvantage on Stealth")
