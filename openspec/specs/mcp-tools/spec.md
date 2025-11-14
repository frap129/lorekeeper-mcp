# mcp-tools Specification

## Purpose
TBD - created by archiving change implement-mcp-tools. Update Purpose after archive.
## Requirements
### Requirement: Spell Lookup Tool
The system SHALL update the `lookup_spell` tool to use enhanced database-level filtering with existing parameters only.

**MODIFIED Implementation:**
- Enhance existing `name` parameter to use case-insensitive, wildcard, and automatic slug fallback matching
- Perform all filtering at database level (no client-side filtering)
- Maintain exact same parameter interface for backward compatibility

#### Scenario: Enhanced case-insensitive spell search
**Given** a user searches with `name="fireball"`
**When** the `lookup_spell` tool is invoked
**Then** the system performs case-insensitive database filtering
**And** returns "Fireball" spell data regardless of input case
**And** uses efficient `LOWER(name) = LOWER(?)` SQL query
**And** response time is under 100ms

#### Scenario: Wildcard partial spell name search
**Given** a user searches with `name="fire*"` or `name="%fire"`
**When** the `lookup_spell` tool is invoked
**Then** the system detects wildcards and performs database-level partial matching
**And** returns spells like "Fireball", "Fire Bolt", "Wall of Fire"
**And** uses `LOWER(name) LIKE LOWER(?)` SQL query with processed wildcards
**And** respects the `limit` parameter

#### Scenario: Automatic slug fallback for spells
**Given** a user searches with `name="fireball"` and no name match exists
**When** the `lookup_spell` tool is invoked
**Then** the system automatically tries slug search as fallback
**And** returns spell data if slug="fireball" exists
**And** provides this fallback transparently without parameter changes

#### Scenario: Enhanced combined spell filtering
**Given** a user searches with `name="fire*", level=3, school="evocation"`
**When** the `lookup_spell` tool is invoked
**Then** the system builds single SQL query with all conditions
**And** performs wildcard matching for "fire" with other filters
**And** returns only 3rd-level evocation spells containing "fire"
**And** respects the `limit` parameter without over-fetching

#### Scenario: Perfect backward compatibility preservation
**Given** existing code uses `lookup_spell(name="Fireball", level=3)`
**When** the tool is invoked
**Then** the system returns identical results as before
**And** adds enhanced case-insensitive capability transparently
**And** improves performance with database-level filtering

---

### Requirement: Creature Lookup Tool
The system SHALL update the `lookup_creature` tool to eliminate client-side filtering and use enhanced database-level filtering.

**MODIFIED Implementation:**
- Remove client-side filtering that fetched 11x data immediately
- Enhance existing `name` parameter to use case-insensitive, wildcard, and automatic slug fallback matching
- Perform all filtering at database level with single parameter interface

#### Scenario: Eliminate 11x over-fetching performance bug
**Given** a user searches with `lookup_creature(limit=20)` without name filters
**When** the `lookup_creature` tool is invoked
**Then** the system fetches exactly 20 records (not 220)
**And** memory usage is reduced by 90%
**And** no client-side filtering loops exist
**And** response time improves by factor of 5 or more

#### Scenario: Efficient case-insensitive creature search
**Given** a user searches with `name="ancient red dragon"`
**When** the `lookup_creature` tool is invoked
**Then** the system performs case-insensitive database filtering
**And** returns Ancient Red Dragon stat block
**And** uses efficient `LOWER(name) = LOWER(?)` SQL query
**And** no client-side filtering occurs

#### Scenario: Wildcard partial creature name search
**Given** a user searches with `name="*dragon*"`, type="dragon", limit=10`
**When** the `lookup_creature` tool is invoked
**Then** the system detects wildcards and performs database-level LIKE query
**And** returns dragons containing "dragon" in name
**And** filters efficiently without over-fetching
**And** respects limit parameter exactly (not limit * 11)

#### Scenario: Automatic slug fallback for creatures
**Given** a user searches with `name="ancient-red-dragon"` (exact slug format)
**When** the `lookup_creature` tool is invoked
**Then** name search fails, automatic slug search succeeds
**And** returns creature data via efficient PRIMARY KEY lookup
**And** provides transparent fallback behavior

---

### Requirement: Character Option Lookup Tool
The system SHALL update the `lookup_character_option` tool to eliminate client-side filtering and use enhanced database-level filtering.

**MODIFIED Implementation:**
- Remove client-side filtering from character option queries completely
- Enhance existing `name` parameter to use case-insensitive, wildcard, and automatic slug fallback matching
- Perform database-level filtering for all character option types with exact limit adherence

#### Scenario: Eliminate character options 11x over-fetching bug
**Given** a user searches with `type="class", limit=20`
**When** the `lookup_character_option` tool is invoked
**Then** the system fetches exactly 20 character options (not 220)
**And** eliminates all client-side filtering loops
**And** memory usage reduces by 90% for filtered queries
**And** response time improves significantly

#### Scenario: Efficient case-insensitive class filtering
**Given** a user searches with `type="class", name="paladin"`
**When** the `lookup_character_option` tool is invoked
**Then** the system performs case-insensitive database filtering
**And** returns Paladin class details efficiently
**And** uses `LOWER(name) = LOWER(?)` SQL query
**And** no client-side filtering occurs

#### Scenario: Wildcard partial character option search
**Given** a user searches with `type="race", name="*elf*", limit=5`
**When** the `lookup_character_option` tool is invoked
**Then** the system detects wildcards and performs database-level LIKE query
**And** returns elf races including subraces efficiently
**And** respects exact limit parameter (not limit * 11)
**And** filters at database level with proper indexes

#### Scenario: Automatic slug fallback for feats
**Given** a user searches with `type="feat", name="sharpshooter"`
**When** the `lookup_character_option` tool is invoked
**Then** system performs case-insensitive name search
**And** automatically falls back to slug search if needed
**And** returns Sharpshooter feat details via optimal lookup
**And** eliminates client-side memory overhead

---

### Requirement: Equipment Lookup Tool
The system SHALL update the `lookup_equipment` tool to eliminate client-side filtering across all equipment types.

**MODIFIED Implementation:**
- Remove client-side filtering from weapons, armor, and magic-items queries completely
- Enhance existing `name` parameter to use case-insensitive, wildcard, and automatic slug fallback matching
- Perform database-level filtering for each equipment type with exact limit adherence

#### Scenario: Eliminate equipment 11x over-fetching bug
**Given** a user searches with `type="weapon", limit=15`
**When** the `lookup_equipment` tool is invoked
**Then** the system fetches exactly 15 weapons (not 165)
**And** eliminates all client-side filtering loops
**And** memory usage reduces by 90% for filtered queries
**And** response time improves significantly

#### Scenario: Case-insensitive equipment search
**Given** a user searches with `type="armor", name="chain mail"`
**When** the `lookup_equipment` tool is invoked
**Then** the system performs case-insensitive database filtering
**And** returns chain mail and related armor items efficiently
**And** uses `LOWER(name) = LOWER(?)` SQL query with proper indexes
**And** no client-side filtering occurs

#### Scenario: Wildcard partial equipment name search
**Given** a user searches with `type="weapon", name="*sword*", limit=10`
**When** the `lookup_equipment` tool is invoked
**Then** the system detects wildcards and performs database-level LIKE query
**And** returns weapons containing "sword" efficiently
**And** respects exact limit (not limit * 11)
**And** filters at database level with proper indexes

#### Scenario: Automatic slug fallback for magic items
**Given** a user searches with `type="magic-item", name="wand-of-magic-missiles"`
**When** the `lookup_equipment` tool is invoked
**Then** name search may fail, automatic slug search succeeds
**And** returns exact magic item via PRIMARY KEY lookup
**And** provides transparent fallback behavior
**And** eliminates memory overhead from client-side over-fetching

---

### Requirement: Rule Lookup Tool
The system SHALL update the `lookup_rule` tool to use enhanced database-level filtering with existing parameters.

**MODIFIED Implementation:**
- Enhance existing `name` parameter to use case-insensitive, wildcard, and automatic slug fallback matching
- Change rule searches from case-sensitive to case-insensitive filtering
- Enable wildcard-based partial matching for rule discovery

#### Scenario: Efficient case-insensitive rule search
**Given** a user searches with `type="rule", name="opportunity attack"`
**When** the `lookup_rule` tool is invoked
**Then** the system performs case-insensitive database filtering
**And** returns opportunity attack rules
**And** uses efficient `LOWER(name) = LOWER(?)` SQL query
**And** eliminates case-sensitivity issues

#### Scenario: Automatic slug fallback for rules
**Given** a user searches with `type="condition", name="grappled"`
**When** the `lookup_rule` tool is invoked
**Then** the system performs case-insensitive name search first
**And** automatically tries slug search if name match fails
**And** returns Grappled condition details via optimal lookup
**And** results are consistent across different capitalizations

#### Scenario: Wildcard partial rule search
**Given** a user searches with `type="damage-type", name="*radiant*"`
**When** the `lookup_rule` tool is invoked
**Then** the system detects wildcards and performs partial matching
**And** returns radiant damage type information efficiently
**And** uses `LOWER(name) LIKE LOWER(?)` database query
**And** provides consistent behavior with other tools

---

### Requirement: Error Handling
The system SHALL handle errors gracefully across all tools.

**Error Types:**
- API failures (network errors, timeouts, 5xx responses)
- Invalid parameters (wrong types, out of range values)
- Empty results (valid query but no matches)
- Invalid API responses (malformed JSON, unexpected schema)

**Error Handling Behavior:**
- Return user-friendly error messages (not stack traces)
- Log detailed errors for debugging
- Use cached responses when available (if API fails)
- Respect error cache TTL (default 5 minutes) to avoid hammering failed endpoints

#### Scenario: API network failure
**Given** the Open5e API is unreachable
**When** any tool is invoked
**Then** the system returns a user-friendly error message
**And** logs the detailed error for debugging
**And** does not expose stack traces to the user

#### Scenario: Invalid parameter type
**Given** a user provides `level="invalid"` to lookup_spell
**When** the tool is invoked
**Then** FastMCP's parameter validation catches the error
**And** returns a clear validation error message

#### Scenario: Empty results
**Given** a user queries for a creature that doesn't exist
**When** lookup_creature is invoked
**Then** the system returns an empty list
**And** does not treat this as an error condition

---

### Requirement: Response Formatting
The system SHALL format all tool responses as structured data suitable for AI consumption.

**Formatting Requirements:**
- Return JSON-serializable data structures
- Include source attribution (document name, API source)
- Use consistent field names across similar data types
- Format text descriptions as plain text or markdown where appropriate
- Include relevant metadata (timestamp, cache status)

#### Scenario: Structured spell response
**Given** a successful spell lookup
**When** results are returned
**Then** the response includes all specified spell fields
**And** the data is JSON-serializable
**And** includes source attribution

#### Scenario: Source attribution
**Given** any successful lookup
**When** results are returned
**Then** each result includes source document information
**And** identifies which API provided the data

---

### Requirement: Performance and Caching
The system SHALL leverage the existing cache layer for all API requests.

**Caching Behavior:**
- All API requests automatically use the cache layer
- Cache TTL: 7 days for successful responses
- Error cache TTL: 5 minutes for failed requests
- Cache key based on endpoint URL and query parameters
- No manual cache management required in tool code

#### Scenario: Cache hit
**Given** a spell lookup for "Fireball" was recently performed
**When** the same lookup is requested again within 7 days
**Then** the system returns cached results
**And** does not make a new API request

#### Scenario: Cache miss
**Given** a spell lookup for "Shield" has never been performed
**When** the lookup is requested
**Then** the system queries the Open5e v2 API
**And** caches the response for 7 days

---

### Requirement: Tool Registration
The system SHALL register all tools with the FastMCP server for MCP protocol exposure.

**Registration Requirements:**
- Tools decorated with `@mcp.tool()` decorator
- Parameter types defined for automatic validation
- Tool descriptions provided for AI assistant discovery
- Tools available immediately after server startup

#### Scenario: Tools visible in MCP protocol
**Given** the LoreKeeper server is started
**When** an MCP client connects
**Then** all 5 tools are visible in the protocol schema
**And** parameter definitions are included

#### Scenario: Tool invocation via MCP
**Given** an MCP client is connected
**When** the client invokes lookup_spell
**Then** the tool executes and returns results via MCP protocol
**And** the response conforms to MCP response format

---

### Requirement: Consistent Tool Interface Standards
The system SHALL ensure all 5 MCP tools have consistent enhanced search behavior using existing parameters.

**Parameters:**
- All tools maintain exactly the same parameters as before: `name`, `limit`, plus tool-specific filters
- The existing `name` parameter is enhanced transparently with case-insensitive, wildcard, and automatic slug fallback matching
- Zero new parameters added to any tools

**Implementation:**
- All filtering performed at database level (no client-side filtering)
- Eliminate 11x over-fetching bug completely
- Consistent SQL parameter binding for security
- Uniform error handling and validation unchanged

#### Scenario: Identical parameter availability
**Given** examining all 5 MCP tool interfaces
**When** checking parameter definitions
**Then** all tools have exactly the same parameters as before enhancement
**And** all tools maintain their tool-specific parameters unchanged
**And** parameter types and defaults remain identical
**And** FastMCP parameter validation works as before

#### Scenario: Consistent enhanced filtering behavior
**Given** using the same search parameters across different tools
**When** performing searches with `name="fire*"`
**Then** all tools return consistent wildcard-based results for their domains
**And** all tools use database-level filtering only
**And** all tools respect limit parameters exactly (not limit * 11)
**And** performance characteristics are similar and optimized across tools

#### Scenario: Unchanged error handling consistency
**Given** invalid parameters provided to any tool
**When** the tool is invoked
**Then** all tools show identical error messages as before
**And** parameter validation behavior is exactly the same
**And** FastMCP handles errors consistently without changes
**And** user experience is predictable and unchanged
