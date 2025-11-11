"""Spell model for D&D 5e spells."""

from typing import Any

from pydantic import Field, model_validator

from lorekeeper_mcp.api_clients.models.base import BaseModel


class Spell(BaseModel):
    """Model representing a D&D 5e spell."""

    level: int = Field(..., ge=0, le=9, description="Spell level (0-9, 0=cantrip)")
    school: str = Field(..., description="Magic school (Evocation, Conjuration, etc.)")
    casting_time: str = Field(..., description="Time required to cast")
    range: str = Field(..., description="Spell range")
    components: str = Field(default="", description="Components (V, S, M)")
    duration: str = Field(..., description="Spell duration")
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
    def preprocess_spell(cls, data: Any) -> Any:
        """Preprocess spell data from API response."""
        if not isinstance(data, dict):
            return data

        # Parse school from dict if needed
        if isinstance(data.get("school"), dict):
            data["school"] = data["school"].get("name", str(data["school"]))

        # Parse range from number to string
        if isinstance(data.get("range"), int | float):
            data["range"] = f"{data['range']} feet"
        elif not data.get("range"):
            data["range"] = "Self"

        # Handle components - default to empty if missing
        if "components" not in data or not data["components"]:
            data["components"] = ""
        elif isinstance(data["components"], list):
            data["components"] = ", ".join(str(c) for c in data["components"])

        # Handle material - convert bool to None or string
        if isinstance(data.get("material"), bool) or not data.get("material"):
            data["material"] = None

        # Parse classes - extract index/key from class objects
        if "classes" in data:
            classes = data["classes"]
            if isinstance(classes, list):
                # If classes are objects with index/name, extract the index
                extracted_classes: list[str] = []
                for c in classes:
                    if isinstance(c, dict):
                        # Extract index or name from dict, ensure lowercase
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
        if not data.get("slug") and data.get("name"):
            data["slug"] = data["name"].lower().replace(" ", "-").replace("'", "").replace("/", "-")

        return data
