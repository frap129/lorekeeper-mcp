"""Creature model for D&D 5e creatures (formerly Monster)."""

import warnings
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
    (Open5e API v1/v2, OrcBrew). Formerly named Monster.
    """

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
    actions: list[dict[str, Any]] | None = Field(None, description="Actions")
    legendary_actions: list[dict[str, Any]] | None = Field(None, description="Legendary actions")
    special_abilities: list[dict[str, Any]] | None = Field(None, description="Special abilities")

    @model_validator(mode="before")
    @classmethod
    def normalize_creature_fields(cls, data: Any) -> Any:
        """Normalize creature-specific fields.

        - 'challenge' -> 'challenge_rating' (OrcBrew uses 'challenge')
        """
        if not isinstance(data, dict):
            return data

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


class Monster(Creature):
    """Deprecated alias for Creature.

    Use Creature instead. This alias exists for backward compatibility
    and will be removed in a future release.
    """

    @model_validator(mode="before")
    @classmethod
    def emit_deprecation_warning(cls, data: Any) -> Any:
        """Emit deprecation warning when Monster is instantiated.

        The stacklevel is set to point to the caller's code (the line where Monster()
        is instantiated), not to the internal Pydantic validation machinery.

        Call stack when warning is emitted:
        1. emit_deprecation_warning (this function)
        2. Pydantic __init__ / validate_python
        3. Caller's code (Monster instantiation) <- we want to point here

        stacklevel=3 points to frame 3 up from warnings.warn().
        """
        warnings.warn(
            "Monster is deprecated, use Creature instead. "
            "Monster will be removed in a future release.",
            DeprecationWarning,
            stacklevel=3,
        )
        return data
