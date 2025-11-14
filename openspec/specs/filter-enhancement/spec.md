# filter-enhancement Specification

## Purpose
TBD - created by archiving change enhance-search-capabilities. Update Purpose after archive.
## Requirements
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
