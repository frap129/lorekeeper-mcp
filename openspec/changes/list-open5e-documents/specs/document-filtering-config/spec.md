# Document Filtering Configuration Specification

## Purpose
Enable users to configure which Open5e source documents are used by the server through configuration files and environment variables, with validation and startup logging.

## ADDED Requirements

### Requirement: Document Inclusion Configuration
The system SHALL support configuring a list of document keys to include via environment variables or configuration files.

#### Scenario:
When a user sets `INCLUDED_DOCUMENTS="srd-5e,tce,phb"` in their environment, the server should acknowledge this configuration at startup.

**Acceptance Criteria:**
- `Settings` class has `included_documents` field accepting comma-separated document keys
- Field accepts `None` (default, means all documents)
- Field accepts list of strings when loaded from environment
- Configuration is loaded from `.env` file or environment variables
- Document keys are trimmed and normalized (lowercase)
- Empty string treated as `None` (no filtering)
- Validation ensures keys are valid document identifiers (alphanumeric, hyphens, underscores)

### Requirement: Document Exclusion Configuration
The system SHALL support configuring a list of document keys to exclude via environment variables or configuration files.

#### Scenario:
When a user sets `EXCLUDED_DOCUMENTS="experimental,preview"` in their environment, the server should acknowledge this configuration at startup.

**Acceptance Criteria:**
- `Settings` class has `excluded_documents` field accepting comma-separated document keys
- Field accepts `None` (default, means no exclusions)
- Field accepts list of strings when loaded from environment
- Configuration is loaded from `.env` file or environment variables
- Document keys are trimmed and normalized (lowercase)
- Empty string treated as `None` (no exclusions)
- Validation ensures keys are valid document identifiers

### Requirement: Configuration Conflict Resolution
The system SHALL handle conflicts between inclusion and exclusion lists gracefully.

#### Scenario:
When both `INCLUDED_DOCUMENTS` and `EXCLUDED_DOCUMENTS` are set, the system should resolve the conflict with clear precedence rules.

**Acceptance Criteria:**
- If both are set, `included_documents` takes precedence
- Logs a warning when both are configured
- Warning message explains which configuration is being used
- Excluded list is ignored when included list is set
- No runtime errors occur from conflicting configuration

### Requirement: Server Startup Logging
The system SHALL log document configuration details during server startup.

#### Scenario:
When the server starts, it should clearly indicate which documents are configured for use.

**Acceptance Criteria:**
- Startup logs include document configuration summary
- Shows number of included documents (if configured)
- Shows number of excluded documents (if configured)
- Indicates if all documents are included (default)
- Log level is INFO for normal configuration
- Log level is WARNING for conflicts or invalid keys
- Example: `[INFO] Document filtering: Using 3 included documents (srd-5e, tce, phb)`
- Example: `[INFO] Document filtering: All documents included (no filters configured)`

### Requirement: Configuration Validation
The system SHALL validate document configuration and provide helpful error messages for invalid values.

#### Scenario:
When a user provides an invalid document key in configuration, the system should warn them but continue operating.

**Acceptance Criteria:**
- Invalid document keys logged as warnings at startup
- Warning includes the invalid key and suggestions
- Server continues to start despite invalid keys
- Valid keys in the list are still processed
- Validation does not require API call (format-only validation)
- Document keys must match pattern: `^[a-z0-9][a-z0-9-_]*$`

### Requirement: Environment Variable Parsing
The system SHALL correctly parse comma-separated document lists from environment variables.

#### Scenario:
When `INCLUDED_DOCUMENTS="srd-5e, tce , phb"` is set (with spaces), the system should parse it correctly.

**Acceptance Criteria:**
- Comma-separated values are split correctly
- Whitespace around keys is trimmed
- Empty entries are ignored
- Works with single document: `INCLUDED_DOCUMENTS="srd-5e"`
- Works with many documents: `INCLUDED_DOCUMENTS="a,b,c,d,e"`
- Handles trailing commas gracefully: `INCLUDED_DOCUMENTS="srd-5e,tce,"`

### Requirement: Configuration File Support
The system SHALL load document configuration from `.env` files using existing pydantic-settings integration.

#### Scenario:
When a `.env` file contains `INCLUDED_DOCUMENTS=srd-5e,tce`, the server should load this configuration automatically.

**Acceptance Criteria:**
- `.env` file in project root is loaded automatically
- Document configuration fields follow existing pattern
- Works alongside existing configuration fields (db_path, cache_ttl, etc.)
- Configuration precedence: CLI args > environment vars > .env file > defaults
- No breaking changes to existing configuration loading

### Requirement: Configuration Documentation
The system SHALL document document filtering configuration in `.env.example` and README.

#### Scenario:
When a new user examines the project, they should find clear examples of how to configure document filtering.

**Acceptance Criteria:**
- `.env.example` includes commented examples of `INCLUDED_DOCUMENTS`
- `.env.example` includes commented examples of `EXCLUDED_DOCUMENTS`
- Examples show common use cases (SRD-only, excluding specific content)
- Inline comments explain the purpose and format
- README or documentation mentions document filtering feature

### Requirement: Default Behavior
The system SHALL include all documents by default when no configuration is provided.

#### Scenario:
When a user starts the server without any document configuration, all available documents should be used.

**Acceptance Criteria:**
- Default `included_documents` is `None`
- Default `excluded_documents` is `None`
- `None` values mean "no filtering applied"
- Server logs indicate all documents are being used
- Behavior matches existing server behavior (backward compatible)

### Requirement: Configuration Access in Code
The system SHALL make document configuration accessible to API clients and repositories.

#### Scenario:
When the server needs to filter API results, it should have access to the document configuration.

**Acceptance Criteria:**
- Document configuration accessible via `settings.included_documents`
- Document configuration accessible via `settings.excluded_documents`
- Configuration is available globally through settings singleton
- Values are parsed into Python lists (not strings)
- Helper method exists to check if a document is enabled: `settings.is_document_enabled(key)`

**Note:** This requirement sets up the foundation for Phase 2 filtering but does not implement actual API result filtering in this change.
