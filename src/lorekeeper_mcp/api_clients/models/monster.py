"""Monster model for D&D 5e creatures."""

from pydantic import Field

from lorekeeper_mcp.api_clients.models.base import BaseModel


class Monster(BaseModel):
    """Model representing a D&D 5e monster or creature."""

    size: str = Field(..., description="Size category (Tiny, Small, Medium, Large, etc.)")
    type: str = Field(..., description="Creature type (humanoid, beast, dragon, etc.)")
    alignment: str = Field(..., description="Alignment")
    armor_class: int = Field(..., ge=0, description="Armor class")
    hit_points: int = Field(..., ge=0, description="Average hit points")
    hit_dice: str = Field(..., description="Hit dice formula")
    challenge_rating: str = Field(..., description="Challenge rating (CR)")
    challenge_rating_decimal: float | None = Field(
        None, ge=0, description="Challenge rating as decimal (for range filtering)"
    )

    # Ability scores (can exceed 30 for legendary creatures)
    strength: int | None = Field(None, ge=1, le=50, description="Strength score")
    dexterity: int | None = Field(None, ge=1, le=50, description="Dexterity score")
    constitution: int | None = Field(None, ge=1, le=50, description="Constitution score")
    intelligence: int | None = Field(None, ge=1, le=50, description="Intelligence score")
    wisdom: int | None = Field(None, ge=1, le=50, description="Wisdom score")
    charisma: int | None = Field(None, ge=1, le=50, description="Charisma score")

    # Optional arrays
    speed: dict[str, int] | None = Field(None, description="Speed values")
    actions: list[dict] | None = Field(None, description="Actions")
    legendary_actions: list[dict] | None = Field(None, description="Legendary actions")
    special_abilities: list[dict] | None = Field(None, description="Special abilities")
    document: str | None = Field(None, description="Document name (e.g., 'SRD 5.1')")
