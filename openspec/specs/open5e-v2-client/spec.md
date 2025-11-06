# open5e-v2-client Specification

## Purpose
TBD - created by archiving change build-api-clients. Update Purpose after archive.
## Requirements
### Requirement: Advanced Search Capabilities
The system SHALL provide advanced search capabilities that leverage Open5e v2's sophisticated filtering options while maintaining a simple interface.

#### Scenario: Multi-criteria spell search
When a user searches for spells with multiple criteria (e.g., 3rd level evocation wizard spells requiring concentration), the client must support combining multiple filters efficiently.

**Acceptance Criteria:**
- Supports multiple simultaneous filters (level + school + class + concentration + ritual)
- Handles complex search queries efficiently with query parameter combination
- Provides relevance ranking for partial name matches (fuzzy search)
- Supports exact match mode when name matches exactly
- Returns search metadata (total count from API, pagination next/previous URLs)

### Requirement: Response Data Normalization
The system SHALL normalize Open5e v2 API response data to match standardized response models used across all API clients.

#### Scenario: v2 response structure normalization
When Open5e v2 returns data with document metadata and nested references different from v1, the client must normalize to standardized Pydantic models for tool consistency.

**Acceptance Criteria:**
- Maps v2 document structure (document.name, document.key, document.publisher) to consistent format
- Handles new fields introduced in v2 (casting_options array, mastery properties for weapons)
- Normalizes nested object references (school.name, damage_type.name) to simple strings or structured objects
- Preserves enhanced v2 data (gamesystem, permalink, publisher) while maintaining compatibility
- Provides clear field mapping documentation for v1 vs v2 differences
