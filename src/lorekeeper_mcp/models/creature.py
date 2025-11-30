"""Creature model for D&D 5e creatures."""

from typing import Any

from pydantic import Field, model_validator

from lorekeeper_mcp.models.base import BaseEntity

# Challenge rating decimal values for fractional CRs
CR_ONE_EIGHTH = 0.125
CR_ONE_QUARTER = 0.25
CR_ONE_HALF = 0.5


class Creature(BaseEntity):
    """Model representing a D&D 5e creature.

    This is the canonical model for creatures from any source
    (Open5e API v1/v2, OrcBrew).
    """

    size: str = Field(
        default="Medium", description="Size category (Tiny, Small, Medium, Large, etc.)"
    )
    type: str = Field(default="", description="Creature type (humanoid, beast, dragon, etc.)")
    alignment: str = Field(default="", description="Alignment")
    armor_class: int = Field(default=10, ge=0, description="Armor class")
    hit_points: int = Field(default=0, ge=0, description="Average hit points")
    hit_dice: str = Field(default="", description="Hit dice formula")
    challenge_rating: str = Field(default="0", description="Challenge rating (CR)")
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
    speed: dict[str, int] | str | None = Field(None, description="Speed values")
    actions: list[dict[str, Any]] | dict[str, Any] | None = Field(None, description="Actions")
    legendary_actions: list[dict[str, Any]] | dict[str, Any] | None = Field(
        None, description="Legendary actions"
    )
    special_abilities: list[dict[str, Any]] | dict[str, Any] | None = Field(
        None, description="Special abilities"
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_creature_fields(cls, data: Any) -> Any:
        """Normalize creature-specific fields.

        - 'challenge' -> 'challenge_rating' (OrcBrew uses 'challenge')
        - 'hit_points' dict -> int (some cached data has dict format)
        """
        if not isinstance(data, dict):
            return data

        # Handle hit_points dict format from cache (e.g., {'die-count': 6, 'die': 6})
        if isinstance(data.get("hit_points"), dict):
            hp_dict = data["hit_points"]
            # Try to calculate average HP from die notation
            die_count = hp_dict.get("die-count", hp_dict.get("die_count", 0))
            die = hp_dict.get("die", 0)
            if die_count and die:
                # Average = die_count * (die + 1) / 2
                data["hit_points"] = int(die_count * (die + 1) / 2)
            else:
                data["hit_points"] = 0

        # Normalize challenge -> challenge_rating (OrcBrew format)
        if "challenge" in data and "challenge_rating" not in data:
            challenge = data["challenge"]
            # Convert numeric challenge to string
            if isinstance(challenge, float):
                if challenge == CR_ONE_EIGHTH:
                    data["challenge_rating"] = "1/8"
                elif challenge == CR_ONE_QUARTER:
                    data["challenge_rating"] = "1/4"
                elif challenge == CR_ONE_HALF:
                    data["challenge_rating"] = "1/2"
                else:
                    data["challenge_rating"] = str(int(challenge))
                data["challenge_rating_decimal"] = challenge
            elif isinstance(challenge, int):
                data["challenge_rating"] = str(challenge)
                data["challenge_rating_decimal"] = float(challenge)
            else:
                data["challenge_rating"] = str(challenge)

        return data
