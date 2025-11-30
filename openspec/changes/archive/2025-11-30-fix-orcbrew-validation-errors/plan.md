# Fix OrcBrew Validation Errors Implementation Plan

**Goal:** Enable OrcBrewSpell and OrcBrewCreature models to handle all OrcBrew data formats, eliminating 834 import validation errors.

**Architecture:** Add normalization logic to model validators to convert OrcBrew-specific dict formats (components, hit_points) to expected types. Update type annotations to allow alternative formats (string speed, dict metadata for actions).

**Tech Stack:** Pydantic model validators, Python type hints, pytest

---

## Task 1: Fix OrcBrewSpell Components Dict-to-String Conversion

**Files:**
- Modify: `src/lorekeeper_mcp/models/orcbrew/spell.py:44-88` (normalize_orcbrew_spell_fields validator)
- Test: `tests/test_models/test_orcbrew.py:16-70` (TestOrcBrewSpell class)

### Step 1: Write failing test for dict components conversion

Add to `tests/test_models/test_orcbrew.py` after line 70 (end of TestOrcBrewSpell class, before TestOrcBrewCreature):

```python
    def test_orcbrew_spell_components_dict_verbal_somatic(self) -> None:
        """Test that components dict is converted to string format."""
        spell = OrcBrewSpell(
            name="Test Spell",
            slug="test-spell",
            level=1,
            school="Evocation",
            components={"verbal": True, "somatic": True},
        )
        assert spell.components == "V, S"

    def test_orcbrew_spell_components_dict_all_three(self) -> None:
        """Test components dict with V, S, M."""
        spell = OrcBrewSpell(
            name="Test Spell",
            slug="test-spell",
            level=1,
            school="Evocation",
            components={"verbal": True, "somatic": True, "material": True},
        )
        assert spell.components == "V, S, M"

    def test_orcbrew_spell_components_dict_with_material_component(self) -> None:
        """Test that material-component is extracted to material field."""
        spell = OrcBrewSpell(
            name="Dawn",
            slug="dawn",
            level=5,
            school="Evocation",
            components={
                "verbal": True,
                "material": True,
                "material-component": "a sunburst pendant worth at least 100 gp",
            },
        )
        assert spell.components == "V, M"
        assert spell.material == "a sunburst pendant worth at least 100 gp"

    def test_orcbrew_spell_components_dict_only_verbal(self) -> None:
        """Test components dict with only verbal."""
        spell = OrcBrewSpell(
            name="Test Spell",
            slug="test-spell",
            level=1,
            school="Evocation",
            components={"verbal": True},
        )
        assert spell.components == "V"
```

### Step 2: Run test to verify it fails

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewSpell::test_orcbrew_spell_components_dict_verbal_somatic -xvs
```

Expected: FAIL with validation error "Input should be a valid string"

### Step 3: Implement dict-to-string conversion

In `src/lorekeeper_mcp/models/orcbrew/spell.py`, replace lines 55-59 with:

```python
        # Handle components - default to empty if missing
        if "components" not in data or not data["components"]:
            data["components"] = ""
        elif isinstance(data["components"], dict):
            # OrcBrew format: {'verbal': True, 'somatic': True, 'material': True}
            parts = []
            if data["components"].get("verbal"):
                parts.append("V")
            if data["components"].get("somatic"):
                parts.append("S")
            if data["components"].get("material"):
                parts.append("M")
            data["components"] = ", ".join(parts)

            # Extract material description if present
            if "material-component" in data["components"]:
                data["material"] = data["components"]["material-component"]
        elif isinstance(data["components"], list):
            data["components"] = ", ".join(str(c) for c in data["components"])
```

### Step 4: Run tests to verify they pass

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewSpell::test_orcbrew_spell_components_dict_verbal_somatic -xvs
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewSpell::test_orcbrew_spell_components_dict_all_three -xvs
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewSpell::test_orcbrew_spell_components_dict_with_material_component -xvs
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewSpell::test_orcbrew_spell_components_dict_only_verbal -xvs
```

Expected: All 4 tests PASS

### Step 5: Verify existing spell tests still pass

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewSpell -v
```

Expected: All tests PASS (including new ones)

### Step 6: Commit

```bash
git add tests/test_models/test_orcbrew.py src/lorekeeper_mcp/models/orcbrew/spell.py
git commit -m "feat(models): add dict-to-string conversion for OrcBrew spell components"
```

---

## Task 2: Fix OrcBrewCreature Hit Points Dict-to-Int Conversion

**Files:**
- Modify: `src/lorekeeper_mcp/models/orcbrew/creature.py:57-86` (normalize_orcbrew_creature validator)
- Test: `tests/test_models/test_orcbrew.py:72-127` (TestOrcBrewCreature class)

### Step 1: Write failing test for dict hit_points conversion

Add to `tests/test_models/test_orcbrew.py` after line 127 (end of TestOrcBrewCreature class, before TestOrcBrewWeapon):

```python
    def test_orcbrew_creature_hit_points_dict_conversion(self) -> None:
        """Test that hit_points dict is converted to integer."""
        creature = OrcBrewCreature(
            name="Test Creature",
            slug="test-creature",
            type="beast",
            size="Medium",
            hit_points={"die": 8, "die-count": 10, "modifier": 20},
        )
        # Average HP: 10 * (8 + 1) / 2 + 20 = 10 * 4.5 + 20 = 45 + 20 = 65
        assert creature.hit_points == 65

    def test_orcbrew_creature_hit_points_dict_no_modifier(self) -> None:
        """Test hit_points dict without modifier."""
        creature = OrcBrewCreature(
            name="Test Creature",
            slug="test-creature",
            type="beast",
            size="Small",
            hit_points={"die": 6, "die-count": 2},
        )
        # Average HP: 2 * (6 + 1) / 2 = 2 * 3.5 = 7
        assert creature.hit_points == 7

    def test_orcbrew_creature_hit_points_dict_with_die_count_key(self) -> None:
        """Test hit_points dict with die_count (underscore) key."""
        creature = OrcBrewCreature(
            name="Test Creature",
            slug="test-creature",
            type="dragon",
            size="Huge",
            hit_points={"die": 12, "die_count": 20, "modifier": 100},
        )
        # Average HP: 20 * (12 + 1) / 2 + 100 = 20 * 6.5 + 100 = 130 + 100 = 230
        assert creature.hit_points == 230
```

### Step 2: Run test to verify it fails

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_hit_points_dict_conversion -xvs
```

Expected: FAIL with validation error "Input should be a valid integer"

### Step 3: Implement dict-to-int conversion

In `src/lorekeeper_mcp/models/orcbrew/creature.py`, add this code after line 65 (right after `return data` check, before the challenge handling):

```python
        # Handle hit_points dict format from OrcBrew (e.g., {'die': 8, 'die-count': 10, 'modifier': 20})
        if isinstance(data.get("hit_points"), dict):
            hp_dict = data["hit_points"]
            # Try to calculate average HP from die notation
            die_count = hp_dict.get("die-count", hp_dict.get("die_count", 0))
            die = hp_dict.get("die", 0)
            modifier = hp_dict.get("modifier", 0)
            if die_count and die:
                # Average = die_count * (die + 1) / 2 + modifier
                data["hit_points"] = int(die_count * (die + 1) / 2 + modifier)
            else:
                data["hit_points"] = 0

```

### Step 4: Run tests to verify they pass

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_hit_points_dict_conversion -xvs
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_hit_points_dict_no_modifier -xvs
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_hit_points_dict_with_die_count_key -xvs
```

Expected: All 3 tests PASS

### Step 5: Verify existing creature tests still pass

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature -v
```

Expected: All tests PASS (including new ones)

### Step 6: Commit

```bash
git add tests/test_models/test_orcbrew.py src/lorekeeper_mcp/models/orcbrew/creature.py
git commit -m "feat(models): add dict-to-int conversion for OrcBrew creature hit_points"
```

---

## Task 3: Fix OrcBrewCreature Speed Type (Allow String)

**Files:**
- Modify: `src/lorekeeper_mcp/models/orcbrew/creature.py:52` (speed field type annotation)
- Test: `tests/test_models/test_orcbrew.py:72-127` (TestOrcBrewCreature class)

### Step 1: Write failing test for string speed

Add to `tests/test_models/test_orcbrew.py` after the hit_points tests (after line 127 + new tests):

```python
    def test_orcbrew_creature_speed_as_string(self) -> None:
        """Test that speed can be a string."""
        creature = OrcBrewCreature(
            name="Test Creature",
            slug="test-creature",
            type="beast",
            size="Medium",
            speed="30 ft.",
        )
        assert creature.speed == "30 ft."

    def test_orcbrew_creature_speed_as_dict(self) -> None:
        """Test that speed can still be a dict."""
        creature = OrcBrewCreature(
            name="Test Creature",
            slug="test-creature",
            type="beast",
            size="Medium",
            speed={"walk": 30, "fly": 60},
        )
        assert creature.speed == {"walk": 30, "fly": 60}
```

### Step 2: Run test to verify it fails

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_speed_as_string -xvs
```

Expected: FAIL with validation error "Input should be a valid dictionary"

### Step 3: Update type annotation to allow string

In `src/lorekeeper_mcp/models/orcbrew/creature.py`, change line 52 from:

```python
    speed: dict[str, int] | None = Field(None, description="Speed values")
```

to:

```python
    speed: dict[str, int] | str | None = Field(None, description="Speed values")
```

### Step 4: Run tests to verify they pass

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_speed_as_string -xvs
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_speed_as_dict -xvs
```

Expected: Both tests PASS

### Step 5: Verify all creature tests still pass

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature -v
```

Expected: All tests PASS

### Step 6: Commit

```bash
git add tests/test_models/test_orcbrew.py src/lorekeeper_mcp/models/orcbrew/creature.py
git commit -m "feat(models): allow string format for OrcBrew creature speed"
```

---

## Task 4: Fix OrcBrewCreature Actions/Legendary Actions Type (Allow Dict)

**Files:**
- Modify: `src/lorekeeper_mcp/models/orcbrew/creature.py:53-54` (actions and legendary_actions field type annotations)
- Test: `tests/test_models/test_orcbrew.py:72-127` (TestOrcBrewCreature class)

### Step 1: Write failing test for dict actions/legendary_actions

Add to `tests/test_models/test_orcbrew.py` after the speed tests:

```python
    def test_orcbrew_creature_legendary_actions_as_dict(self) -> None:
        """Test that legendary_actions can be a single dict (metadata)."""
        creature = OrcBrewCreature(
            name="Zuggtmoy",
            slug="zuggtmoy",
            type="fiend",
            size="Large",
            legendary_actions={
                "description": "Zuggtmoy can take 3 legendary actions, choosing from the options below."
            },
        )
        assert creature.legendary_actions == {
            "description": "Zuggtmoy can take 3 legendary actions, choosing from the options below."
        }

    def test_orcbrew_creature_legendary_actions_as_list(self) -> None:
        """Test that legendary_actions can still be a list."""
        creature = OrcBrewCreature(
            name="Test Creature",
            slug="test-creature",
            type="beast",
            size="Medium",
            legendary_actions=[
                {"name": "Attack", "desc": "The creature attacks."},
                {"name": "Move", "desc": "The creature moves."},
            ],
        )
        assert len(creature.legendary_actions) == 2

    def test_orcbrew_creature_actions_as_dict(self) -> None:
        """Test that actions can be a single dict (metadata)."""
        creature = OrcBrewCreature(
            name="Test Creature",
            slug="test-creature",
            type="beast",
            size="Medium",
            actions={"description": "On each of its turns, the creature can use its action."},
        )
        assert creature.actions == {"description": "On each of its turns, the creature can use its action."}

    def test_orcbrew_creature_actions_as_list(self) -> None:
        """Test that actions can still be a list."""
        creature = OrcBrewCreature(
            name="Test Creature",
            slug="test-creature",
            type="beast",
            size="Medium",
            actions=[
                {"name": "Bite", "desc": "Melee attack."},
                {"name": "Claw", "desc": "Melee attack."},
            ],
        )
        assert len(creature.actions) == 2
```

### Step 2: Run test to verify it fails

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_legendary_actions_as_dict -xvs
```

Expected: FAIL with validation error "Input should be a valid list"

### Step 3: Update type annotations to allow dict

In `src/lorekeeper_mcp/models/orcbrew/creature.py`, change lines 53-54 from:

```python
    actions: list[dict[str, Any]] | None = Field(None, description="Actions")
    legendary_actions: list[dict[str, Any]] | None = Field(None, description="Legendary actions")
```

to:

```python
    actions: list[dict[str, Any]] | dict[str, Any] | None = Field(None, description="Actions")
    legendary_actions: list[dict[str, Any]] | dict[str, Any] | None = Field(
        None, description="Legendary actions"
    )
```

### Step 4: Run tests to verify they pass

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_legendary_actions_as_dict -xvs
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_legendary_actions_as_list -xvs
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_actions_as_dict -xvs
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature::test_orcbrew_creature_actions_as_list -xvs
```

Expected: All 4 tests PASS

### Step 5: Verify all creature tests still pass

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py::TestOrcBrewCreature -v
```

Expected: All tests PASS

### Step 6: Commit

```bash
git add tests/test_models/test_orcbrew.py src/lorekeeper_mcp/models/orcbrew/creature.py
git commit -m "feat(models): allow dict format for OrcBrew creature actions/legendary_actions"
```

---

## Task 5: Integration Testing with MegaPak Import

**Files:**
- None modified (verification only)

### Step 1: Run full OrcBrew model test suite

Run:
```bash
uv run pytest tests/test_models/test_orcbrew.py -v
```

Expected: All tests PASS (should be 20+ tests now)

### Step 2: Run all model tests to check for regressions

Run:
```bash
uv run pytest tests/test_models/ -v
```

Expected: All tests PASS

### Step 3: Count warnings before fix (baseline)

Run:
```bash
uv run python -m lorekeeper_mcp import MegaPak_-_WotC_Books.orcbrew 2>&1 | grep "WARNING:" | wc -l
```

Expected: Shows a large number (should be 834 or close to it based on initial analysis)

### Step 4: Run MegaPak import and verify warning reduction

Run:
```bash
uv run python -m lorekeeper_mcp import MegaPak_-_WotC_Books.orcbrew 2>&1 | tee import_results.txt
```

Then count warnings:
```bash
grep "WARNING:" import_results.txt | wc -l
```

Expected: Significantly reduced warnings (ideally < 10, mostly just unsupported entity types)

### Step 5: Verify specific warning types are fixed

Run:
```bash
# Check for components validation errors (should be 0)
grep "components" import_results.txt | grep "Input should be a valid string" | wc -l

# Check for hit_points validation errors (should be 0)
grep "hit_points" import_results.txt | grep "Input should be a valid integer" | wc -l

# Check for speed validation errors (should be 0)
grep "speed" import_results.txt | grep "Input should be a valid dictionary" | wc -l

# Check for legendary_actions validation errors (should be 0)
grep "legendary_actions" import_results.txt | grep "Input should be a valid list" | wc -l
```

Expected: All counts should be 0

### Step 6: Verify expected remaining warnings

Run:
```bash
# Should only see unsupported entity type warnings
grep "WARNING:" import_results.txt | grep "unsupported type"
```

Expected output should include:
```
WARNING: Replaced unsupported EDN special float tokens (##NaN/##Inf/##-Inf) with nil
WARNING: Skipping 20 entities of unsupported type 'orcpub.dnd.e5/selections'
WARNING: Skipping 46 entities of unsupported type 'orcpub.dnd.e5/invocations'
```

### Step 7: Run full test suite

Run:
```bash
just test
```

Expected: All tests PASS

### Step 8: Clean up test output file

```bash
rm import_results.txt
```

### Step 9: Final commit

```bash
git add -A
git commit -m "test: verify MegaPak import with reduced validation errors"
```

---

## Task 6: Update Tasks Checklist

**Files:**
- Modify: `openspec/changes/fix-orcbrew-validation-errors/tasks.md`

### Step 1: Mark all tasks as complete

Update `openspec/changes/fix-orcbrew-validation-errors/tasks.md` to mark all checkboxes as `[x]`:

```markdown
## 1. Fix OrcBrewSpell Components Validation

- [x] 1.1 Add dict-to-string conversion logic to `OrcBrewSpell.normalize_orcbrew_spell_fields()` validator
- [x] 1.2 Handle dict format with keys: `verbal`, `somatic`, `material`, `material-component`
- [x] 1.3 Convert to comma-separated string format: "V, S, M"
- [x] 1.4 Extract material description from `material-component` key if present
- [x] 1.5 Add test case for dict components conversion

## 2. Fix OrcBrewCreature Hit Points Validation

- [x] 2.1 Add dict-to-int conversion logic to `OrcBrewCreature.normalize_orcbrew_creature()` validator
- [x] 2.2 Handle dict format with keys: `die`, `die-count`, `modifier`
- [x] 2.3 Calculate average HP: `die_count * (die + 1) / 2 + modifier`
- [x] 2.4 Add test case for dict hit_points conversion

## 3. Fix OrcBrewCreature Speed Type

- [x] 3.1 Update `speed` field type annotation from `dict[str, int] | None` to `dict[str, int] | str | None`
- [x] 3.2 Verify existing code handles both dict and string formats
- [x] 3.3 Add test case for string speed format

## 4. Fix OrcBrewCreature Actions/Legendary Actions Type

- [x] 4.1 Update `actions` field type from `list[dict[str, Any]] | None` to `list[dict[str, Any]] | dict[str, Any] | None`
- [x] 4.2 Update `legendary_actions` field type from `list[dict[str, Any]] | None` to `list[dict[str, Any]] | dict[str, Any] | None`
- [x] 4.3 Verify existing code handles both list and single dict formats
- [x] 4.4 Add test cases for dict metadata format

## 5. Integration Testing

- [x] 5.1 Run import on MegaPak_-_WotC_Books.orcbrew
- [x] 5.2 Verify warning count drops from 834 to near zero
- [x] 5.3 Verify imported entity counts match expected values
- [x] 5.4 Run full test suite: `just test`
- [x] 5.5 Verify no regressions in existing tests
```

### Step 2: Commit updated tasks

```bash
git add openspec/changes/fix-orcbrew-validation-errors/tasks.md
git commit -m "docs: mark all tasks complete for fix-orcbrew-validation-errors"
```

---

## Summary

After completing all tasks, you will have:

1. ✅ Added dict-to-string conversion for spell components (~141 entities fixed)
2. ✅ Added dict-to-int conversion for creature hit_points (~693 entities fixed)
3. ✅ Allowed string format for creature speed (fixes string speed errors)
4. ✅ Allowed dict format for creature actions/legendary_actions (fixes metadata dict errors)
5. ✅ Added 15 new test cases covering all new functionality
6. ✅ Verified import warnings reduced from 834 to ~3 (only unsupported entity types)
7. ✅ Confirmed no regressions in existing tests

**Files Modified:**
- `src/lorekeeper_mcp/models/orcbrew/spell.py` (components validator)
- `src/lorekeeper_mcp/models/orcbrew/creature.py` (hit_points validator, type annotations)
- `tests/test_models/test_orcbrew.py` (15 new test cases)
- `openspec/changes/fix-orcbrew-validation-errors/tasks.md` (completion tracking)

**Total Commits:** 6 (one per major task + final verification)
