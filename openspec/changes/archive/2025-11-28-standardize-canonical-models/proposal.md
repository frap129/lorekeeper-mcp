## Why

The codebase lacks a true canonical data representation. API responses, OrcBrew entities, and cached data use inconsistent field naming (`key` vs `slug`, `challenge` vs `challenge_rating`, `description` vs `desc`), different type representations (nested objects vs strings), and missing validation for OrcBrew imports. This causes:

1. Transformation logic scattered across API clients, parsers, and repositories
2. OrcBrew data bypassing Pydantic validation entirely
3. Field name mismatches requiring ad-hoc handling at multiple layers
4. "Monster" naming inconsistent with Open5e v2's "Creature" terminology

## What Changes

### Phase 1: Core Model Standardization
- Create `src/lorekeeper_mcp/models/` package for canonical models
- Rename `Monster` model to `Creature` throughout codebase
- Add shared slug/key normalization validator to all models
- Standardize description field mapping (`description` → `desc`)
- Repositories MUST accept and return only canonical Pydantic models (not dicts)

### Phase 2: OrcBrew Validation
- Add OrcBrew-specific Pydantic models in `models/orcbrew/`
- Validate OrcBrew entities through Pydantic before caching
- Expand `entity_mapper.py` to capture all fields (not just indexed ones)

### Phase 3: Simplified Equipment Models
- Simplify `DamageType` to store string with optional object for API compatibility
- Add `damage_type_name` computed property on `Weapon`
- Flatten `WeaponProperty` structure for simpler storage

### Phase 4: Field Normalization
- Standardize challenge rating handling: `challenge`, `challenge_rating`, `challenge_rating_text` → `challenge_rating` (str) + `challenge_rating_decimal` (float)
- Add sensible defaults for missing OrcBrew fields

## Impact

- **Affected specs**:
  - `orcbrew-parser` (MODIFIED: validation requirements)
  - `entity-cache` (MODIFIED: document/model storage)
  - NEW: `canonical-models` spec

- **Affected code**:
  - `src/lorekeeper_mcp/api_clients/models/` → Move to `src/lorekeeper_mcp/models/`
  - `src/lorekeeper_mcp/parsers/entity_mapper.py` → Use canonical models
  - `src/lorekeeper_mcp/api_clients/open5e_v1.py` → Use `Creature` not `Monster`
  - `src/lorekeeper_mcp/api_clients/open5e_v2.py` → Use `Creature` not `Monster`
  - `src/lorekeeper_mcp/repositories/` → Update to accept/return canonical models only (not dicts)
  - `src/lorekeeper_mcp/tools/` → Update imports
  - All tests referencing `Monster` class

- **Breaking changes**: None for external API; internal model location changes
