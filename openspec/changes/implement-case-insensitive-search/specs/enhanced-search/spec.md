## MODIFIED Requirements

### Requirement: Enhanced Case-Insensitive Default Behavior
The system SHALL change all name filtering from case-sensitive to case-insensitive by default.

**Implementation:**
- Replace `name = ?` with `LOWER(name) = LOWER(?)` SQL queries
- Maintain existing `name` parameter interface unchanged
- Ensure all tools inherit this enhancement automatically
- Repository layer SHALL use case-insensitive filter operator when querying cache

#### Scenario: Case-insensitive default across all tools
**Given** a user searches with `name="fireball"` (any case combination)
**When** any lookup tool is invoked
**Then** the repository uses case-insensitive matching operator
**And** the cache layer generates `LOWER(name) = LOWER(?)` SQL
**And** provides consistent behavior across all 5 tools

#### Scenario: Enhanced creature lookup with case-insensitivity
**Given** a user searches for `name="ancient red dragon"` (any case)
**When** the `lookup_creature` tool is invoked
**Then** the system returns Ancient Red Dragon data
**And** performs filtering at database level
**And** eliminates the 11x over-fetching performance bug

#### Scenario: Perfect backward compatibility
**Given** existing code uses `name="Fireball"` (proper case)
**When** any lookup tool is invoked
**Then** the system returns identical results as before
**And** adds case-insensitive capability without breaking changes
**And** maintains exact same parameter interface

---

### Requirement: Automatic Slug Fallback Implementation
The system SHALL implement transparent slug fallback when name search returns no results.

**Implementation:**
- First attempt enhanced case-insensitive name search
- If no results, automatically try exact slug match using same input value
- Fallback occurs transparently without user interaction or parameter changes
- Repository layer SHALL handle fallback logic before returning empty results

#### Scenario: Transparent slug fallback for spells
**Given** a user searches with `name="fireball"` and no name match exists
**When** the `lookup_spell` tool is invoked
**Then** the repository automatically tries `slug = "fireball"` as fallback
**And** returns spell data using efficient PRIMARY KEY lookup
**And** provides this fallback behavior invisibly to users

#### Scenario: Equipment search with slug fallback
**Given** a user searches with `name="wand of magic missiles"` (exact slug)
**When** the `lookup_equipment` tool is invoked
**Then** name search fails, repository performs automatic slug search
**And** returns equipment item using slug PRIMARY KEY
**And** maintains single-parameter interface

#### Scenario: Performance optimization via fallback
**Given** slug search provides better performance than name search
**When** automatic fallback triggers for exact slug matches
**Then** system leverages PRIMARY KEY index for optimal query performance
**And** reduces query time compared to case-insensitive name matching

---

### Requirement: Wildcard-Based Partial Name Matching
The system SHALL support partial matching when the `name` parameter contains explicit wildcard characters.

**Implementation:**
- Detect `*` or `%` characters in the `name` parameter value
- Convert to `LOWER(name) LIKE LOWER(?)` SQL queries with processed wildcards
- Only perform partial matching when explicitly requested via wildcards
- Repository layer SHALL detect wildcards and use LIKE operator in cache queries

#### Scenario: Explicit wildcard partial matching
**Given** a user searches for `name="fire*"` or `name="%fire"`
**When** any lookup tool is invoked
**Then** the repository detects wildcard characters in the parameter
**And** passes LIKE operator to cache layer
**And** returns partial matches like "Fireball", "Fire Bolt", "Wall of Fire"

#### Scenario: Equipment partial search with wildcards
**Given** a user searches for `name="*sword*"` with `limit=5`
**When** the `lookup_equipment` tool is invoked
**Then** the repository processes wildcards for partial matching
**And** returns up to 5 equipment items containing "sword"
**And** performs all filtering at database level

#### Scenario: No wildcard means exact matching
**Given** a user searches for `name="Fireball"` (no wildcards)
**When** the `lookup_spell` tool is invoked
**Then** the system performs case-insensitive exact matching only
**And** returns only "Fireball" spell if found
**And** does not perform partial matching unless wildcards present
