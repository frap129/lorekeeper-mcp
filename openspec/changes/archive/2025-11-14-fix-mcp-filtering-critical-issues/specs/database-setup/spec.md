# database-setup Specification

## Purpose
Define database schema enhancements and index requirements to support efficient case-insensitive and enhanced search capabilities for all MCP tools.

## Requirements

## ADDED Requirements

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

---

### Requirement: Essential Case-Insensitive Indexes Only
The system SHALL create only essential case-insensitive indexes to support the new query patterns.

**Essential Indexes Only:**
- `LOWER(name)` indexes for all entity tables
- No composite indexes unless proven necessary through performance testing

#### Scenario: Create only necessary case-insensitive indexes
**Given** performance testing with real query patterns
**When** measuring query execution times
**Then** only create indexes that provide measurable performance benefits
**And** avoid unnecessary index maintenance overhead
**And** focus on essential `LOWER(name)` indexes for case-insensitive queries

#### Scenario: Validate index necessity
**Given** the database is in production use
**When** analyzing query performance with `EXPLAIN QUERY PLAN`
**Then** ensure all case-insensitive queries use the created indexes
**And** verify no full table scans occur for indexed searches
**And** confirm composite indexes are not needed for current query patterns

---

### Requirement: Optional Performance Index Creation
The system SHALL support optional performance index creation for case-insensitive queries without affecting existing functionality.

#### Scenario: Database migration for new indexes
**Given** an existing database without case-insensitive indexes
**When** running the database migration
**Then** the system adds all required case-insensitive indexes
**And** migration is idempotent (can run multiple times safely)
**And** existing data and functionality remain intact
**And** migration completes within reasonable time for large datasets

#### Scenario: Performance index monitoring
**Given** adding case-insensitive performance indexes to large databases
**When** creating the optional indexes
**Then** the system provides progress feedback for index creation
**And** handles index creation timeouts gracefully
**And** continues normal operation even if index creation fails
**And** provides retry mechanisms for failed index creation

#### Scenario: Performance index verification
**Given** the optional performance indexes have been created
**When** verifying the index creation success
**Then** all new performance indexes exist and are usable
**And** `EXPLAIN QUERY PLAN` shows index usage for `LOWER(name)` queries
**And** performance tests confirm improved query times
**And** no regression in existing functionality

---

### Requirement: Database Statistics and Optimization
The system SHALL maintain database statistics and run periodic optimization to ensure optimal query performance.

#### Scenario: Database statistics collection
**Given** the database is in regular use
**When** data is inserted, updated, or deleted
**Then** the system runs `ANALYZE` command to update statistics
**And** query planner has accurate information for optimal query plans
**And** performance remains consistent as data grows

#### Scenario: Periodic database optimization
**Given** the database has been in use for extended periods
**When** performing maintenance operations
**Then** the system runs `VACUUM` to optimize database file
**And** reorganizes indexes for optimal performance
**And** cleans up unused space and fragmented data
**And** maintains optimal query performance over time

#### Scenario: Performance monitoring
**Given** the database is serving production queries
**When** monitoring query performance
**Then** the system tracks query execution times
**And** identifies slow queries that need optimization
**And** ensures indexes are being used effectively
**And** alerts on performance degradation

---

### Requirement: Transaction Safety and Consistency
The system SHALL ensure all database operations maintain data consistency and support proper transaction handling.

#### Scenario: Index creation within transactions
**Given** database schema modifications are needed
**When** creating new indexes
**Then** all index operations are wrapped in transactions
**And** partial index creation is rolled back on failure
**And** database remains consistent even if operations fail
**And** no orphaned or incomplete indexes remain

#### Scenario: Concurrent access during migrations
**Given** the database is being updated while serving queries
**When** schema changes occur
**Then** read operations continue to work during index creation
**And** write operations are properly handled
**And** database remains available throughout the migration
**And** isolation levels prevent interference between operations

---

### Requirement: Gradual Migration Safety
The system SHALL support gradual migration of tools from client-side to database filtering with feature flags.

#### Scenario: Feature flag for creature tool migration
**Given** the enhanced database layer is implemented
**When** migrating `lookup_creature` tool
**Then** the system supports a feature flag to enable/disable enhanced filtering
**And** can revert to client-side filtering if issues occur
**And** maintains backward compatibility during transition

---

### Requirement: Backup and Recovery Compatibility
The system SHALL ensure database enhancements are compatible with existing backup and recovery procedures.

#### Scenario: Backup with enhanced indexes
**Given** regular database backups are performed
**When** backing up the enhanced database
**Then** all new indexes are included in the backup
**And** backup file contains complete schema definition
**And** restore operation recreates all indexes correctly
**And** no data or functionality is lost in backup/restore cycle

#### Scenario: Recovery testing
**Given** database recovery procedures are tested
**When** restoring from backup
**Then** all enhanced indexes are properly restored
**And** query performance after restore matches pre-backup performance
**And** all filtering capabilities work correctly after restore
**And** database integrity is maintained through recovery process
