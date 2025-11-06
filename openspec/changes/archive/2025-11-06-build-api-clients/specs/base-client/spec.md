# Base HTTP Client Specification

## ADDED Requirements

### Requirement: Base HTTP Client Infrastructure
The system SHALL provide a base HTTP client class that offers common functionality for making HTTP requests to external APIs including request handling, retry logic, caching integration, and error handling.

#### Scenario:
When the LoreKeeper MCP server needs to make HTTP requests to external APIs, the base HTTP client must provide common functionality including request handling, retry logic, caching integration, and error handling.

**Acceptance Criteria:**
- Base client class `BaseHttpClient` exists with methods for making HTTP requests
- Implements exponential backoff retry logic for failed requests
- Integrates with SQLite cache for storing/retrieving responses
- Provides structured error handling with custom exception types
- Includes request/response logging for debugging
- Supports configurable timeouts and rate limiting

### Requirement: Cache Integration
The system SHALL integrate with SQLite cache to check for existing data before making network requests and store successful responses for future use.

#### Scenario:
When any API client makes a request, the base client should first check the cache for existing data before making network calls, and cache successful responses for future use.

**Acceptance Criteria:**
- `_get_cached_response()` method checks cache by URL/key
- `_cache_response()` method stores responses with TTL (7 days default)
- Cache integration is transparent to API client implementations
- Handles cache failures gracefully without breaking requests
- Supports cache invalidation and manual cache clearing

### Requirement: Error Handling and Retry Logic
The system SHALL implement retry logic with exponential backoff for failed network requests and provide meaningful error messages for different types of failures.

#### Scenario:
When network requests fail due to timeouts, rate limits, or server errors, the base client should implement appropriate retry strategies and provide meaningful error messages.

**Acceptance Criteria:**
- Implements exponential backoff with jitter for retries
- Distinguishes between retryable and non-retryable errors
- Rate limit detection and automatic backoff
- Custom exception hierarchy for different error types
- Structured logging with appropriate log levels
- Configurable retry limits and timeout values

### Requirement: Request/Response Interceptors
The system SHALL support request and response interceptors for common concerns like adding headers, logging requests, and transforming responses.

#### Scenario:
When making API requests, the base client should support interceptors for common concerns like adding headers, logging requests, and transforming responses.

**Acceptance Criteria:**
- Support for request interceptors (add headers, auth, logging)
- Support for response interceptors (logging, transformation)
- Configurable interceptor chains
- Default interceptors for common functionality
- Ability to add/remove interceptors per client instance

## ADDED Requirements

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
