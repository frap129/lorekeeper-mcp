## 1. Create Canonical Models Package

- [x] 1.1 Create `src/lorekeeper_mcp/models/` package directory
- [x] 1.2 Create `models/__init__.py` with public exports
- [x] 1.3 Create `models/base.py` with `BaseEntity` class and shared validators
- [x] 1.4 Add `SlugNormalizerMixin` for `key` → `slug` transformation
- [x] 1.5 Add `DescriptionNormalizerMixin` for `description` → `desc` transformation

## 2. Rename Monster to Creature

- [x] 2.1 Create `models/creature.py` with `Creature` class (copy from Monster)
- [x] 2.2 Add `Monster = Creature` alias with deprecation warning
- [x] 2.3 Update `api_clients/open5e_v1.py` imports to use `Creature`
- [x] 2.4 Update `api_clients/open5e_v2.py` imports to use `Creature`
- [x] 2.5 Update `repositories/monster.py` to use `Creature` and accept/return canonical models only
- [x] 2.6 Update `tools/creature_lookup.py` to use `Creature`
- [x] 2.7 Update all test files referencing `Monster`
- [x] 2.8 Run full test suite to verify no regressions

## 3. Migrate Spell Model

- [x] 3.1 Create `models/spell.py` with canonical `Spell` class
- [x] 3.2 Apply `SlugNormalizerMixin` and `DescriptionNormalizerMixin`
- [x] 3.3 Standardize `classes` field extraction (list of strings)
- [x] 3.4 Standardize `school` field (string, not object)
- [x] 3.5 Update imports in `api_clients/open5e_v2.py`
- [x] 3.6 Update imports in repositories and tools
- [x] 3.7 Verify spell tests pass

## 4. Migrate Equipment Models

- [x] 4.1 Create `models/weapon.py` with simplified `Weapon` class
- [x] 4.2 Add `damage_type_name` computed property
- [x] 4.3 Simplify `WeaponProperty` to string list with detail dict
- [x] 4.4 Create `models/armor.py` with `Armor` class
- [x] 4.5 Create `models/magic_item.py` with `MagicItem` class
- [x] 4.6 Update `api_clients/open5e_v2.py` to use new models
- [x] 4.7 Update equipment repository imports
- [x] 4.8 Verify equipment tests pass

## 5. Create OrcBrew Validation Models

- [x] 5.1 Create `models/orcbrew/` subpackage
- [x] 5.2 Create `models/orcbrew/spell.py` with relaxed `OrcBrewSpell`
- [x] 5.3 Create `models/orcbrew/creature.py` with relaxed `OrcBrewCreature`
- [x] 5.4 Create `models/orcbrew/equipment.py` with relaxed equipment models
- [x] 5.5 Update `entity_mapper.py` to validate through OrcBrew models
- [x] 5.6 Add comprehensive field extraction (not just indexed fields)
- [x] 5.7 Verify OrcBrew import tests pass

## 6. Standardize Challenge Rating

- [x] 6.1 Update `Creature` model to handle all CR variants
- [x] 6.2 Add `challenge_rating_from_orcbrew()` helper for `challenge` → `challenge_rating`
- [x] 6.3 Ensure `challenge_rating` is always string, `challenge_rating_decimal` always float
- [x] 6.4 Update entity mapper CR extraction
- [x] 6.5 Verify creature filtering works with standardized CR

## 7. Update Re-exports and Cleanup

- [x] 7.1 Update `api_clients/models/__init__.py` to re-export from `models/`
- [x] 7.2 Add deprecation warnings to `api_clients/models/` direct imports
- [x] 7.3 Update `api_clients/__init__.py` exports
- [x] 7.4 Update all documentation referencing model locations

## 8. Testing and Validation

- [x] 8.1 Run `just test` to verify all tests pass
- [x] 8.2 Run `just lint` to verify code quality
- [x] 8.3 Run `just type-check` to verify type hints
- [x] 8.4 Run live tests to verify end-to-end functionality
- [x] 8.5 Manual verification of OrcBrew import with sample file

## 9. Post-Review Follow-up Tasks

### 9.1 Add `to_canonical()` method to OrcBrew models

Per spec lines 151-155, OrcBrew models should provide a `to_canonical()` method to convert relaxed models to canonical models.

- [x] 9.1.1 Add `to_canonical()` method to `OrcBrewSpell` returning `Spell` instance
- [x] 9.1.2 Add `to_canonical()` method to `OrcBrewCreature` returning `Creature` instance
- [x] 9.1.3 Add `to_canonical()` method to `OrcBrewWeapon` returning `Weapon` instance
- [x] 9.1.4 Add `to_canonical()` method to `OrcBrewArmor` returning `Armor` instance
- [x] 9.1.5 Add `to_canonical()` method to `OrcBrewMagicItem` returning `MagicItem` instance
- [x] 9.1.6 Write unit tests for `to_canonical()` methods
- [x] 9.1.7 Run full test suite to verify no regressions

### 9.2 Investigate test_cross_tool_document_consistency failure

The `test_cross_tool_document_consistency` test fails due to a test logic issue unrelated to the model changes. The test populates a cache with spells in document "Adventurer's Guide" and monsters in document "mm", then queries expecting document filtering to work cross-tool.

- [x] 9.2.1 Analyze the test to understand the expected behavior
- [x] 9.2.2 Determine if this is a test logic issue or a document filtering implementation issue
- [x] 9.2.3 Fix the test or implementation as appropriate
- [x] 9.2.4 Verify the fix passes and doesn't break other tests

### 9.3 Review Monster deprecation warning stacklevel

The code review noted that `stacklevel=6` in the Monster deprecation warning may need adjustment depending on call context.

- [x] 9.3.1 Test the deprecation warning from various import contexts
- [x] 9.3.2 Adjust stacklevel if warning doesn't point to correct caller location
- [x] 9.3.3 Document the expected behavior in code comments
