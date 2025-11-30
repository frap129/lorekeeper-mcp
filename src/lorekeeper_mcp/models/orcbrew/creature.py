"""OrcBrew creature model with relaxed constraints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field, model_validator

from lorekeeper_mcp.models.base import BaseEntity

if TYPE_CHECKING:
    from lorekeeper_mcp.models.creature import Creature

# Challenge rating decimal values for fractional CRs
CR_ONE_EIGHTH = 0.125
CR_ONE_QUARTER = 0.25
CR_ONE_HALF = 0.5


class OrcBrewCreature(BaseEntity):
    """Creature model for OrcBrew data with optional fields.

    OrcBrew creature data often lacks fields like armor_class, hit_points, hit_dice,
    alignment that are required in the canonical Creature model.

    Note: This does NOT inherit from Creature to avoid type errors with optional fields.
    """

    # Required fields
    size: str = Field(..., description="Size category (Tiny, Small, Medium, Large, etc.)")
    type: str = Field(..., description="Creature type (humanoid, beast, dragon, etc.)")

    # Optional fields (required in canonical Creature)
    alignment: str | None = Field(None, description="Alignment")
    armor_class: int | None = Field(None, ge=0, description="Armor class")
    hit_points: int | None = Field(None, ge=0, description="Average hit points")
    hit_dice: str | None = Field(None, description="Hit dice formula")
    challenge_rating: str | None = Field(None, description="Challenge rating (CR)")
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
    def normalize_orcbrew_creature(cls, data: Any) -> Any:
        """Normalize OrcBrew creature fields.

        Handles 'challenge' -> 'challenge_rating' conversion.
        """
        if not isinstance(data, dict):
            return data

        # Handle hit_points dict format from OrcBrew (e.g., {'die': 8, 'die-count': 10, 'modifier': 20})
        if isinstance(data.get("hit_points"), dict):
            hp_dict = data["hit_points"]
            # Try to calculate average HP from die notation
            die_count = hp_dict.get("die-count") or hp_dict.get("die_count") or 0
            die = hp_dict.get("die", 0)
            modifier = hp_dict.get("modifier", 0)
            if die_count and die:
                # Average = die_count * (die + 1) / 2 + modifier
                data["hit_points"] = int(die_count * (die + 1) / 2 + modifier)
            else:
                # Fall back to just the modifier if die/die_count are not present
                data["hit_points"] = modifier if modifier else 0

        # Handle OrcBrew 'challenge' field
        if "challenge" in data and "challenge_rating" not in data:
            challenge = data["challenge"]
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

    def to_canonical(self) -> Creature:
        """Convert OrcBrew creature to canonical Creature model.

        Returns:
            Creature: A canonical Creature instance with default values for missing fields.
        """
        from lorekeeper_mcp.models.creature import Creature

        return Creature(
            name=self.name,
            slug=self.slug,
            desc=self.desc,
            document=self.document,
            document_url=self.document_url,
            source_api=self.source_api,
            size=self.size,
            type=self.type,
            alignment=self.alignment or "unaligned",
            armor_class=self.armor_class if self.armor_class is not None else 10,
            hit_points=self.hit_points if self.hit_points is not None else 1,
            hit_dice=self.hit_dice or "1d8",
            challenge_rating=self.challenge_rating or "0",
            challenge_rating_decimal=self.challenge_rating_decimal,
            strength=self.strength,
            dexterity=self.dexterity,
            constitution=self.constitution,
            intelligence=self.intelligence,
            wisdom=self.wisdom,
            charisma=self.charisma,
            speed=self.speed,
            actions=self.actions,
            legendary_actions=self.legendary_actions,
            special_abilities=self.special_abilities,
        )
