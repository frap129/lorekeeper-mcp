# enhanced-search Specification

## Purpose
TBD - created by archiving change fix-mcp-filtering-critical-issues. Update Purpose after archive.
## Requirements
### Requirement: Enhanced Case-Insensitive Name Filtering
The system SHALL enhance the existing `name` parameter to use case-insensitive matching by default.

#### Scenario: Case-insensitive name search
**Given** a user searches with `name="fireball"`
**When** any lookup tool is invoked
**Then** the system uses `LOWER(name) = LOWER(?)` SQL query
**And** returns "Fireball" spell data regardless of input case

---

### Requirement: Automatic Slug Fallback
The system SHALL automatically attempt slug field search when name search returns no results.

#### Scenario: Automatic slug fallback
**Given** a user searches with `name="fireball"`
**When** the `lookup_spell` tool is invoked and no name match exists
**Then** the system automatically tries `slug = "fireball"`
**And** returns the spell if slug matches
**And** provides fallback behavior transparently to users

---

### Requirement: Wildcard Partial Matching
The system SHALL support partial matching when the `name` parameter contains wildcard characters.

#### Scenario: Explicit wildcard matching
**Given** a user searches with `name="fire*"` or `name="%fire"`
**When** any lookup tool is invoked
**Then** the system detects wildcards in the name parameter
**And** uses `LOWER(name) LIKE LOWER(?)` with processed wildcards
**And** returns partial matches containing "fire"

---

### Requirement: Enhanced Case-Insensitive Default Behavior
The system SHALL change all name filtering from case-sensitive to case-insensitive by default.

**Implementation:**
- Replace `name = ?` with `LOWER(name) = LOWER(?)` SQL queries
- Maintain existing `name` parameter interface unchanged
- Ensure all tools inherit this enhancement automatically

#### Scenario: Case-insensitive default across all tools
**Given** a user searches with `name="fireball"` (any case combination)
**When** any lookup tool is invoked
**Then** the system finds matches regardless of input case
**And** uses efficient case-insensitive SQL queries
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

#### Scenario: Transparent slug fallback for spells
**Given** a user searches with `name="fireball"` and no name match exists
**When** the `lookup_spell` tool is invoked
**Then** the system automatically tries `slug = "fireball"` as fallback
**And** returns spell data using efficient PRIMARY KEY lookup
**And** provides this fallback behavior invisibly to users

#### Scenario: Equipment search with slug fallback
**Given** a user searches with `name="wand of magic missiles"` (exact slug)
**When** the `lookup_equipment` tool is invoked
**Then** name search fails, automatic slug search succeeds
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

#### Scenario: Explicit wildcard partial matching
**Given** a user searches for `name="fire*"` or `name="%fire"`
**When** any lookup tool is invoked
**Then** the system detects wildcard characters in the parameter
**And** returns partial matches like "Fireball", "Fire Bolt", "Wall of Fire"
**And** uses efficient `LOWER(name) LIKE LOWER(?)` database queries
**And** respects the `limit` parameter

#### Scenario: Equipment partial search with wildcards
**Given** a user searches for `name="*sword*"` with `limit=5`
**When** the `lookup_equipment` tool is invoked
**Then** the system processes wildcards for partial matching
**And** returns up to 5 equipment items containing "sword"
**And** includes "Longsword", "Shortsword", "Greatsword", "Flame Tongue", "Frost Brand"
**And** performs all filtering at database level

#### Scenario: No wildcard means exact matching
**Given** a user searches for `name="Fireball"` (no wildcards)
**When** the `lookup_spell` tool is invoked
**Then** the system performs case-insensitive exact matching only
**And** returns only "Fireball" spell if found
**And** does not perform partial matching unless wildcards present

#### Scenario: Wildcard search with no results
**Given** a user searches for `name="xyz123*"`
**When** any lookup tool is invoked
**Then** the system performs partial match query efficiently
**And** returns empty result list without error
**And** query executes with proper indexing

---

### Requirement: Database-Level Filtering Performance
The system SHALL perform all filtering operations at the database level to eliminate client-side filtering and reduce data transfer.

**Implementation:**
- Remove all client-side filtering from affected tools
- Ensure database queries include all filter criteria
- Optimize SQL queries with proper indexes

#### Scenario: Efficient creature filtering
**Given** a user searches `lookup_creature(name="dragon", cr=10, limit=20)`
**When** the tool is invoked
**Then** the system builds a single SQL query with all WHERE conditions
**And** the database returns exactly matching results (not 220 items)
**And** memory usage is proportional to actual results (20 items max)
**And** network transfer is minimized

#### Scenario: Equipment search with multiple filters
**Given** a user searches `lookup_equipment(type="weapon", name="sword", limit=15)`
**When** the tool is invoked
**Then** the system performs filtering at database level
**And** does not fetch all weapons then filter client-side
**And** query performance uses indexes effectively
**And** response time is under 100ms for typical queries

#### Scenario: Performance comparison validation
**Given** the enhanced filtering is implemented
**When** comparing before/after performance metrics
**Then** database queries return exactly `limit` results (not `limit * 11`)
**And** memory usage reduction is 90% or more for filtered queries
**And** query execution time improves by factor of 5 or more
**And** client CPU usage for filtering is eliminated

---

### Requirement: Consistent Enhanced Tool Interface
The system SHALL provide consistent enhanced search behavior across all MCP tools using unchanged existing parameters.

**Implementation:**
- All tools maintain exact existing parameter interface: `name`, `limit`, plus tool-specific filters
- The existing `name` parameter is enhanced with case-insensitive, wildcard, and slug fallback behavior
- Tools preserve their specific parameters (e.g., `level` for spells, `cr` for creatures)
- Enhanced behavior applies automatically without parameter changes

#### Scenario: Identical interface across all tools
**Given** examining the parameter definitions for all 5 tools
**When** checking tool interfaces
**Then** all tools have exactly the same parameters as before
**And** each tool maintains its domain-specific parameters unchanged
**And** parameter types and defaults remain identical
**And** FastMCP parameter validation works as before

#### Scenario: Enhanced behavior with existing parameters
**Given** a user searches `lookup_spell(name="fire", level=3, school="evocation")`
**When** the spell tool is invoked
**Then** the system uses enhanced case-insensitive matching for "fire"
**And** combines with spell-specific filters (level=3, school="evocation")
**And** performs efficient database query with all conditions
**And** respects the `limit` parameter without over-fetching

#### Scenario: Unchanged parameter validation
**Given** invalid parameters provided to any tool
**When** the tool is invoked
**Then** FastMCP validation behaves exactly as before
**And** error messages remain consistent and user-friendly
**And** error handling follows the same pattern for all tools
**And** no new validation rules are introduced

---

### Requirement: Perfect Backward Compatibility
The system SHALL maintain 100% backward compatibility with all existing tool parameters and behavior.

**Implementation:**
- All existing parameters work exactly as before
- All existing parameter types and defaults remain unchanged
- Enhanced behavior is transparent and automatic
- No existing integrations require changes

#### Scenario: Identical behavior for existing calls
**Given** existing code uses `lookup_spell(name="Fireball", level=3)`
**When** the tool is invoked
**Then** the system returns exactly the same results as before
**And** adds case-insensitive capability transparently
**And** maintains exact same parameter interface
**And** performs filtering efficiently at database level

#### Scenario: Unchanged limit parameter behavior
**Given** existing code uses `lookup_creature(limit=20)` without name filters
**When** the tool is invoked
**Then** the system returns exactly 20 creatures as expected
**And** maintains the same ordering behavior
**And** performance is improved without changing results
**And** response format remains identical

#### Scenario: Enhanced capability with existing parameters
**Given** a user searches `lookup_spell(name="fire", level=3, school="evocation", limit=10)`
**When** the tool is invoked
**Then** the system uses enhanced case-insensitive matching for "fire"
**And** combines with spell-specific filters (level=3, school="evocation)
**And** performs efficient database query with all conditions
**And** respects the limit parameter without the 11x over-fetching bug

#### Scenario: Zero impact on existing integrations
**Given** existing client code or MCP clients
**When** using current tool interfaces
**Then** all existing functionality works unchanged
**And** no API or interface changes are required
**And** enhanced features work automatically without awareness

---

### Requirement: SQL Security and Parameter Binding
The system SHALL use proper SQL parameter binding for all user input to prevent SQL injection attacks.

**Implementation:**
- All user input uses parameterized queries with `?` placeholders
- No string concatenation of user input in SQL queries
- Input validation and sanitization for special characters

#### Scenario: Safe parameter binding for names
**Given** a user searches for `name="Robert'; DROP TABLE spells; --"`
**When** any lookup tool is invoked
**Then** the system uses parameterized query `LOWER(name) = LOWER(?)`
**And** the malicious input is treated as a literal string value
**And** no SQL injection is possible
**And** query executes safely with no matches found

#### Scenario: Safe LIKE query handling
**Given** a user searches for `name="%; DROP TABLE creatures; --"`
**When** any lookup tool is invoked
**Then** the system safely escapes LIKE wildcards
**And** uses parameter binding `LOWER(name) LIKE LOWER(?)`
**And** SQL injection is prevented
**And** query executes safely

#### Scenario: Input validation and sanitization
**Given** extremely long input strings or special characters
**When** any lookup tool is invoked
**Then** the system validates input length limits
**And** escapes or rejects dangerous characters
**And** provides appropriate error messages for invalid input
**And** maintains database security while allowing valid searches
