"""Spell model for D&D 5e spells."""

from pydantic import Field

from lorekeeper_mcp.api_clients.models.base import BaseModel


class Spell(BaseModel):
    """Model representing a D&D 5e spell."""

    level: int = Field(..., ge=0, le=9, description="Spell level (0-9, 0=cantrip)")
    school: str = Field(..., description="Magic school (Evocation, Conjuration, etc.)")
    casting_time: str = Field(..., description="Time required to cast")
    range: str = Field(..., description="Spell range")
    components: str = Field(..., description="Components (V, S, M)")
    duration: str = Field(..., description="Spell duration")
    concentration: bool = Field(False, description="Requires concentration")
    ritual: bool = Field(False, description="Can be cast as ritual")
    material: str | None = Field(None, description="Material components")
    higher_level: str | None = Field(None, description="Higher level casting effects")
    damage_type: list[str] | None = Field(None, description="Damage types dealt")
