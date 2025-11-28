# Standardize Canonical Models Implementation Plan

**Goal:** Create a unified `models/` package with canonical Pydantic models, rename Monster to Creature, add OrcBrew validation, and ensure repositories only deal with canonical models.

**Architecture:** New `src/lorekeeper_mcp/models/` package becomes the single source of truth for all entity models. API clients transform responses into canonical models. OrcBrew parser validates through relaxed OrcBrew-specific models. Repositories accept and return only canonical Pydantic models (not dicts).

**Tech Stack:** Pydantic v2 with model validators, Python 3.11+ type hints, pytest for TDD

---

## Task 1: Create Canonical Models Package Structure

**Files:**
- Create: `src/lorekeeper_mcp/models/__init__.py`
- Create: `src/lorekeeper_mcp/models/base.py`
- Test: `tests/test_models/__init__.py`
- Test: `tests/test_models/test_base.py`

**Step 1: Create the models directory**

Run: `mkdir -p src/lorekeeper_mcp/models tests/test_models`

**Step 2: Write failing test for base model with slug normalizer**

Create `tests/test_models/test_base.py`:
```python
"""Tests for canonical base models."""

import pytest

from lorekeeper_mcp.models.base import BaseEntity


class TestBaseEntity:
    """Tests for BaseEntity model."""

    def test_base_entity_required_fields(self) -> None:
        """Test that BaseEntity validates required fields."""
        entity = BaseEntity(name="Test Item", slug="test-item")
        assert entity.name == "Test Item"
        assert entity.slug == "test-item"

    def test_base_entity_normalizes_key_to_slug(self) -> None:
        """Test that 'key' field is normalized to 'slug'."""
        entity = BaseEntity(name="Test", key="test-key")
        assert entity.slug == "test-key"

    def test_base_entity_slug_takes_precedence_over_key(self) -> None:
        """Test that explicit slug takes precedence over key."""
        entity = BaseEntity(name="Test", slug="explicit-slug", key="key-value")
        assert entity.slug == "explicit-slug"

    def test_base_entity_normalizes_description_to_desc(self) -> None:
        """Test that 'description' field is normalized to 'desc'."""
        entity = BaseEntity(name="Test", slug="test", description="A description")
        assert entity.desc == "A description"

    def test_base_entity_desc_takes_precedence_over_description(self) -> None:
        """Test that explicit desc takes precedence over description."""
        entity = BaseEntity(name="Test", slug="test", desc="explicit", description="ignored")
        assert entity.desc == "explicit"

    def test_base_entity_missing_slug_and_key_raises_error(self) -> None:
        """Test that missing both slug and key raises validation error."""
        with pytest.raises(ValueError):
            BaseEntity(name="Test")
```

Create `tests/test_models/__init__.py`:
```python
"""Tests for canonical models."""
```

**Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_models/test_base.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.models'"

**Step 4: Write minimal implementation**

Create `src/lorekeeper_mcp/models/__init__.py`:
```python
"""Canonical Pydantic models for LoreKeeper entities.

This package contains the single source of truth for all entity models.
All data sources (API clients, OrcBrew parser) transform to these models.
"""

from lorekeeper_mcp.models.base import BaseEntity

__all__ = ["BaseEntity"]
```

Create `src/lorekeeper_mcp/models/base.py`:
```python
"""Base canonical models with shared validators."""

from typing import Any

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, model_validator


class BaseEntity(PydanticBaseModel):
    """Base model for all canonical entities.

    Includes shared validators for:
    - Normalizing 'key' to 'slug'
    - Normalizing 'description' to 'desc'
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    name: str = Field(..., description="Name of the entity")
    slug: str = Field(..., description="URL-safe identifier")
    desc: str | None = Field(None, description="Description text")
    document: str | None = Field(None, description="Source document name")
    document_url: str | None = Field(None, description="Source document URL")
    source_api: str | None = Field(None, description="Source API (open5e, orcbrew)")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        """Normalize field names from various sources.

        - 'key' -> 'slug' (OrcBrew and Open5e v2 use 'key')
        - 'description' -> 'desc' (OrcBrew uses 'description')
        """
        if not isinstance(data, dict):
            return data

        # Normalize key -> slug
        if "key" in data and "slug" not in data:
            data["slug"] = data["key"]

        # Normalize description -> desc
        if "description" in data and "desc" not in data:
            data["desc"] = data["description"]

        return data
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_models/test_base.py -v`
Expected: PASS (all 6 tests)

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/models/ tests/test_models/
git commit -m "feat(models): add canonical BaseEntity with field normalizers"
```

---

## Task 2: Create Creature Model (Rename from Monster)

**Files:**
- Create: `src/lorekeeper_mcp/models/creature.py`
- Modify: `src/lorekeeper_mcp/models/__init__.py`
- Test: `tests/test_models/test_creature.py`

**Step 1: Write failing test for Creature model**

Create `tests/test_models/test_creature.py`:
```python
"""Tests for canonical Creature model."""

import warnings

import pytest
from pydantic import ValidationError

from lorekeeper_mcp.models import Creature, Monster


class TestCreature:
    """Tests for Creature model."""

    def test_creature_minimal_fields(self) -> None:
        """Test Creature with minimal required fields."""
        creature = Creature(
            name="Goblin",
            slug="goblin",
            size="Small",
            type="humanoid",
            alignment="neutral evil",
            armor_class=15,
            hit_points=7,
            hit_dice="2d6",
            challenge_rating="1/4",
        )
        assert creature.name == "Goblin"
        assert creature.size == "Small"
        assert creature.challenge_rating == "1/4"

    def test_creature_normalizes_key_to_slug(self) -> None:
        """Test that key is normalized to slug."""
        creature = Creature(
            name="Goblin",
            key="goblin-key",
            size="Small",
            type="humanoid",
            alignment="neutral evil",
            armor_class=15,
            hit_points=7,
            hit_dice="2d6",
            challenge_rating="1/4",
        )
        assert creature.slug == "goblin-key"

    def test_creature_with_ability_scores(self) -> None:
        """Test Creature with ability scores."""
        creature = Creature(
            name="Goblin",
            slug="goblin",
            size="Small",
            type="humanoid",
            alignment="neutral evil",
            armor_class=15,
            hit_points=7,
            hit_dice="2d6",
            challenge_rating="1/4",
            strength=8,
            dexterity=14,
            constitution=10,
        )
        assert creature.strength == 8
        assert creature.dexterity == 14

    def test_creature_invalid_ability_score_below_minimum(self) -> None:
        """Test that ability scores below 1 are rejected."""
        with pytest.raises(ValidationError):
            Creature(
                name="Invalid",
                slug="invalid",
                size="Medium",
                type="humanoid",
                alignment="neutral",
                armor_class=10,
                hit_points=10,
                hit_dice="2d6",
                challenge_rating="1",
                strength=0,
            )

    def test_monster_alias_with_deprecation_warning(self) -> None:
        """Test that Monster alias works but emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            monster = Monster(
                name="Goblin",
                slug="goblin",
                size="Small",
                type="humanoid",
                alignment="neutral evil",
                armor_class=15,
                hit_points=7,
                hit_dice="2d6",
                challenge_rating="1/4",
            )
            assert monster.name == "Goblin"
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
            assert "Creature" in str(w[0].message)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models/test_creature.py -v`
Expected: FAIL with "ImportError: cannot import name 'Creature' from 'lorekeeper_mcp.models'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/models/creature.py`:
```python
"""Creature model for D&D 5e creatures (formerly Monster)."""

import warnings
from typing import Any

from pydantic import Field, model_validator

from lorekeeper_mcp.models.base import BaseEntity


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
                if challenge == 0.125:
                    data["challenge_rating"] = "1/8"
                elif challenge == 0.25:
                    data["challenge_rating"] = "1/4"
                elif challenge == 0.5:
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


def _create_monster_with_warning(*args: Any, **kwargs: Any) -> Creature:
    """Factory function that creates a Creature with deprecation warning."""
    warnings.warn(
        "Monster is deprecated, use Creature instead. "
        "Monster will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    return Creature(*args, **kwargs)


class _MonsterMeta(type):
    """Metaclass to emit deprecation warning when Monster is instantiated."""

    def __call__(cls, *args: Any, **kwargs: Any) -> Creature:
        return _create_monster_with_warning(*args, **kwargs)


class Monster(Creature, metaclass=_MonsterMeta):
    """Deprecated alias for Creature.

    Use Creature instead. This alias exists for backward compatibility
    and will be removed in a future release.
    """

    pass
```

Update `src/lorekeeper_mcp/models/__init__.py`:
```python
"""Canonical Pydantic models for LoreKeeper entities.

This package contains the single source of truth for all entity models.
All data sources (API clients, OrcBrew parser) transform to these models.
"""

from lorekeeper_mcp.models.base import BaseEntity
from lorekeeper_mcp.models.creature import Creature, Monster

__all__ = ["BaseEntity", "Creature", "Monster"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models/test_creature.py -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/models/creature.py src/lorekeeper_mcp/models/__init__.py tests/test_models/test_creature.py
git commit -m "feat(models): add Creature model with Monster deprecation alias"
```

---

## Task 3: Create Canonical Spell Model

**Files:**
- Create: `src/lorekeeper_mcp/models/spell.py`
- Modify: `src/lorekeeper_mcp/models/__init__.py`
- Test: `tests/test_models/test_spell.py`

**Step 1: Write failing test for Spell model**

Create `tests/test_models/test_spell.py`:
```python
"""Tests for canonical Spell model."""

import pytest
from pydantic import ValidationError

from lorekeeper_mcp.models import Spell


class TestSpell:
    """Tests for Spell model."""

    def test_spell_minimal_fields(self) -> None:
        """Test Spell with minimal required fields."""
        spell = Spell(
            name="Fireball",
            slug="fireball",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
        )
        assert spell.name == "Fireball"
        assert spell.level == 3
        assert spell.school == "Evocation"

    def test_spell_normalizes_key_to_slug(self) -> None:
        """Test that key is normalized to slug."""
        spell = Spell(
            name="Fireball",
            key="fireball-key",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
        )
        assert spell.slug == "fireball-key"

    def test_spell_normalizes_school_from_dict(self) -> None:
        """Test that school object is normalized to string."""
        spell = Spell(
            name="Fireball",
            slug="fireball",
            level=3,
            school={"name": "Evocation", "key": "evocation"},
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
        )
        assert spell.school == "Evocation"

    def test_spell_extracts_classes_from_objects(self) -> None:
        """Test that class objects are normalized to list of strings."""
        spell = Spell(
            name="Fireball",
            slug="fireball",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
            classes=[
                {"index": "wizard", "name": "Wizard"},
                {"index": "sorcerer", "name": "Sorcerer"},
            ],
        )
        assert spell.classes == ["wizard", "sorcerer"]

    def test_spell_generates_slug_from_name(self) -> None:
        """Test that slug is generated from name if not provided."""
        spell = Spell(
            name="Magic Missile",
            level=1,
            school="Evocation",
            casting_time="1 action",
            range="120 feet",
            duration="Instantaneous",
        )
        assert spell.slug == "magic-missile"

    def test_spell_cantrip_level_zero(self) -> None:
        """Test cantrip with level 0."""
        spell = Spell(
            name="Fire Bolt",
            slug="fire-bolt",
            level=0,
            school="Evocation",
            casting_time="1 action",
            range="120 feet",
            duration="Instantaneous",
        )
        assert spell.level == 0

    def test_spell_invalid_level_raises_error(self) -> None:
        """Test that invalid spell level raises error."""
        with pytest.raises(ValidationError):
            Spell(
                name="Invalid",
                slug="invalid",
                level=10,  # Invalid: max is 9
                school="Evocation",
                casting_time="1 action",
                range="Self",
                duration="Instantaneous",
            )
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models/test_spell.py -v`
Expected: FAIL with "ImportError: cannot import name 'Spell' from 'lorekeeper_mcp.models'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/models/spell.py`:
```python
"""Spell model for D&D 5e spells."""

from typing import Any

from pydantic import Field, model_validator

from lorekeeper_mcp.models.base import BaseEntity


class Spell(BaseEntity):
    """Model representing a D&D 5e spell.

    This is the canonical model for spells from any source
    (Open5e API v1/v2, OrcBrew).
    """

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
    def normalize_spell_fields(cls, data: Any) -> Any:
        """Normalize spell-specific fields from various API formats."""
        if not isinstance(data, dict):
            return data

        # Parse school from dict if needed (Open5e v2 format)
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
            data["slug"] = (
                data["name"].lower().replace(" ", "-").replace("'", "").replace("/", "-")
            )

        return data
```

Update `src/lorekeeper_mcp/models/__init__.py`:
```python
"""Canonical Pydantic models for LoreKeeper entities.

This package contains the single source of truth for all entity models.
All data sources (API clients, OrcBrew parser) transform to these models.
"""

from lorekeeper_mcp.models.base import BaseEntity
from lorekeeper_mcp.models.creature import Creature, Monster
from lorekeeper_mcp.models.spell import Spell

__all__ = ["BaseEntity", "Creature", "Monster", "Spell"]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models/test_spell.py -v`
Expected: PASS (all 7 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/models/spell.py src/lorekeeper_mcp/models/__init__.py tests/test_models/test_spell.py
git commit -m "feat(models): add canonical Spell model with field normalizers"
```

---

## Task 4: Create Equipment Models (Weapon, Armor, MagicItem)

**Files:**
- Create: `src/lorekeeper_mcp/models/equipment.py`
- Modify: `src/lorekeeper_mcp/models/__init__.py`
- Test: `tests/test_models/test_equipment.py`

**Step 1: Write failing test for equipment models**

Create `tests/test_models/test_equipment.py`:
```python
"""Tests for canonical equipment models."""

import pytest
from pydantic import ValidationError

from lorekeeper_mcp.models import Armor, MagicItem, Weapon


class TestWeapon:
    """Tests for Weapon model."""

    def test_weapon_minimal_fields(self) -> None:
        """Test Weapon with required fields."""
        weapon = Weapon(
            name="Dagger",
            slug="dagger",
            damage_dice="1d4",
            damage_type="Piercing",
            range=20.0,
            long_range=60.0,
            distance_unit="feet",
            is_simple=True,
            is_improvised=False,
        )
        assert weapon.name == "Dagger"
        assert weapon.damage_dice == "1d4"
        assert weapon.damage_type == "Piercing"

    def test_weapon_normalizes_key_to_slug(self) -> None:
        """Test that key is normalized to slug."""
        weapon = Weapon(
            name="Dagger",
            key="srd-2024_dagger",
            damage_dice="1d4",
            damage_type="Piercing",
            range=20.0,
            long_range=60.0,
            distance_unit="feet",
            is_simple=True,
            is_improvised=False,
        )
        assert weapon.slug == "srd-2024_dagger"

    def test_weapon_extracts_damage_type_from_dict(self) -> None:
        """Test that damage_type object is normalized to string."""
        weapon = Weapon(
            name="Dagger",
            slug="dagger",
            damage_dice="1d4",
            damage_type={"name": "Piercing", "key": "piercing"},
            range=20.0,
            long_range=60.0,
            distance_unit="feet",
            is_simple=True,
            is_improvised=False,
        )
        assert weapon.damage_type == "Piercing"

    def test_weapon_with_properties(self) -> None:
        """Test Weapon with property list."""
        weapon = Weapon(
            name="Longsword",
            slug="longsword",
            damage_dice="1d8",
            damage_type="Slashing",
            range=0.0,
            long_range=0.0,
            distance_unit="feet",
            is_simple=False,
            is_improvised=False,
            properties=["Versatile"],
            versatile_dice="1d10",
        )
        assert weapon.properties == ["Versatile"]
        assert weapon.versatile_dice == "1d10"

    def test_weapon_extracts_properties_from_complex_structure(self) -> None:
        """Test that complex property objects are normalized to strings."""
        weapon = Weapon(
            name="Dagger",
            slug="dagger",
            damage_dice="1d4",
            damage_type="Piercing",
            range=20.0,
            long_range=60.0,
            distance_unit="feet",
            is_simple=True,
            is_improvised=False,
            properties=[
                {"property": {"name": "Finesse", "type": None}},
                {"property": {"name": "Light", "type": None}},
            ],
        )
        assert weapon.properties == ["Finesse", "Light"]


class TestArmor:
    """Tests for Armor model."""

    def test_armor_minimal_fields(self) -> None:
        """Test Armor with required fields."""
        armor = Armor(
            name="Chain Mail",
            slug="chain-mail",
            category="Heavy",
        )
        assert armor.name == "Chain Mail"
        assert armor.category == "Heavy"

    def test_armor_with_all_fields(self) -> None:
        """Test Armor with all optional fields."""
        armor = Armor(
            name="Chain Mail",
            slug="chain-mail",
            category="Heavy",
            base_ac=16,
            cost="75 gp",
            weight=55.0,
            stealth_disadvantage=True,
            strength_required=13,
        )
        assert armor.base_ac == 16
        assert armor.stealth_disadvantage is True
        assert armor.strength_required == 13


class TestMagicItem:
    """Tests for MagicItem model."""

    def test_magic_item_minimal_fields(self) -> None:
        """Test MagicItem with required fields."""
        item = MagicItem(
            name="Bag of Holding",
            slug="bag-of-holding",
        )
        assert item.name == "Bag of Holding"

    def test_magic_item_with_attunement(self) -> None:
        """Test MagicItem with attunement requirement."""
        item = MagicItem(
            name="Ring of Protection",
            slug="ring-of-protection",
            rarity="rare",
            requires_attunement=True,
            type="ring",
        )
        assert item.requires_attunement is True
        assert item.rarity == "rare"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models/test_equipment.py -v`
Expected: FAIL with "ImportError: cannot import name 'Weapon' from 'lorekeeper_mcp.models'"

**Step 3: Write minimal implementation**

Create `src/lorekeeper_mcp/models/equipment.py`:
```python
"""Equipment models for weapons, armor, and magic items."""

from typing import Any

from pydantic import Field, model_validator

from lorekeeper_mcp.models.base import BaseEntity


class Weapon(BaseEntity):
    """Model representing a D&D 5e weapon.

    Simplified model that stores damage_type as string (not nested object).
    """

    damage_dice: str = Field(..., description="Damage dice (e.g., 1d8)")
    damage_type: str = Field(..., description="Damage type name (e.g., Piercing)")
    properties: list[str] = Field(
        default_factory=list,
        description="Weapon properties (Finesse, Light, etc.)",
    )
    range: float = Field(..., ge=0, description="Normal range in distance units")
    long_range: float = Field(..., ge=0, description="Long range in distance units")
    distance_unit: str = Field(..., description="Unit of distance measurement")
    is_simple: bool = Field(..., description="Whether weapon is Simple (vs Martial)")
    is_improvised: bool = Field(..., description="Whether weapon is improvised")

    # Optional fields
    category: str | None = Field(None, description="Weapon category (derived)")
    cost: str | None = Field(None, description="Cost in gold pieces")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")
    range_normal: int | None = Field(None, description="Normal range (legacy name)")
    range_long: int | None = Field(None, description="Long range (legacy name)")
    versatile_dice: str | None = Field(None, description="Versatile damage dice")

    @model_validator(mode="before")
    @classmethod
    def normalize_weapon_fields(cls, data: Any) -> Any:
        """Normalize weapon-specific fields from API format."""
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


class Armor(BaseEntity):
    """Model representing D&D 5e armor."""

    category: str = Field(..., description="Armor category (Light, Medium, Heavy, Shield)")
    base_ac: int | None = Field(None, ge=0, description="Base armor class")
    cost: str | None = Field(None, description="Cost in gold pieces")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")

    dex_bonus: bool | None = Field(None, description="Can add Dex bonus to AC")
    max_dex_bonus: int | None = Field(None, description="Maximum Dex bonus")
    strength_required: int | None = Field(None, description="Minimum Strength required")
    stealth_disadvantage: bool = Field(False, description="Imposes disadvantage on Stealth")


class MagicItem(BaseEntity):
    """Model representing a D&D 5e magic item."""

    rarity: str | None = Field(None, description="Rarity level (common to artifact)")
    requires_attunement: bool | None = Field(
        None, description="Whether item requires attunement"
    )
    type: str | None = Field(None, description="Type of item (wondrous, wand, ring, etc.)")
    wondrous: bool | None = Field(None, description="Whether item is wondrous")
    weight: float | None = Field(None, ge=0, description="Weight in pounds")
    armor_class: int | None = Field(None, ge=0, description="AC bonus if armor")
    damage: str | None = Field(None, description="Damage if weapon")
```

Update `src/lorekeeper_mcp/models/__init__.py`:
```python
"""Canonical Pydantic models for LoreKeeper entities.

This package contains the single source of truth for all entity models.
All data sources (API clients, OrcBrew parser) transform to these models.
"""

from lorekeeper_mcp.models.base import BaseEntity
from lorekeeper_mcp.models.creature import Creature, Monster
from lorekeeper_mcp.models.equipment import Armor, MagicItem, Weapon
from lorekeeper_mcp.models.spell import Spell

__all__ = [
    "Armor",
    "BaseEntity",
    "Creature",
    "MagicItem",
    "Monster",
    "Spell",
    "Weapon",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models/test_equipment.py -v`
Expected: PASS (all 9 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/models/equipment.py src/lorekeeper_mcp/models/__init__.py tests/test_models/test_equipment.py
git commit -m "feat(models): add canonical Weapon, Armor, MagicItem models"
```

---

## Task 5: Create OrcBrew Validation Models

**Files:**
- Create: `src/lorekeeper_mcp/models/orcbrew/__init__.py`
- Create: `src/lorekeeper_mcp/models/orcbrew/spell.py`
- Create: `src/lorekeeper_mcp/models/orcbrew/creature.py`
- Create: `src/lorekeeper_mcp/models/orcbrew/equipment.py`
- Modify: `src/lorekeeper_mcp/models/__init__.py`
- Test: `tests/test_models/test_orcbrew.py`

**Step 1: Write failing test for OrcBrew models**

Create `tests/test_models/test_orcbrew.py`:
```python
"""Tests for OrcBrew-specific validation models."""

import pytest
from pydantic import ValidationError

from lorekeeper_mcp.models.orcbrew import OrcBrewCreature, OrcBrewSpell


class TestOrcBrewSpell:
    """Tests for OrcBrewSpell model with relaxed constraints."""

    def test_orcbrew_spell_minimal_fields(self) -> None:
        """Test OrcBrewSpell with minimal fields (missing optional fields)."""
        spell = OrcBrewSpell(
            name="Test Spell",
            slug="test-spell",
            level=1,
            school="Evocation",
        )
        assert spell.name == "Test Spell"
        assert spell.level == 1
        # These are optional in OrcBrew models
        assert spell.casting_time is None
        assert spell.range is None
        assert spell.duration is None

    def test_orcbrew_spell_with_all_fields(self) -> None:
        """Test OrcBrewSpell with all fields populated."""
        spell = OrcBrewSpell(
            name="Fireball",
            slug="fireball",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="150 feet",
            duration="Instantaneous",
            concentration=False,
            description="A burst of flame",
        )
        assert spell.casting_time == "1 action"
        assert spell.desc == "A burst of flame"

    def test_orcbrew_spell_normalizes_description(self) -> None:
        """Test that description field is normalized to desc."""
        spell = OrcBrewSpell(
            name="Test",
            slug="test",
            level=1,
            school="Evocation",
            description="Test description",
        )
        assert spell.desc == "Test description"

    def test_orcbrew_spell_invalid_level_still_rejected(self) -> None:
        """Test that invalid level values are still rejected."""
        with pytest.raises(ValidationError):
            OrcBrewSpell(
                name="Invalid",
                slug="invalid",
                level=10,  # Still invalid
                school="Evocation",
            )


class TestOrcBrewCreature:
    """Tests for OrcBrewCreature model with relaxed constraints."""

    def test_orcbrew_creature_minimal_fields(self) -> None:
        """Test OrcBrewCreature with minimal fields."""
        creature = OrcBrewCreature(
            name="Goblin",
            slug="goblin",
            type="humanoid",
            size="Small",
            challenge=0.25,
        )
        assert creature.name == "Goblin"
        assert creature.challenge_rating == "1/4"
        assert creature.challenge_rating_decimal == 0.25
        # These are optional in OrcBrew models
        assert creature.armor_class is None
        assert creature.hit_points is None
        assert creature.hit_dice is None
        assert creature.alignment is None

    def test_orcbrew_creature_converts_challenge_to_string(self) -> None:
        """Test that numeric challenge is converted to challenge_rating string."""
        creature = OrcBrewCreature(
            name="Dragon",
            slug="dragon",
            type="dragon",
            size="Huge",
            challenge=17,
        )
        assert creature.challenge_rating == "17"
        assert creature.challenge_rating_decimal == 17.0

    def test_orcbrew_creature_handles_fractional_cr(self) -> None:
        """Test fractional challenge ratings are converted correctly."""
        # Test 1/8
        creature = OrcBrewCreature(
            name="Tiny Creature",
            slug="tiny-creature",
            type="beast",
            size="Tiny",
            challenge=0.125,
        )
        assert creature.challenge_rating == "1/8"
        assert creature.challenge_rating_decimal == 0.125

        # Test 1/2
        creature2 = OrcBrewCreature(
            name="Medium Creature",
            slug="medium-creature",
            type="beast",
            size="Medium",
            challenge=0.5,
        )
        assert creature2.challenge_rating == "1/2"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models/test_orcbrew.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'lorekeeper_mcp.models.orcbrew'"

**Step 3: Write minimal implementation**

Create directory: `mkdir -p src/lorekeeper_mcp/models/orcbrew`

Create `src/lorekeeper_mcp/models/orcbrew/__init__.py`:
```python
"""OrcBrew-specific validation models with relaxed constraints.

OrcBrew files often have incomplete data compared to API responses.
These models inherit from canonical models but make most fields optional.
"""

from lorekeeper_mcp.models.orcbrew.creature import OrcBrewCreature
from lorekeeper_mcp.models.orcbrew.spell import OrcBrewSpell

__all__ = ["OrcBrewCreature", "OrcBrewSpell"]
```

Create `src/lorekeeper_mcp/models/orcbrew/spell.py`:
```python
"""OrcBrew spell model with relaxed constraints."""

from pydantic import Field

from lorekeeper_mcp.models.spell import Spell


class OrcBrewSpell(Spell):
    """Spell model for OrcBrew data with optional fields.

    OrcBrew spell data often lacks fields like casting_time, range, duration
    that are required in the canonical Spell model.
    """

    # Override required fields to be optional
    casting_time: str | None = Field(None, description="Time required to cast")
    range: str | None = Field(None, description="Spell range")
    duration: str | None = Field(None, description="Spell duration")
```

Create `src/lorekeeper_mcp/models/orcbrew/creature.py`:
```python
"""OrcBrew creature model with relaxed constraints."""

from typing import Any

from pydantic import Field, model_validator

from lorekeeper_mcp.models.creature import Creature


class OrcBrewCreature(Creature):
    """Creature model for OrcBrew data with optional fields.

    OrcBrew creature data often lacks fields like armor_class, hit_points, hit_dice,
    alignment that are required in the canonical Creature model.
    """

    # Override required fields to be optional
    armor_class: int | None = Field(None, ge=0, description="Armor class")
    hit_points: int | None = Field(None, ge=0, description="Average hit points")
    hit_dice: str | None = Field(None, description="Hit dice formula")
    alignment: str | None = Field(None, description="Alignment")
    challenge_rating: str | None = Field(None, description="Challenge rating (CR)")

    @model_validator(mode="before")
    @classmethod
    def normalize_orcbrew_creature(cls, data: Any) -> Any:
        """Normalize OrcBrew creature fields.

        Handles 'challenge' -> 'challenge_rating' conversion.
        """
        if not isinstance(data, dict):
            return data

        # Handle OrcBrew 'challenge' field
        if "challenge" in data and "challenge_rating" not in data:
            challenge = data["challenge"]
            if isinstance(challenge, float):
                if challenge == 0.125:
                    data["challenge_rating"] = "1/8"
                elif challenge == 0.25:
                    data["challenge_rating"] = "1/4"
                elif challenge == 0.5:
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
```

Create `src/lorekeeper_mcp/models/orcbrew/equipment.py`:
```python
"""OrcBrew equipment models with relaxed constraints."""

from pydantic import Field

from lorekeeper_mcp.models.equipment import Armor, MagicItem, Weapon


class OrcBrewWeapon(Weapon):
    """Weapon model for OrcBrew data with optional fields.

    OrcBrew weapon data often lacks fields like range, long_range, distance_unit
    that are required in the canonical Weapon model.
    """

    # Override required fields to be optional
    range: float | None = Field(None, ge=0, description="Normal range")
    long_range: float | None = Field(None, ge=0, description="Long range")
    distance_unit: str | None = Field(None, description="Unit of distance")
    is_simple: bool | None = Field(None, description="Whether weapon is Simple")
    is_improvised: bool | None = Field(None, description="Whether weapon is improvised")


class OrcBrewArmor(Armor):
    """Armor model for OrcBrew data with optional fields."""

    # Override required fields to be optional
    category: str | None = Field(None, description="Armor category")


class OrcBrewMagicItem(MagicItem):
    """Magic item model for OrcBrew data with optional fields.

    Most fields are already optional in canonical MagicItem.
    """

    pass
```

Update `src/lorekeeper_mcp/models/orcbrew/__init__.py`:
```python
"""OrcBrew-specific validation models with relaxed constraints.

OrcBrew files often have incomplete data compared to API responses.
These models inherit from canonical models but make most fields optional.
"""

from lorekeeper_mcp.models.orcbrew.creature import OrcBrewCreature
from lorekeeper_mcp.models.orcbrew.equipment import (
    OrcBrewArmor,
    OrcBrewMagicItem,
    OrcBrewWeapon,
)
from lorekeeper_mcp.models.orcbrew.spell import OrcBrewSpell

__all__ = [
    "OrcBrewArmor",
    "OrcBrewCreature",
    "OrcBrewMagicItem",
    "OrcBrewSpell",
    "OrcBrewWeapon",
]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models/test_orcbrew.py -v`
Expected: PASS (all 7 tests)

**Step 5: Commit**

```bash
git add src/lorekeeper_mcp/models/orcbrew/ tests/test_models/test_orcbrew.py
git commit -m "feat(models): add OrcBrew validation models with relaxed constraints"
```

---

## Task 6: Update Tools to Use Creature

**Files:**
- Modify: `src/lorekeeper_mcp/tools/creature_lookup.py`

**Step 1: Run existing tests to establish baseline**

Run: `uv run pytest tests/test_tools/test_creature_lookup.py -v`
Expected: PASS

**Step 2: Update creature_lookup.py imports**

Modify `src/lorekeeper_mcp/tools/creature_lookup.py`:

Update imports to use canonical `Creature` model:
```python
from lorekeeper_mcp.models import Creature
```

Update any type hints and references from `Monster` to `Creature`.

**Step 3: Run tests to verify changes**

Run: `uv run pytest tests/test_tools/test_creature_lookup.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/lorekeeper_mcp/tools/creature_lookup.py
git commit -m "refactor(tools): use canonical Creature model in creature_lookup"
```

---

## Task 7: Update API Clients to Use Canonical Models

**Files:**
- Modify: `src/lorekeeper_mcp/api_clients/models/__init__.py`
- Modify: `src/lorekeeper_mcp/api_clients/open5e_v1.py`
- Modify: `src/lorekeeper_mcp/api_clients/open5e_v2.py`

**Step 1: Run existing tests to establish baseline**

Run: `uv run pytest tests/test_api_clients/ -v`
Expected: PASS (all tests should pass before changes)

**Step 2: Update api_clients/models/__init__.py to re-export from canonical models**

Modify `src/lorekeeper_mcp/api_clients/models/__init__.py`:
```python
"""Pydantic models for API response parsing and validation.

DEPRECATED: Import models from lorekeeper_mcp.models instead.
This module re-exports from the canonical models package for backward compatibility.
"""

import warnings

from lorekeeper_mcp.models import Armor, Creature, MagicItem, Spell, Weapon

# Re-export canonical models
__all__ = ["Armor", "BaseModel", "Creature", "MagicItem", "Monster", "Spell", "Weapon"]

# Keep BaseModel for backward compatibility
from lorekeeper_mcp.models.base import BaseEntity as BaseModel


def __getattr__(name: str):
    """Emit deprecation warning for Monster import."""
    if name == "Monster":
        warnings.warn(
            "Importing Monster from api_clients.models is deprecated. "
            "Use 'from lorekeeper_mcp.models import Creature' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return Creature
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

**Step 3: Update Open5e v1 client to use Creature**

Modify imports in `src/lorekeeper_mcp/api_clients/open5e_v1.py` (line 6):
```python
from lorekeeper_mcp.models import Creature
```

Update return types and docstrings - replace `Monster` with `Creature`:
- Line 24: `-> list[Creature]:`
- Line 48: `return [Creature(**monster_data) for monster_data in entities]`
- Line 54: `-> list[Creature]:`
- Line 66: `list[Creature]`

**Step 4: Update Open5e v2 client to use Creature**

Modify imports in `src/lorekeeper_mcp/api_clients/open5e_v2.py` (line 6):
```python
from lorekeeper_mcp.models import Armor, Creature, Spell, Weapon
```

Update the `_transform_creature_response` docstring (line 36-44):
```python
def _transform_creature_response(self, creature: dict[str, Any]) -> dict[str, Any] | None:
    """Transform Open5e v2 creature response to Creature model format.

    Args:
        creature: Raw creature data from Open5e v2 API

    Returns:
        Transformed creature data compatible with Creature model,
        or None if creature should be filtered out (missing required fields)
    """
```

Update `get_creatures` return type (line 392): `-> list[Creature]:`

Update `get_creatures` docstring (line 405): `List of Creature models`

Update the final return line (line 435):
```python
return [Creature.model_validate(creature) for creature in transformed_creatures]
```

**Step 5: Run tests to verify changes**

Run: `uv run pytest tests/test_api_clients/ -v`
Expected: PASS (all tests)

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/api_clients/
git commit -m "refactor(api_clients): use canonical Creature model instead of Monster"
```

---

## Task 8: Update Repositories to Use Canonical Models

**Files:**
- Modify: `src/lorekeeper_mcp/repositories/monster.py`
- Modify: `src/lorekeeper_mcp/repositories/spell.py`
- Modify: `src/lorekeeper_mcp/repositories/equipment.py`

**Step 1: Run existing tests to establish baseline**

Run: `uv run pytest tests/test_repositories/ -v`
Expected: PASS (all tests should pass before changes)

**Step 2: Update monster repository to use Creature**

Modify `src/lorekeeper_mcp/repositories/monster.py`:

Update imports (line 5):
```python
from lorekeeper_mcp.models import Creature
```

Update protocol (lines 11-16):
```python
class CreatureClient(Protocol):
    """Protocol for creature API client."""

    async def get_creatures(self, **filters: Any) -> list[Creature]:
        """Fetch creatures from API with optional filters."""
        ...
```

Rename `MonsterRepository` to `CreatureRepository` and update all `Monster` references to `Creature` throughout the file.

**Step 3: Update spell repository imports**

Modify `src/lorekeeper_mcp/repositories/spell.py` (line 5):
```python
from lorekeeper_mcp.models import Spell
```

**Step 4: Update equipment repository imports**

Modify `src/lorekeeper_mcp/repositories/equipment.py` (line 5):
```python
from lorekeeper_mcp.models import Armor, MagicItem, Weapon
```

**Step 5: Run tests to verify changes**

Run: `uv run pytest tests/test_repositories/ -v`
Expected: PASS (all tests)

**Step 6: Commit**

```bash
git add src/lorekeeper_mcp/repositories/
git commit -m "refactor(repositories): use canonical models from models package"
```

---

## Task 9: Update Entity Mapper to Use OrcBrew Models

**Files:**
- Modify: `src/lorekeeper_mcp/parsers/entity_mapper.py`
- Test: `tests/test_parsers/test_entity_mapper.py`

**Step 1: Run existing tests to establish baseline**

Run: `uv run pytest tests/test_parsers/test_entity_mapper.py -v`
Expected: PASS

**Step 2: Update entity_mapper.py to validate through OrcBrew models**

Modify `src/lorekeeper_mcp/parsers/entity_mapper.py`:

Add imports at top:
```python
from pydantic import ValidationError

from lorekeeper_mcp.models.orcbrew import OrcBrewCreature, OrcBrewSpell
```

Update `normalize_entity` function to validate through Pydantic models:
```python
def normalize_entity(
    entity: dict[str, Any],
    orcbrew_type: str,
) -> dict[str, Any]:
    """Normalize OrcBrew entity to LoreKeeper format.

    Args:
        entity: OrcBrew entity dictionary
        orcbrew_type: OrcBrew entity type key

    Returns:
        Normalized entity dictionary with LoreKeeper schema

    Raises:
        ValueError: If entity is missing required fields
        ValidationError: If entity fails Pydantic validation
    """
    # Extract or generate slug
    slug = entity.get("key")
    if not slug:
        name = entity.get("name", "")
        if not name:
            raise ValueError("Entity missing both 'key' and 'name' fields")
        slug = name.lower().replace(" ", "-").replace("'", "")

    # Extract name
    name = entity.get("name", slug.replace("-", " ").title())

    # Extract source book
    source = entity.get("_source_book", "Unknown")
    if "option-pack" in entity:
        source = entity["option-pack"]

    # Extract document name
    document = entity.get("option-pack") or entity.get("_source_book", "Unknown")

    # Build base normalized entity with ALL fields from OrcBrew (not just indexed)
    normalized: dict[str, Any] = {
        "slug": slug,
        "name": name,
        "source": source,
        "source_api": "orcbrew",
        "document": document,
        "data": {k: v for k, v in entity.items() if not k.startswith("_")},
    }

    # Extract ALL OrcBrew fields to top level (comprehensive extraction)
    # This ensures fields like concentration, ritual, components are available
    for key, value in entity.items():
        if not key.startswith("_") and key not in normalized:
            # Convert kebab-case to snake_case
            snake_key = key.replace("-", "_")
            normalized[snake_key] = value

    # Copy indexed fields to top level for filtering (may override some above)
    lorekeeper_type = map_entity_type(orcbrew_type)
    if lorekeeper_type:
        normalized.update(_extract_indexed_fields(entity, lorekeeper_type))

    # Validate through OrcBrew Pydantic models
    _validate_through_model(normalized, lorekeeper_type)

    return normalized


def _validate_through_model(normalized: dict[str, Any], entity_type: str | None) -> None:
    """Validate normalized entity through appropriate OrcBrew Pydantic model.

    Args:
        normalized: Normalized entity data
        entity_type: LoreKeeper entity type

    Raises:
        ValidationError: If validation fails
    """
    if entity_type == "spells":
        OrcBrewSpell.model_validate(normalized)
    elif entity_type == "creatures":
        OrcBrewCreature.model_validate(normalized)
    # Other types don't have OrcBrew models yet - pass through
```

**Step 3: Run tests to verify changes**

Run: `uv run pytest tests/test_parsers/test_entity_mapper.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/lorekeeper_mcp/parsers/entity_mapper.py
git commit -m "feat(parsers): validate OrcBrew entities through Pydantic models"
```

---

## Task 10: Update Test Files for Monster to Creature Rename

**Files:**
- Modify: `tests/test_api_clients/test_models.py`
- Modify: `tests/test_api_clients/test_open5e_v1.py`
- Modify: `tests/test_api_clients/test_open5e_v2.py`
- Modify: `tests/test_repositories/test_monster.py`
- Modify: `tests/test_tools/test_creature_lookup.py`

**Step 1: Update test_models.py to use Creature**

Modify `tests/test_api_clients/test_models.py`:

Update imports (line 8):
```python
from lorekeeper_mcp.models import Creature
```

Rename all `test_monster_*` functions to `test_creature_*` and replace `Monster` with `Creature`.

**Step 2: Update test_open5e_v1.py imports**

Modify imports to use `Creature` instead of `Monster`.

**Step 3: Update test_open5e_v2.py imports**

Modify imports to use `Creature` instead of `Monster`.

**Step 4: Rename test_monster.py to test_creature.py**

Run:
```bash
git mv tests/test_repositories/test_monster.py tests/test_repositories/test_creature.py
```

Update all references in the file from `Monster` to `Creature`.

**Step 5: Run all tests to verify**

Run: `uv run pytest tests/ -v`
Expected: PASS

**Step 6: Commit**

```bash
git add tests/
git commit -m "test: update tests for Monster to Creature rename"
```

---

## Task 11: Update Re-exports and api_clients Cleanup

**Files:**
- Remove: `src/lorekeeper_mcp/api_clients/models/monster.py`
- Remove: `src/lorekeeper_mcp/api_clients/models/spell.py`
- Remove: `src/lorekeeper_mcp/api_clients/models/equipment.py`
- Remove: `src/lorekeeper_mcp/api_clients/models/base.py`
- Keep: `src/lorekeeper_mcp/api_clients/models/__init__.py` (re-exports)
- Modify: `src/lorekeeper_mcp/api_clients/__init__.py`

**Step 1: Verify all imports use canonical models**

Run: `rg "from lorekeeper_mcp.api_clients.models" src/`

Expected: Only `__init__.py` should import from canonical models. All other files should import from `lorekeeper_mcp.models`.

**Step 2: Update api_clients/__init__.py exports**

Modify `src/lorekeeper_mcp/api_clients/__init__.py` to re-export models from canonical location:
```python
"""API clients for external D&D data sources.

Models are now in lorekeeper_mcp.models. Imports from api_clients.models
are deprecated but still work for backward compatibility.
"""

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.open5e_v1 import Open5eV1Client
from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client

# Re-export models for backward compatibility (deprecated)
from lorekeeper_mcp.models import Armor, Creature, MagicItem, Spell, Weapon

__all__ = [
    "Armor",
    "BaseHttpClient",
    "Creature",
    "MagicItem",
    "Open5eV1Client",
    "Open5eV2Client",
    "Spell",
    "Weapon",
]
```

**Step 3: Remove old model files**

Run:
```bash
git rm src/lorekeeper_mcp/api_clients/models/monster.py
git rm src/lorekeeper_mcp/api_clients/models/spell.py
git rm src/lorekeeper_mcp/api_clients/models/equipment.py
git rm src/lorekeeper_mcp/api_clients/models/base.py
```

**Step 4: Run all tests to verify nothing breaks**

Run: `uv run pytest tests/ -v`
Expected: PASS

**Step 5: Update documentation**

Update `docs/architecture.md` if it references model locations. Key changes:
- Models now live in `src/lorekeeper_mcp/models/`
- `Monster` renamed to `Creature` (with backward-compatible alias)
- OrcBrew entities validated through `models/orcbrew/` subpackage

**Step 6: Commit**

```bash
git add -A
git commit -m "refactor(models): remove old api_clients/models files, update re-exports"
```

---

## Task 12: Final Verification and Cleanup

**Step 1: Run full test suite**

Run: `just test`
Expected: All tests PASS

**Step 2: Run linting**

Run: `just lint`
Expected: No errors

**Step 3: Run type checking**

Run: `just type-check`
Expected: No errors

**Step 4: Run live tests**

Run: `uv run pytest tests/test_tools/test_live_mcp.py -v`
Expected: All live tests PASS

**Step 5: Manual verification of OrcBrew import**

Run:
```bash
uv run python -c "
from lorekeeper_mcp.parsers.orcbrew import OrcBrewParser
from lorekeeper_mcp.parsers.entity_mapper import normalize_entity, map_entity_type
from pathlib import Path

parser = OrcBrewParser()
data = parser.parse_file(Path('tests/fixtures/sample.orcbrew'))
entities = parser.extract_entities(data)

for orcbrew_type, entity_list in entities.items():
    lk_type = map_entity_type(orcbrew_type)
    if lk_type:
        for entity in entity_list:
            normalized = normalize_entity(entity, orcbrew_type)
            print(f'{lk_type}: {normalized[\"name\"]} (slug={normalized[\"slug\"]})')
"
```
Expected: Lists spells and creatures from sample.orcbrew

**Step 6: Commit final state**

```bash
git add -A
git commit -m "chore: complete canonical models standardization"
```

---

## Task 13: Add `to_canonical()` Method to OrcBrew Models

**Files:**
- Modify: `src/lorekeeper_mcp/models/orcbrew/spell.py`
- Modify: `src/lorekeeper_mcp/models/orcbrew/creature.py`
- Modify: `src/lorekeeper_mcp/models/orcbrew/equipment.py`
- Test: `tests/test_models/test_orcbrew.py`

Per spec requirement (canonical-models/spec.md lines 151-155), OrcBrew models should provide a `to_canonical()` method to convert relaxed models to canonical models.

**Step 1: Write failing test for to_canonical() method**

Add to `tests/test_models/test_orcbrew.py`:
```python
class TestOrcBrewToCanonical:
    """Tests for to_canonical() conversion methods."""

    def test_orcbrew_spell_to_canonical(self) -> None:
        """Test converting OrcBrewSpell to canonical Spell."""
        orcbrew_spell = OrcBrewSpell(
            name="Test Spell",
            slug="test-spell",
            level=3,
            school="Evocation",
            casting_time="1 action",
            range="60 feet",
            duration="Instantaneous",
        )
        canonical = orcbrew_spell.to_canonical()

        from lorekeeper_mcp.models import Spell
        assert isinstance(canonical, Spell)
        assert canonical.name == "Test Spell"
        assert canonical.level == 3
        assert canonical.school == "Evocation"

    def test_orcbrew_spell_to_canonical_with_missing_fields(self) -> None:
        """Test converting OrcBrewSpell with missing optional fields."""
        orcbrew_spell = OrcBrewSpell(
            name="Incomplete Spell",
            slug="incomplete-spell",
            level=1,
            school="Divination",
            # Missing: casting_time, range, duration
        )
        canonical = orcbrew_spell.to_canonical()

        from lorekeeper_mcp.models import Spell
        assert isinstance(canonical, Spell)
        assert canonical.casting_time == "Unknown"  # Default for missing required
        assert canonical.range == "Unknown"
        assert canonical.duration == "Unknown"

    def test_orcbrew_creature_to_canonical(self) -> None:
        """Test converting OrcBrewCreature to canonical Creature."""
        orcbrew_creature = OrcBrewCreature(
            name="Test Monster",
            slug="test-monster",
            type="beast",
            size="Medium",
            challenge=2,
        )
        canonical = orcbrew_creature.to_canonical()

        from lorekeeper_mcp.models import Creature
        assert isinstance(canonical, Creature)
        assert canonical.name == "Test Monster"
        assert canonical.challenge_rating == "2"
        assert canonical.challenge_rating_decimal == 2.0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewToCanonical -v`
Expected: FAIL with "AttributeError: 'OrcBrewSpell' object has no attribute 'to_canonical'"

**Step 3: Implement to_canonical() in OrcBrewSpell**

Modify `src/lorekeeper_mcp/models/orcbrew/spell.py`:
```python
"""OrcBrew spell model with relaxed constraints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Any

if TYPE_CHECKING:
    from lorekeeper_mcp.models.spell import Spell as CanonicalSpell


class OrcBrewSpell(BaseModel):
    """Spell model for OrcBrew data with optional fields.

    OrcBrew spell data often lacks fields like casting_time, range, duration
    that are required in the canonical Spell model.

    Note: This does NOT inherit from Spell to avoid the parent's validators
    that set default values for required fields.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="allow",
    )

    # Required fields
    name: str = Field(..., description="Spell name")
    slug: str = Field(..., description="URL-safe identifier")
    level: int = Field(..., ge=0, le=9, description="Spell level (0-9)")
    school: str = Field(..., description="Magic school")

    # Optional fields (relaxed from canonical Spell)
    casting_time: str | None = Field(None, description="Time required to cast")
    range: str | None = Field(None, description="Spell range")
    duration: str | None = Field(None, description="Spell duration")
    components: str | None = Field(None, description="Components (V, S, M)")
    concentration: bool = Field(False, description="Requires concentration")
    ritual: bool = Field(False, description="Can be cast as ritual")
    material: str | None = Field(None, description="Material components")
    higher_level: str | None = Field(None, description="Higher level effects")
    classes: list[str] = Field(default_factory=list, description="Classes")
    desc: str | None = Field(None, description="Description text")
    document: str | None = Field(None, description="Source document")
    source_api: str | None = Field(None, description="Source API")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        """Normalize field names from OrcBrew format."""
        if not isinstance(data, dict):
            return data

        # Normalize key -> slug
        if "key" in data and "slug" not in data:
            data["slug"] = data["key"]

        # Normalize description -> desc
        if "description" in data and "desc" not in data:
            data["desc"] = data["description"]

        return data

    def to_canonical(self) -> CanonicalSpell:
        """Convert to canonical Spell model.

        Returns:
            Spell instance with same data. Missing required fields
            are set to "Unknown" placeholder.
        """
        from lorekeeper_mcp.models.spell import Spell

        return Spell(
            name=self.name,
            slug=self.slug,
            level=self.level,
            school=self.school,
            casting_time=self.casting_time or "Unknown",
            range=self.range or "Unknown",
            duration=self.duration or "Unknown",
            components=self.components or "",
            concentration=self.concentration,
            ritual=self.ritual,
            material=self.material,
            higher_level=self.higher_level,
            classes=self.classes,
            desc=self.desc,
            document=self.document,
            source_api=self.source_api,
        )
```

**Step 4: Implement to_canonical() in OrcBrewCreature**

Modify `src/lorekeeper_mcp/models/orcbrew/creature.py`:
```python
"""OrcBrew creature model with relaxed constraints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from lorekeeper_mcp.models.creature import Creature as CanonicalCreature


class OrcBrewCreature(BaseModel):
    """Creature model for OrcBrew data with optional fields.

    OrcBrew creature data often lacks fields like armor_class, hit_points, hit_dice,
    alignment that are required in the canonical Creature model.

    Note: This does NOT inherit from Creature to avoid the parent's validators
    that set default values for required fields.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="allow",
    )

    # Required fields
    name: str = Field(..., description="Creature name")
    slug: str = Field(..., description="URL-safe identifier")
    type: str = Field(..., description="Creature type")
    size: str = Field(..., description="Size category")

    # Optional fields (relaxed from canonical Creature)
    armor_class: int | None = Field(None, ge=0, description="Armor class")
    hit_points: int | None = Field(None, ge=0, description="Hit points")
    hit_dice: str | None = Field(None, description="Hit dice formula")
    alignment: str | None = Field(None, description="Alignment")
    challenge_rating: str | None = Field(None, description="Challenge rating")
    challenge_rating_decimal: float | None = Field(None, description="CR as decimal")

    # Ability scores
    strength: int | None = Field(None, ge=1, le=50)
    dexterity: int | None = Field(None, ge=1, le=50)
    constitution: int | None = Field(None, ge=1, le=50)
    intelligence: int | None = Field(None, ge=1, le=50)
    wisdom: int | None = Field(None, ge=1, le=50)
    charisma: int | None = Field(None, ge=1, le=50)

    # Optional complex fields
    speed: dict[str, int] | None = Field(None, description="Speed values")
    actions: list[dict[str, Any]] | None = Field(None, description="Actions")
    legendary_actions: list[dict[str, Any]] | None = Field(None)
    special_abilities: list[dict[str, Any]] | None = Field(None)
    desc: str | None = Field(None, description="Description")
    document: str | None = Field(None, description="Source document")
    source_api: str | None = Field(None, description="Source API")

    @model_validator(mode="before")
    @classmethod
    def normalize_orcbrew_creature(cls, data: Any) -> Any:
        """Normalize OrcBrew creature fields."""
        if not isinstance(data, dict):
            return data

        # Normalize key -> slug
        if "key" in data and "slug" not in data:
            data["slug"] = data["key"]

        # Normalize description -> desc
        if "description" in data and "desc" not in data:
            data["desc"] = data["description"]

        # Handle OrcBrew 'challenge' field
        if "challenge" in data and "challenge_rating" not in data:
            challenge = data["challenge"]
            if isinstance(challenge, float):
                if challenge == 0.125:
                    data["challenge_rating"] = "1/8"
                elif challenge == 0.25:
                    data["challenge_rating"] = "1/4"
                elif challenge == 0.5:
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

    def to_canonical(self) -> CanonicalCreature:
        """Convert to canonical Creature model.

        Returns:
            Creature instance with same data. Missing required fields
            are set to sensible defaults.
        """
        from lorekeeper_mcp.models.creature import Creature

        return Creature(
            name=self.name,
            slug=self.slug,
            size=self.size,
            type=self.type,
            alignment=self.alignment or "unaligned",
            armor_class=self.armor_class or 10,
            hit_points=self.hit_points or 1,
            hit_dice=self.hit_dice or "1d4",
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
            desc=self.desc,
            document=self.document,
            source_api=self.source_api,
        )
```

**Step 5: Implement to_canonical() in OrcBrew equipment models**

Modify `src/lorekeeper_mcp/models/orcbrew/equipment.py` similarly, adding `to_canonical()` methods to `OrcBrewWeapon`, `OrcBrewArmor`, and `OrcBrewMagicItem`.

**Step 6: Run tests to verify**

Run: `uv run pytest tests/test_models/test_orcbrew.py -v`
Expected: All tests PASS

**Step 7: Commit**

```bash
git add src/lorekeeper_mcp/models/orcbrew/ tests/test_models/test_orcbrew.py
git commit -m "feat(models): add to_canonical() method to OrcBrew models"
```

---

## Task 14: Investigate test_cross_tool_document_consistency Failure

**Files:**
- Analyze: `tests/test_tools/test_document_filtering.py`
- Potentially modify: Test or implementation

The failing test populates a cache with spells in document "Adventurer's Guide" and monsters in document "mm", then queries expecting document filtering to work across different entity types.

**Step 1: Analyze the failing test**

Read the test file and understand:
1. What entities are being cached with which documents
2. What queries are being made
3. What the expected vs actual results are

Run: `uv run pytest tests/test_tools/test_document_filtering.py::test_cross_tool_document_consistency -v --tb=long`

**Step 2: Identify root cause**

The failure occurs because "the spell repository returns spells regardless of the creature document being queried." This suggests:
- The test may be incorrectly expecting cross-entity document filtering
- Or the test setup may not correctly isolate entity types

**Step 3: Determine fix approach**

If this is a test logic issue:
- The test should not expect creature document filters to affect spell queries
- Fix the test assertions

If this is an implementation issue:
- Document filtering should be entity-type scoped
- Review the repository implementation

**Step 4: Implement fix**

Based on analysis, either:
- Update test expectations to match correct behavior
- Or fix the implementation if cross-tool document consistency is actually required

**Step 5: Verify fix**

Run: `uv run pytest tests/test_tools/test_document_filtering.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add tests/test_tools/test_document_filtering.py
git commit -m "fix(tests): correct test_cross_tool_document_consistency expectations"
```

---

## Task 15: Review Monster Deprecation Warning Stacklevel

**Files:**
- Modify: `src/lorekeeper_mcp/models/creature.py`
- Test: Manual verification

The deprecation warning uses `stacklevel=6` which may not correctly point to the caller in all contexts.

**Step 1: Test warning from different import contexts**

Run:
```python
# Test 1: Direct import
python -c "from lorekeeper_mcp.models import Monster; m = Monster(name='Test', slug='test', size='Medium', type='beast', alignment='neutral', armor_class=10, hit_points=10, hit_dice='2d6', challenge_rating='1')"

# Test 2: Import via api_clients
python -c "from lorekeeper_mcp.api_clients.models import Monster; m = Monster(name='Test', slug='test', size='Medium', type='beast', alignment='neutral', armor_class=10, hit_points=10, hit_dice='2d6', challenge_rating='1')"
```

**Step 2: Verify warning points to correct location**

The warning should point to the line where `Monster(...)` is called, not to internal model code.

**Step 3: Adjust stacklevel if needed**

If the warning points to wrong location, adjust the `stacklevel` parameter in `_create_monster_with_warning()` function.

**Step 4: Add code comment documenting expected behavior**

Add comment explaining why specific stacklevel was chosen.

**Step 5: Commit if changes needed**

```bash
git add src/lorekeeper_mcp/models/creature.py
git commit -m "fix(models): adjust Monster deprecation warning stacklevel"
```
