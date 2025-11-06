# base-client Specification

## Purpose
TBD - created by archiving change build-api-clients. Update Purpose after archive.
## Requirements
### Requirement: HTTP Client Configuration
The system SHALL provide configurable HTTP client settings for different use cases and environments while maintaining sensible defaults.

#### Scenario: Configurable client settings
When creating API clients, the system must support configurable settings including timeouts, retry limits, and rate limits while providing sensible defaults.

**Acceptance Criteria:**
- Configurable base URLs for different API services (Open5e v1, v2, D&D 5e API)
- Configurable timeouts (default: 30s), retry limits (default: 5), and rate limits
- Environment-specific configuration support via environment variables or config files
- Default user agent header identifying LoreKeeper MCP client
- Support for custom headers per request or client instance
