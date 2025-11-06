# dnd5e-api-client Specification

## Purpose
TBD - created by archiving change build-api-clients. Update Purpose after archive.
## Requirements
### Requirement: API Version Handling
The system SHALL handle D&D 5e API version management transparently, including redirects and version compatibility.

#### Scenario: Versioned endpoint access
When accessing D&D 5e API endpoints that use versioned URLs (/api/2014/), the client must handle version prefixes and redirects transparently without user intervention.

**Acceptance Criteria:**
- Handles automatic redirects from `/api/` to `/api/2014/` using httpx follow_redirects
- Configurable API version parameter (default: "2014") with fallback to latest stable
- Maintains compatibility across API versions if new versions are released
- Provides version information in response metadata or logging
- Handles deprecated endpoints gracefully with clear error messages

### Requirement: Rules Data Integration
The system SHALL integrate D&D 5e API rules data seamlessly with the existing Open5e content ecosystem.

#### Scenario: Cross-API rule references
When D&D 5e API provides rules data (e.g., combat rules) that reference game mechanics also available in Open5e (e.g., conditions), the client must integrate seamlessly with normalized data models.

**Acceptance Criteria:**
- Normalizes rule data to match project Pydantic Rule models
- Cross-references rules with Open5e content where applicable (e.g., conditions)
- Provides consistent error handling across API boundaries (same exception types)
- Supports combined searches across multiple APIs in tool implementations
- Maintains source attribution for rule content (document__title, document__license_url equivalent)

### Requirement: Reference Data Caching Strategy
The system SHALL implement appropriate caching strategies for reference data that changes infrequently but is accessed often.

#### Scenario: Long-lived reference data cache
When accessing static reference data (damage types, skills, ability scores) that never changes, the client must use extended cache TTL to minimize API calls and enable offline capability.

**Acceptance Criteria:**
- Extended TTL for reference data (30 days = 2,592,000 seconds vs 7 days for dynamic content)
- Cache warming on first request for commonly accessed reference data (damage types, skills)
- Efficient cache invalidation using timestamp comparison for reference updates
- Offline capability for essential reference information (all reference data pre-cached)
- Cache size management to prevent unbounded growth (reference data is ~200 items total)
