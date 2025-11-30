"""OrcBrew spell model with relaxed constraints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field, model_validator

from lorekeeper_mcp.models.base import BaseEntity

if TYPE_CHECKING:
    from lorekeeper_mcp.models.spell import Spell


class OrcBrewSpell(BaseEntity):
    """Spell model for OrcBrew data with optional fields.

    OrcBrew spell data often lacks fields like casting_time, range, duration
    that are required in the canonical Spell model.

    Note: This does NOT inherit from Spell to avoid the parent's validators
    that set default values for required fields.
    """

    level: int = Field(..., ge=0, le=9, description="Spell level (0-9, 0=cantrip)")
    school: str = Field(..., description="Magic school (Evocation, Conjuration, etc.)")

    # Optional fields for OrcBrew (required in canonical Spell)
    casting_time: str | None = Field(None, description="Time required to cast")
    range: str | None = Field(None, description="Spell range")
    duration: str | None = Field(None, description="Spell duration")

    # Other optional fields
    components: str = Field(default="", description="Components (V, S, M)")
    concentration: bool = Field(False, description="Requires concentration")
    ritual: bool = Field(False, description="Can be cast as ritual")
    material: str | None = Field(None, description="Material components")
    higher_level: str | None = Field(None, description="Higher level casting effects")
    damage_type: list[str] | None = Field(None, description="Damage types dealt")
    classes: list[str] = Field(
        default_factory=list, description="Classes that can learn this spell"
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_orcbrew_spell_fields(cls, data: Any) -> Any:
        """Normalize OrcBrew spell fields without setting defaults for optional fields."""
        if not isinstance(data, dict):
            return data

        # Parse school from dict if needed
        if isinstance(data.get("school"), dict):
            data["school"] = data["school"].get("name", str(data["school"]))

        # Handle components - default to empty if missing
        if "components" not in data or not data["components"]:
            data["components"] = ""
        elif isinstance(data["components"], dict):
            # OrcBrew format: {'verbal': True, 'somatic': True, 'material': True}
            components_dict = data["components"]
            parts = []
            if components_dict.get("verbal"):
                parts.append("V")
            if components_dict.get("somatic"):
                parts.append("S")
            if components_dict.get("material"):
                parts.append("M")
            data["components"] = ", ".join(parts)

            # Extract material description if present
            if "material-component" in components_dict:
                data["material"] = components_dict["material-component"]
        elif isinstance(data["components"], list):
            data["components"] = ", ".join(str(c) for c in data["components"])

        # Handle material - convert bool to None or string
        if isinstance(data.get("material"), bool) or not data.get("material"):
            data["material"] = None

        # Parse classes - extract index/key from class objects
        if "classes" in data:
            classes = data["classes"]
            if isinstance(classes, list):
                extracted_classes: list[str] = []
                for c in classes:
                    if isinstance(c, dict):
                        class_key = c.get("index") or c.get("name") or str(c)
                        extracted_classes.append(class_key.lower())
                    else:
                        extracted_classes.append(str(c).lower())
                data["classes"] = extracted_classes
            elif isinstance(classes, str):
                data["classes"] = [classes.lower()]
            else:
                data["classes"] = []
        else:
            data["classes"] = []

        # Generate slug from name if not provided
        if not data.get("slug") and not data.get("key") and data.get("name"):
            data["slug"] = data["name"].lower().replace(" ", "-").replace("'", "").replace("/", "-")

        return data

    def to_canonical(self) -> Spell:
        """Convert OrcBrew spell to canonical Spell model.

        Returns:
            Spell: A canonical Spell instance with default values for missing fields.
        """
        from lorekeeper_mcp.models.spell import Spell

        return Spell(
            name=self.name,
            slug=self.slug,
            desc=self.desc,
            document=self.document,
            document_url=self.document_url,
            source_api=self.source_api,
            level=self.level,
            school=self.school,
            casting_time=self.casting_time or "Unknown",
            range=self.range or "Self",
            duration=self.duration or "Instantaneous",
            components=self.components,
            concentration=self.concentration,
            ritual=self.ritual,
            material=self.material,
            higher_level=self.higher_level,
            damage_type=self.damage_type,
            classes=self.classes,
        )
