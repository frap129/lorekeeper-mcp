## Why

The OrcBrew parser fails to import 834 entities from the MegaPak file due to incomplete validation logic in OrcBrew-specific Pydantic models. The canonical models have normalization logic that was not copied to the OrcBrew relaxed models, causing validation failures for legitimate OrcBrew data structures.

## What Changes

- Add dict-to-string conversion for spell components in `OrcBrewSpell` model (handles `{'verbal': True, 'somatic': True}` format)
- Add dict-to-int conversion for creature hit_points in `OrcBrewCreature` model (handles `{'die': 8, 'die-count': 10, 'modifier': 20}` format)
- Allow string format for creature speed in `OrcBrewCreature` model (e.g., `"30 ft."`)
- Allow single dict metadata for creature actions and legendary_actions (handles metadata dicts describing action economy)

## Impact

- Affected specs: `canonical-models`
- Affected code:
  - `src/lorekeeper_mcp/models/orcbrew/spell.py` - Add components dict handling to validator
  - `src/lorekeeper_mcp/models/orcbrew/creature.py` - Add hit_points dict handling to validator, update speed and actions type annotations
- Successfully imports ~830+ additional entities from OrcBrew files
- No breaking changes - only makes validators more permissive
