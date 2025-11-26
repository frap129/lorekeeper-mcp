## MODIFIED Requirements

### Requirement: Case-Insensitive Indexes
The system SHALL create case-insensitive indexes on the `name` field for all entity tables to support efficient case-insensitive queries.

**Tables to Index:**
- `spells`
- `creatures`
- `equipment`
- `character_options`
- `rules`

#### Scenario: Create case-insensitive spell index
**Given** the database initialization process
**When** creating the spells table indexes
**Then** the system executes `CREATE INDEX IF NOT EXISTS idx_spells_name_lower ON spells(LOWER(name))`
**And** the index supports efficient `LOWER(name) = LOWER(?)` queries
**And** query performance is sub-100ms for case-insensitive lookups

#### Scenario: Case-insensitive creature index creation
**Given** the database setup script runs
**When** indexing the creatures table
**Then** the system creates `idx_creatures_name_lower` index
**And** the index covers all creature records
**And** supports efficient case-insensitive creature searches

#### Scenario: Index verification
**Given** the database is initialized
**When** checking index existence
**Then** all required case-insensitive indexes exist
**And** `EXPLAIN QUERY PLAN` shows index usage for case-insensitive queries
**And** no full table scans occur for indexed searches

## ADDED Requirements

### Requirement: Cache Query Filter Operators
The system SHALL support multiple filter operators in cache queries beyond simple equality matching.

**Supported Operators:**
- `EQ` (default): Exact equality matching with `field = ?`
- `ILIKE`: Case-insensitive matching with `LOWER(field) = LOWER(?)`
- `LIKE`: Pattern matching with `field LIKE ?`
- `IN`: Multiple value matching with `field IN (...)`

#### Scenario: Case-insensitive name query
**Given** a cache with spell "Fireball" (capital F)
**When** querying with `name="fireball"` (lowercase) and operator `ILIKE`
**Then** the system generates SQL `LOWER(name) = LOWER(?)`
**And** returns the "Fireball" spell regardless of input case

#### Scenario: Wildcard pattern query
**Given** a cache with spells "Fireball", "Fire Bolt", "Wall of Fire"
**When** querying with `name="fire*"` and operator `LIKE`
**Then** the system converts `*` to `%` for SQL LIKE
**And** generates SQL `LOWER(name) LIKE LOWER(?)`
**And** returns all three fire-related spells

#### Scenario: Backward compatible default behavior
**Given** existing code using `query_cached_entities(entity_type, name="exact")`
**When** no operator is specified
**Then** the system defaults to exact equality (`EQ`) matching
**And** existing behavior is preserved
