"""OrcBrew equipment models with relaxed constraints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field, model_validator

from lorekeeper_mcp.models.base import BaseEntity

if TYPE_CHECKING:
    from lorekeeper_mcp.models.equipment import Armor, MagicItem, Weapon


class OrcBrewWeapon(BaseEntity):
    """Weapon model for OrcBrew data with optional fields.

    OrcBrew weapon data often lacks fields like range, long_range, distance_unit
    that are required in the canonical Weapon model.

    Note: This does NOT inherit from Weapon to avoid type errors with optional fields.
    """

    # Required fields
    damage_dice: str = Field(..., description="Damage dice (e.g., 1d8)")
    damage_type: str = Field(..., description="Damage type name (e.g., Piercing)")

    # Optional fields (required in canonical Weapon)
    range: float | None = Field(None, ge=0, description="Normal range")
    long_range: float | None = Field(None, ge=0, description="Long range")
    distance_unit: str | None = Field(None, description="Unit of distance")
    is_simple: bool | None = Field(None, description="Whether weapon is Simple")
    is_improvised: bool | None = Field(None, description="Whether weapon is improvised")

    # Other optional fields
    properties: list[str] = Field(
        default_factory=list,
        description="Weapon properties (Finesse, Light, etc.)",
    )
    category: str | None = Field(None, description="Weapon category (derived)")
    cost: str | None = Field(None, description="Cost in gold pieces")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")
    range_normal: int | None = Field(None, description="Normal range (legacy name)")
    range_long: int | None = Field(None, description="Long range (legacy name)")
    versatile_dice: str | None = Field(None, description="Versatile damage dice")

    @model_validator(mode="before")
    @classmethod
    def normalize_orcbrew_weapon_fields(cls, data: Any) -> Any:
        """Normalize OrcBrew weapon-specific fields."""
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

    def to_canonical(self) -> Weapon:
        """Convert OrcBrew weapon to canonical Weapon model.

        Returns:
            Weapon: A canonical Weapon instance with default values for missing fields.
        """
        from lorekeeper_mcp.models.equipment import Weapon

        return Weapon(
            name=self.name,
            slug=self.slug,
            desc=self.desc,
            document=self.document,
            document_url=self.document_url,
            source_api=self.source_api,
            damage_dice=self.damage_dice,
            damage_type=self.damage_type,
            properties=self.properties,
            range=self.range if self.range is not None else 5,
            long_range=self.long_range if self.long_range is not None else 5,
            distance_unit=self.distance_unit or "feet",
            is_simple=self.is_simple if self.is_simple is not None else True,
            is_improvised=self.is_improvised if self.is_improvised is not None else False,
            category=self.category,
            cost=self.cost,
            weight=self.weight,
            range_normal=self.range_normal,
            range_long=self.range_long,
            versatile_dice=self.versatile_dice,
        )


class OrcBrewArmor(BaseEntity):
    """Armor model for OrcBrew data with optional fields.

    Note: This does NOT inherit from Armor to avoid type errors with optional fields.
    """

    # Optional fields (required in canonical Armor)
    category: str | None = Field(None, description="Armor category")

    # Other optional fields
    base_ac: int | None = Field(None, ge=0, description="Base armor class")
    cost: str | None = Field(None, description="Cost in gold pieces")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")
    dex_bonus: bool | None = Field(None, description="Can add Dex bonus to AC")
    max_dex_bonus: int | None = Field(None, description="Maximum Dex bonus")
    strength_required: int | None = Field(None, description="Minimum Strength required")
    stealth_disadvantage: bool = Field(False, description="Imposes disadvantage on Stealth")

    def to_canonical(self) -> Armor:
        """Convert OrcBrew armor to canonical Armor model.

        Returns:
            Armor: A canonical Armor instance with default values for missing fields.
        """
        from lorekeeper_mcp.models.equipment import Armor

        return Armor(
            name=self.name,
            slug=self.slug,
            desc=self.desc,
            document=self.document,
            document_url=self.document_url,
            source_api=self.source_api,
            category=self.category or "Light",
            base_ac=self.base_ac,
            cost=self.cost,
            weight=self.weight,
            dex_bonus=self.dex_bonus,
            max_dex_bonus=self.max_dex_bonus,
            strength_required=self.strength_required,
            stealth_disadvantage=self.stealth_disadvantage,
        )


class OrcBrewMagicItem(BaseEntity):
    """Magic item model for OrcBrew data with optional fields.

    Note: This does NOT inherit from MagicItem to avoid type errors.
    Most fields are already optional.
    """

    rarity: str | None = Field(None, description="Rarity level (common to artifact)")
    requires_attunement: bool | None = Field(None, description="Whether item requires attunement")
    type: str | None = Field(None, description="Type of item (wondrous, wand, ring, etc.)")
    wondrous: bool | None = Field(None, description="Whether item is wondrous")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")
    armor_class: int | None = Field(None, ge=0, description="AC bonus if armor")
    damage: str | None = Field(None, description="Damage if weapon")

    def to_canonical(self) -> MagicItem:
        """Convert OrcBrew magic item to canonical MagicItem model.

        Returns:
            MagicItem: A canonical MagicItem instance.
        """
        from lorekeeper_mcp.models.equipment import MagicItem

        return MagicItem(
            name=self.name,
            slug=self.slug,
            desc=self.desc,
            document=self.document,
            document_url=self.document_url,
            source_api=self.source_api,
            rarity=self.rarity,
            requires_attunement=self.requires_attunement,
            type=self.type,
            wondrous=self.wondrous,
            weight=self.weight,
            armor_class=self.armor_class,
            damage=self.damage,
        )
