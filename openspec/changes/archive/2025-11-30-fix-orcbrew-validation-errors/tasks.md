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
