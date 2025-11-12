# filter-enhancement Specification

## Summary

Enhance filtering capabilities by implementing range operators, boolean filters, and multi-value filtering using existing API features, and optionally exposing these capabilities through backward-compatible tool parameters.

## Background

Both Open5e v2 and D&D 5e APIs support rich filtering beyond simple equality checks. Current implementation only uses exact matches, missing opportunities for range queries, boolean filters, and multi-value filtering that improve search precision and usability.

## Requirements

## ADDED Requirements

### Requirement: Implement range filtering operators

API clients SHALL utilize range filtering operators (`__gte`, `__lte`, `__gt`, `__lt`) for numeric fields where available.

**Rationale**: Open5e v2 supports range operators for numeric fields like level, challenge rating, cost, weight, armor class, ability scores, etc. These enable precise server-side range queries.

#### Scenario: Spell level range filtering
- **Given**: User searches for spells of levels 2-4
- **When**: Open5e v2 API request is made with level_min=2, level_max=4
- **Then**: Request includes `?level__gte=2&level__lte=4`
- **And**: API returns only spells within specified range
- **And**: No client-side filtering is needed

#### Scenario: Challenge rating range filtering
- **Given**: User searches for monsters with CR 1-3
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?challenge_rating_decimal__gte=1&challenge_rating_decimal__lte=3`
- **And**: API returns only monsters within CR range
- **And**: Filtering is performed server-side

#### Scenario: Cost and weight range filtering
- **Given**: User searches for equipment costing 10-100gp weighing under 5lbs
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?cost__gte=10&cost__lte=100&weight__lte=5`
- **And**: API returns only equipment matching all criteria
- **And**: Efficient server-side filtering

### Requirement: Implement boolean filtering

API clients SHALL utilize boolean filters for properties where available.

**Rationale**: Open5e v2 provides boolean filters for equipment and spell properties that enable precise filtering.

#### Scenario: Boolean equipment property filters
- **Given**: User searches for finesse, light weapons
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?is_finesse=true&is_light=true`
- **And**: API returns only weapons matching both properties
- **And**: Efficient server-side filtering replaces client-side logic

#### Scenario: Boolean spell property filters
- **Given**: User searches for concentration spells that are also rituals
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?concentration=true&ritual=true`
- **And**: API returns only spells matching both criteria

#### Scenario: Magic item filtering
- **Given**: User searches for magic items requiring attunement
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?is_magic_item=true&requires_attunement=true`
- **And**: API returns only attuned magic items

### Requirement: Implement multi-value filtering

API clients SHALL support array/multi-value parameters for filters accepting multiple values.

**Rationale**: Both APIs support filtering by multiple values efficiently in a single request.

#### Scenario: Multiple spell levels via D&D API
- **Given**: User searches for spells of levels 1, 2, and 3
- **When**: D&D 5e API request uses multi-value filter
- **Then**: Request includes `?level=1,2,3`
- **And**: API returns spells from all specified levels
- **And**: Single API call instead of three separate requests

#### Scenario: Multiple spell schools via Open5e
- **Given**: User searches for evocation and illusion spells
- **When**: Open5e v2 API request uses in operator
- **Then**: Request includes `?school__in=evocation,illusion` or `?school=evocation,illusion`
- **And**: API returns spells from both schools
- **And**: Results are efficiently filtered server-side

#### Scenario: Multiple creature types
- **Given**: User searches for dragon and undead creatures
- **When**: Open5e v2 API request is made
- **Then**: Request uses appropriate multi-value type filter
- **And**: API returns creatures matching any specified type

### Requirement: Implement entity-specific specialized filters

API clients SHALL implement entity-specific filters that provide more precise search capabilities.

**Rationale**: Different entity types have specialized filters (e.g., spell casting time, weapon damage type, creature ability scores) that enable precise searches.

#### Scenario: Specialized spell filtering
- **Given**: User searches for 1-action spells of level 3+ in evocation school with fire damage
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?casting_time=1 action&level__gte=3&school__key=evocation&damage_type=fire`
- **And**: API returns spells matching all criteria
- **And**: Results are precisely filtered server-side

#### Scenario: Specialized equipment filtering
- **Given**: User searches for rare magic weapons that are finesse and don't require attunement
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?is_magic_item=true&is_weapon=true&is_finesse=true&rarity=rare&requires_attunement=false`
- **And**: API returns only equipment matching all criteria

#### Scenario: Specialized creature filtering
- **Given**: User searches for large creatures with high strength (16+) and low intelligence (<10)
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?size=large&ability_score_strength__gte=16&ability_score_intelligence__lt=10`
- **And**: API returns creatures matching both criteria

## MODIFIED Requirements

### Modified Requirement: Tool filter parameter expansion (Optional Phase 3)

MCP tools MAY be enhanced with additional optional filtering parameters that map to API filter capabilities, maintaining backward compatibility.

**Rationale**: Current tools only support basic filters. Exposing more API capabilities through optional parameters improves usability without breaking existing code.

#### Scenario: Enhanced spell tool filtering (backward compatible)
- **Given**: Enhanced lookup_spell tool with new optional parameters
- **When**: User calls with level_min=2, level_max=4, concentration=true, damage_type="fire"
- **Then**: Tool translates to appropriate API filters
- **And**: Results are filtered server-side
- **And**: Existing code calling lookup_spell(level=3) still works unchanged

#### Scenario: Enhanced equipment tool filtering (backward compatible)
- **Given**: Enhanced lookup_equipment tool with new optional parameters
- **When**: User calls with cost_min=10, cost_max=100, is_finesse=true, weight_max=5
- **Then**: Tool translates to appropriate API filters
- **And**: Results are filtered server-side
- **And**: Existing code calling lookup_equipment(type="weapon") still works

### Modified Requirement: Repository filter mapping

Repository layer SHALL map high-level filter parameters to API-specific filter syntax for both exact and range queries.

**Rationale**: Repository acts as adapter, translating generic filter concepts to API-specific implementations.

#### Scenario: Repository translates range filters to Open5e
- **Given**: Repository receives `{level_min: 1, level_max: 3, school: "evocation"}`
- **When**: Search is performed with Open5e v2 client
- **Then**: Repository translates to `{level__gte: 1, level__lte: 3, school__key: "evocation"}`
- **And**: Translation is handled transparently

#### Scenario: Repository translates range to D&D API multi-value
- **Given**: Repository receives `{level_min: 1, level_max: 3}`
- **When**: Search is performed with D&D 5e client
- **Then**: Repository translates to `{level: "1,2,3"}`
- **And**: Range converted to comma-separated list for D&D API compatibility

## Implementation Notes

### Filter Operator Support by Entity Type

**Spells**:
- Range: `level__gte/lte`, `range__gte/lte`
- Boolean: `concentration`, `ritual`, `verbal`, `somatic`, `material`, `material_consumed`
- Multi-value: `school__in`, `level` (comma-separated)
- Specialized: `casting_time`, `damage_type`, `dc_type`, `duration`

**Creatures/Monsters**:
- Range: `challenge_rating_decimal__gte/lte`, `armor_class__gte/lte`, `ability_score_*__gte/lte`, `passive_perception__gte/lte`
- Multi-value: `size` (multiple sizes), `type` (multiple types)
- Boolean: `skill_bonus_*__isnull`, `saving_throw_*__isnull`
- Specialized: `size`, `category`, `subcategory`

**Equipment/Items**:
- Range: `cost__gte/lte`, `weight__gte/lte`, `ac_base__gte/lte`, `strength_score_required__gte/lte`
- Boolean: `is_magic_item`, `is_weapon`, `is_armor`, `is_light`, `is_versatile`, `is_thrown`, `is_finesse`, `is_two_handed`, `requires_attunement`, `grants_stealth_disadvantage`
- Multi-value: `rarity__in`
- Specialized: `damage_dice`, `category`

### Tool Parameter Expansion (Phase 3 - Optional)

**Enhanced lookup_spell** (all new parameters optional):
- `level_min`, `level_max` - spell level range
- `damage_type` - filter by damage type
- All existing parameters retained

**Enhanced lookup_creature** (all new parameters optional):
- `armor_class_min` - minimum AC
- `hit_points_min` - minimum HP
- `ability_scores` - filter by ability score thresholds
- All existing parameters retained

**Enhanced lookup_equipment** (all new parameters optional):
- `cost_min`, `cost_max` - price range
- `weight_max` - maximum weight
- `is_finesse`, `is_light`, `is_versatile`, `is_two_handed` - weapon properties
- `is_magic` - magic item filter
- All existing parameters retained

### Backward Compatibility

All enhancements are optional and backward compatible:
- Existing tool calls work unchanged
- New parameters are all optional with None defaults
- No breaking changes to signatures or return values
- Backend optimizations (filter operators) transparent to users

### Performance Impact

**Multi-Filter Example**:
- Before: Fetch all items (~1000), filter client-side for finesse+light+cost<50 to get 3 results
- After: Fetch 3 items with `?is_finesse=true&is_light=true&cost__lte=50`
- **Improvement**: 95%+ reduction in data transfer, 85% latency reduction
