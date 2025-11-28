## Context

The LoreKeeper MCP server aggregates D&D 5e data from multiple sources:
1. **Open5e API v2** - Primary source, returns JSON with nested objects
2. **Open5e API v1** - Legacy endpoints, simpler flat structures
3. **OrcBrew files** - EDN format from OrcPub/DungeonMastersVault

Currently, data flows through:
```
API/OrcBrew → Pydantic Models (API only) → Cache (dict) → Repository → Tool
```

The problem is OrcBrew bypasses validation and field naming varies by source.

## Goals / Non-Goals

**Goals:**
- Single source of truth for field names and types across all entity types
- Pydantic validation for ALL data sources (API and OrcBrew)
- Clear separation between external formats and internal representation
- Backward-compatible migration (no breaking API changes)

**Non-Goals:**
- Changing external API contracts
- Full schema migration (cache schema stays compatible)
- Supporting additional data sources beyond current three
- Performance optimization (current performance is acceptable)

## Decisions

### Decision 1: Create `models/` package at top level

**Choice:** New `src/lorekeeper_mcp/models/` package separate from `api_clients/models/`

**Rationale:**
- Canonical models are not API-specific; they represent our internal truth
- Allows `api_clients/` to remain focused on HTTP concerns
- Clear import path: `from lorekeeper_mcp.models import Creature, Spell`

**Alternatives considered:**
- Keep models in `api_clients/models/` → Confusing ownership, OrcBrew isn't an API client
- Create `canonical/` package → Too abstract, "models" is clearer

### Decision 2: Rename Monster → Creature

**Choice:** Rename `Monster` class to `Creature` throughout

**Rationale:**
- Aligns with Open5e v2 API terminology (`/creatures/` endpoint)
- More inclusive term (encompasses NPCs, animals, etc.)
- Modern D&D usage prefers "creature"

**Migration:**
- Create `Monster = Creature` alias for backward compatibility in imports
- Deprecation warning on `Monster` usage
- Remove alias after one release cycle

### Decision 3: Shared base validators via mixins

**Choice:** Use Pydantic `model_validator` mixins for common transformations

**Rationale:**
- Slug/key normalization needed on ALL models
- Description field mapping common across sources
- DRY principle - one place to fix bugs

**Implementation:**
```python
class SlugNormalizerMixin:
    @model_validator(mode="before")
    def normalize_slug(cls, data):
        if isinstance(data, dict) and "key" in data and "slug" not in data:
            data["slug"] = data["key"]
        return data
```

### Decision 4: OrcBrew models as subset of canonical

**Choice:** OrcBrew models inherit from canonical with relaxed constraints

**Rationale:**
- OrcBrew data is often incomplete (missing `casting_time`, `range`, etc.)
- Can't require all fields that API provides
- Still get type validation on present fields

**Implementation:**
```python
class OrcBrewSpell(Spell):
    # Override required fields to optional
    casting_time: str | None = None
    range: str | None = None
    duration: str | None = None
```

### Decision 5: Keep equipment models simple

**Choice:** Simplify `DamageType` and `WeaponProperty` to strings with optional expansion

**Rationale:**
- Current nested objects rarely accessed beyond `.name`
- Simpler storage and querying
- Add computed properties for backward compatibility

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Breaking existing tests | Create comprehensive test migration guide; run full test suite after each phase |
| Import path changes break tools | Use `__init__.py` re-exports for common patterns |
| OrcBrew validation too strict | Make OrcBrew models permissive with optional fields |
| Performance regression | Profile before/after; Pydantic v2 is fast enough |

## Migration Plan

**Phase 1 (Low risk):**
1. Create `models/` package with copies of current models
2. Update imports in new code only
3. Add `Monster = Creature` alias

**Phase 2 (Medium risk):**
1. Add OrcBrew validation models
2. Update `entity_mapper.py` to use them
3. Run full test suite

**Phase 3 (Medium risk):**
1. Simplify equipment models
2. Add computed properties
3. Update cache extraction logic

**Phase 4 (Low risk):**
1. Remove `api_clients/models/` (keep re-exports)
2. Remove `Monster` alias (after deprecation period)
3. Update all documentation

**Rollback:** Each phase is independent; can revert by restoring previous imports.

## Open Questions

1. **Deprecation timeline:** How long to keep `Monster` alias? (Suggested: 1 release cycle)
2. **OrcBrew field mapping:** Should we try to infer missing fields from context? (Suggested: No, use explicit defaults)
3. **Cache migration:** Should we migrate existing cached data? (Suggested: No, let it refresh naturally)
