# base-client Specification Changes

## ADDED Requirements

### Requirement: Parallel cache queries with API calls

The base HTTP client MUST query the entity cache in parallel with API requests to minimize latency and enable offline fallback.

#### Scenario: Parallel cache and API query

**Given** some entities are cached and others are not
**When** making an API request for multiple entities
**Then** cache query starts immediately in parallel with API request
**And** both operations complete concurrently
**And** results are merged with API taking precedence
**And** total latency is approximately max(cache_time, api_time), not cache_time + api_time

#### Scenario: Cache fills gaps in API response

**Given** an API request that times out after returning partial results
**And** remaining entities exist in cache
**When** the request completes with timeout error
**Then** cached entities are merged with partial API results
**And** user receives complete dataset from cache + API
**And** no error is raised for the partial timeout

### Requirement: Offline fallback using cache

The base HTTP client MUST fall back to cached entities when APIs are unreachable, providing graceful degradation.

#### Scenario: Network failure serves from cache

**Given** multiple entities cached locally
**When** an API request fails with NetworkError
**Then** the client catches the error
**And** returns all matching entities from cache
**And** logs a warning about offline mode
**And** does not raise an exception

#### Scenario: Offline with partial cache data

**Given** 5 out of 10 requested entities are cached
**When** API request fails due to network error
**Then** the 5 cached entities are returned
**And** response indicates partial data (via metadata or logging)
**And** user receives useful partial results instead of total failure

#### Scenario: Complete cache miss during offline

**Given** no relevant entities in cache
**When** API request fails with network error
**Then** an empty list is returned
**And** error is logged about offline mode with no cache
**And** appropriate exception is raised indicating no data available

### Requirement: Entity-based cache storage from responses

The base HTTP client MUST cache individual entities from API responses instead of caching entire URL responses.

#### Scenario: Cache entities from paginated API response

**Given** an API endpoint returns a paginated response with 20 spells
**When** the response is successfully received
**Then** each of the 20 spells is cached individually in the spells table
**And** the URL itself is NOT cached
**And** subsequent requests for any of those 20 spells hit cache

#### Scenario: Preserve entity metadata during caching

**Given** an API response with entities containing source_api metadata
**When** caching entities
**Then** each entity retains its source_api field
**And** created_at timestamp is set to current time for new entities
**And** updated_at is set to current time
**And** slug is extracted from entity for primary key

### Requirement: Cache-first query option for offline-preferred mode

The base HTTP client MUST support a cache-first mode where cache results are returned immediately while API refreshes asynchronously in the background.

#### Scenario: Return cached data immediately for faster UX

**Given** entities exist in cache
**When** making a request with `cache_first=True` flag
**Then** cached entities are returned immediately to caller
**And** API request starts in background to refresh cache
**And** user experiences instant response time

#### Scenario: Background API refresh updates cache

**Given** a cache-first request returned stale data
**When** background API request completes successfully
**Then** cache is updated with fresh data
**And** subsequent requests get the refreshed data
**And** original caller is not blocked on API response
