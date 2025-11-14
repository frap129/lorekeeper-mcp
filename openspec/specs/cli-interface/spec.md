# cli-interface Specification

## Purpose
TBD - created by archiving change import-orcbrew-data. Update Purpose after archive.
## Requirements
### Requirement: CLI Entry Point
The system SHALL provide a command-line interface accessible via `lorekeeper` command or `python -m lorekeeper_mcp.cli`.

#### Scenario: User invokes CLI help
**Given** the lorekeeper package is installed
**When** the user runs `lorekeeper --help`
**Then** the CLI displays available commands and global options

#### Scenario: User invokes CLI version
**Given** the lorekeeper package is installed
**When** the user runs `lorekeeper --version`
**Then** the CLI displays the current version number

---

### Requirement: Import Command
The CLI SHALL provide an `import` command that accepts .orcbrew file paths and imports their content into the cache.

#### Scenario: User imports a valid .orcbrew file
**Given** a valid .orcbrew file at `./data.orcbrew`
**And** the database is initialized
**When** the user runs `lorekeeper import ./data.orcbrew`
**Then** the CLI parses the file
**And** imports all supported entities into the cache
**And** displays a success summary with entity counts

#### Scenario: User imports with non-existent file
**Given** no file exists at `./missing.orcbrew`
**When** the user runs `lorekeeper import ./missing.orcbrew`
**Then** the CLI displays an error message "File not found: ./missing.orcbrew"
**And** exits with status code 1

#### Scenario: User imports with malformed EDN file
**Given** a file `./bad.orcbrew` with invalid EDN syntax
**When** the user runs `lorekeeper import ./bad.orcbrew`
**Then** the CLI displays an error message "Failed to parse EDN file"
**And** exits with status code 1

---

### Requirement: Global Options
The CLI SHALL support global options that apply to all commands.

#### Scenario: User specifies custom database path
**Given** the user wants to use a custom database
**When** the user runs `lorekeeper --db-path ./custom.db import data.orcbrew`
**Then** the CLI uses `./custom.db` for all database operations

#### Scenario: User enables verbose logging
**Given** the user wants detailed progress information
**When** the user runs `lorekeeper -v import data.orcbrew`
**Then** the CLI displays detailed logging output including parse progress and entity details

---

### Requirement: Import Options
The `import` command SHALL support options to control import behavior.

#### Scenario: User performs dry-run import
**Given** a valid .orcbrew file
**When** the user runs `lorekeeper import --dry-run data.orcbrew`
**Then** the CLI parses the file and displays what would be imported
**And** does not write any data to the cache
**And** displays "Dry run complete. No data was imported."

#### Scenario: User forces overwrite of existing data
**Given** entities already exist in the cache
**When** the user runs `lorekeeper import --force data.orcbrew`
**Then** the CLI overwrites existing entities with matching slugs
**And** logs the number of entities overwritten

---

### Requirement: Progress Reporting
The CLI SHALL display progress information during long-running import operations.

#### Scenario: User imports large file
**Given** a .orcbrew file with 1000+ entities
**When** the user runs `lorekeeper import largefile.orcbrew`
**Then** the CLI displays progress updates showing:
- Current entity type being imported
- Number of entities processed
- Number of entities skipped
- Estimated time remaining (optional)

#### Scenario: User imports with verbose mode
**Given** verbose mode is enabled
**When** the import processes entities
**Then** the CLI logs each entity being processed with its slug and name

---

### Requirement: Error Handling and User Feedback
The CLI SHALL provide clear, actionable error messages and exit codes.

#### Scenario: Database initialization fails
**Given** the database path is in a read-only directory
**When** the user runs `lorekeeper import data.orcbrew`
**Then** the CLI displays "Database initialization failed: Permission denied"
**And** exits with status code 2

#### Scenario: Partial import success
**Given** a .orcbrew file with some malformed entities
**When** the import completes
**Then** the CLI displays:
- Total entities processed
- Number successfully imported
- Number skipped with reasons
- Warning message about skipped entities

---

### Requirement: Framework Implementation
The CLI SHALL be implemented using the Click framework following Python CLI best practices.

#### Scenario: CLI follows Click conventions
**Given** the CLI is implemented with Click
**Then** the CLI supports:
- Automatic help generation
- Option validation
- Environment variable configuration (LOREKEEPER_DB_PATH)
- Shell completion (if enabled)
