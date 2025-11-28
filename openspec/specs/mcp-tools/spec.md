# mcp-tools Specification

## Purpose
Defines the five core MCP tools that provide D&D 5e content lookup capabilities: `lookup_spell`, `lookup_creature`, `lookup_equipment`, `lookup_character_option`, and `lookup_rule`. Also includes the `list_documents` and `search_dnd_content` tools. These tools are the primary interface for AI assistants to access cached game content through the Model Context Protocol with enhanced search features (case-insensitive matching, wildcards, slug fallback) and document-based filtering.

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

#### Scenario: Normalized document metadata in responses
- **WHEN** any lookup tool returns results with document metadata available
- **THEN** the response includes normalized document fields (`document_key`, `document_name`, `document_source`) in addition to existing source attribution
- **AND** tools use these fields consistently across all entity types (spells, creatures, equipment, character options, rules)
- **AND** responses remain backward compatible for callers that ignore the new fields

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

### Requirement: Document-Aware Tool Filtering
The system SHALL support optional document-based filtering for MCP tools that fetch entities from the cache.

#### Scenario: Filter spells by Open5e document key
- **WHEN** a caller invokes `lookup_spell` with a document filter (for example, `document_key="srd-5e"` or another Open5e document key)
- **THEN** the tool limits results to entities whose normalized document metadata matches the specified document key
- **AND** combines this constraint with existing filters such as name, level, and school
- **AND** respects the existing `limit` parameter without over-fetching or client-side filtering

#### Scenario: Filter creatures to SRD-only content
- **WHEN** a caller invokes `lookup_creature` with a document filter indicating SRD-only content
- **THEN** the tool returns only creatures whose document metadata corresponds to SRD documents (from Open5e)
- **AND** continues to apply other filters (e.g., challenge rating, type) at the database level
- **AND** returns an empty list (not an error) if no entities match the specified document filter

### Requirement: Document Metadata in Tool Responses
The system SHALL include normalized document metadata in tool responses, aligned with underlying entity document metadata.

#### Scenario: Spell response includes document information
- **WHEN** a spell lookup returns one or more entities
- **THEN** each result includes document metadata fields such as `document_key`, `document_name`, and `document_source`
- **AND** these values are derived from the same normalized entity metadata used for filtering
- **AND** remain consistent regardless of whether results were filtered by document

#### Scenario: OrcBrew spell response includes book as document
- **WHEN** a spell or other entity originates from an OrcBrew file
- **THEN** the tool response includes the OrcBrew book name as `document_name` and a normalized `document_key` derived from that book
- **AND** `document_source` identifies the origin as `orcbrew`
- **AND** downstream callers can distinguish OrcBrew-derived content from Open5e data using this metadata

### Requirement: Document Listing Tool
The system SHALL provide an MCP tool to list all available documents in the cache.

#### Scenario: List all documents with metadata
- **WHEN** the user invokes `list_documents()` with no filters
- **THEN** the tool returns all cached documents across all sources
- **AND** each document includes: document_name, source_api, entity_count
- **AND** documents are sorted by entity_count descending
- **AND** the tool description explains it shows cached documents only

#### Scenario: Filter documents by source
- **WHEN** the user invokes `list_documents(source="open5e_v2")`
- **THEN** only Open5e documents are returned
- **AND** documents from other sources are excluded
- **AND** valid source values are documented: "open5e_v1", "open5e_v2", "orcbrew"

#### Scenario: Format as JSON
- **WHEN** the user invokes `list_documents(format="json")`
- **THEN** the tool returns structured JSON with all document fields
- **AND** JSON is parseable by standard JSON tools
- **AND** includes optional metadata fields (publisher, license) when available

#### Scenario: Format as text
- **WHEN** the user invokes `list_documents(format="text")`
- **THEN** the tool returns human-readable formatted text
- **AND** text includes document name, source, and entity count
- **AND** text is easy to scan (aligned columns or bullet points)

#### Scenario: Handle empty cache
- **WHEN** `list_documents()` is called on an empty cache
- **THEN** the tool returns a message "No documents found in cache"
- **AND** no errors are raised

### Requirement: Document Filtering in Search Tool
The search tool SHALL support filtering results by document keys.

#### Scenario: Search with single document filter
- **WHEN** the user invokes `search_dnd_content(query="fireball", documents=["srd-5e"])`
- **THEN** only results from the "srd-5e" document are returned
- **AND** results from other documents are excluded
- **AND** search still respects fuzzy and semantic matching parameters

#### Scenario: Search with multiple document filters
- **WHEN** the user invokes `search_dnd_content(query="dragon", documents=["srd-5e", "tce", "phb"])`
- **THEN** results from all three documents are returned
- **AND** results from other documents are excluded
- **AND** results are merged and deduplicated

#### Scenario: Search without document filter
- **WHEN** the user invokes `search_dnd_content(query="healing")` without documents
- **THEN** results from all documents are returned
- **AND** behavior is identical to current implementation (backward compatible)

#### Scenario: Search with non-existent document
- **WHEN** the user invokes `search_dnd_content(query="spell", documents=["non-existent"])`
- **THEN** an empty result list is returned
- **AND** no errors are raised
- **AND** a message indicates no results match the document filter

---

### Requirement: Document Filtering in Spell Lookup Tool
The spell lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup spell with document filter
- **WHEN** the user invokes `lookup_spell(name="fireball", documents=["srd-5e"])`
- **THEN** only "Fireball" from "srd-5e" is returned
- **AND** if "Fireball" exists in other documents, those versions are excluded

#### Scenario: Lookup spells by level with document filter
- **WHEN** the user invokes `lookup_spell(level=3, documents=["srd-5e", "tce"])`
- **THEN** all level 3 spells from both documents are returned
- **AND** spells from other documents are excluded

#### Scenario: Lookup without document filter
- **WHEN** the user invokes `lookup_spell(name="fireball")` without documents
- **THEN** all versions of "Fireball" from all documents are returned
- **AND** behavior is identical to current implementation (backward compatible)

---

### Requirement: Document Filtering in Creature Lookup Tool
The creature lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup creature with document filter
- **WHEN** the user invokes `lookup_creature(name="dragon", documents=["srd-5e"])`
- **THEN** only dragons from "srd-5e" are returned
- **AND** creatures from other documents are excluded

#### Scenario: Lookup creatures by type with document filter
- **WHEN** the user invokes `lookup_creature(type="dragon", challenge_rating=10, documents=["tce"])`
- **THEN** only dragons from "tce" with CR 10 are returned
- **AND** all filter parameters work together (type AND cr AND document)

---

### Requirement: Document Filtering in Equipment Lookup Tool
The equipment lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup weapon with document filter
- **WHEN** the user invokes `lookup_equipment(item_type="weapon", name="longsword", documents=["srd-5e"])`
- **THEN** only "Longsword" from "srd-5e" is returned
- **AND** equipment from other documents is excluded

#### Scenario: Lookup all weapons with document filter
- **WHEN** the user invokes `lookup_equipment(item_type="weapon", documents=["srd-5e", "phb"])`
- **THEN** all weapons from both documents are returned
- **AND** weapons from other documents are excluded

---

### Requirement: Document Filtering in Character Option Lookup Tool
The character option lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup class with document filter
- **WHEN** the user invokes `lookup_character_option(option_type="class", name="wizard", documents=["srd-5e"])`
- **THEN** only the "Wizard" class from "srd-5e" is returned
- **AND** classes from other documents are excluded

#### Scenario: Lookup all backgrounds with document filter
- **WHEN** the user invokes `lookup_character_option(option_type="background", documents=["phb"])`
- **THEN** all backgrounds from "phb" are returned
- **AND** backgrounds from other documents are excluded

---

### Requirement: Document Filtering in Rule Lookup Tool
The rule lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup rule with document filter
- **WHEN** the user invokes `lookup_rule(rule_type="rule", name="combat", documents=["srd-5e"])`
- **THEN** only combat rules from "srd-5e" are returned
- **AND** rules from other sources are excluded

---

### Requirement: Consistent Document Filter Parameter
All lookup and search tools SHALL use consistent parameter naming and behavior for document filtering.

#### Scenario: Consistent parameter naming
- **GIVEN** all lookup tools (spell, creature, equipment, character_option, rule) and search tool
- **WHEN** any tool is invoked with document filtering
- **THEN** the parameter is named `documents` (not `document` or `document_keys`)
- **AND** the parameter accepts a list of strings
- **AND** the parameter is optional with default None (no filtering)

#### Scenario: Consistent filtering behavior
- **GIVEN** any lookup or search tool with documents parameter
- **WHEN** documents is None
- **THEN** no document filtering is applied
- **WHEN** documents is an empty list
- **THEN** an empty result is returned
- **WHEN** documents is a non-empty list
- **THEN** only results from those documents are returned

---

### Requirement: Document Filter Response Metadata
Tool responses SHALL include document information for transparency.

#### Scenario: Include document in spell response
- **WHEN** `lookup_spell(name="fireball")` returns results
- **THEN** each spell in the response includes a `document` field
- **AND** the document field shows which document the spell came from
- **AND** this enables users to verify document filtering worked correctly

#### Scenario: Include document in search response
- **WHEN** `search_dnd_content(query="dragon")` returns results
- **THEN** each result includes document metadata
- **AND** users can see which document each result originated from

---

### Requirement: Test Context Cleanup Fixture
The system SHALL provide an automatic cleanup fixture that clears all tool repository contexts after each test.

#### Scenario: Prevent test pollution
When running multiple tests, repository context from one test should not affect other tests.

**Acceptance Criteria:**
- New `cleanup_tool_contexts` fixture in `tests/test_tools/conftest.py`
- Fixture has `autouse=True` to run automatically
- Fixture clears `_repository_context` for all 5 tools after each test
- Runs in teardown phase (yield pattern)
- Imports all tool modules to access their contexts
- Zero test pollution between test cases

#### Scenario: Automatic context isolation
When a test sets a repository context, it should be automatically cleared after the test.

**Acceptance Criteria:**
- Developer does not need to manually clear context
- Context empty at start of each test
- Failed tests do not leave context dirty
- Works with parallel test execution (pytest-xdist)

---

### Requirement: Type Safety for Tool Signatures
The system SHALL ensure all tool function signatures are properly typed without `Any` parameters.

#### Scenario: Type checking passes
When running mypy on tool modules, there should be no warnings about `Any` type parameters.

**Acceptance Criteria:**
- No `repository: Any = None` parameters in any tool
- `_get_repository()` functions have proper return type annotations
- `_repository_context` properly typed as `dict[str, Any]`
- `uv run mypy src/lorekeeper_mcp/tools/` passes with no errors
- No `Type of parameter "repository" is Any` warnings

---

### Requirement: Backward Compatibility for Tool Callers
The system SHALL ensure existing tool callers (MCP server, integration tests) continue to work without modification.

#### Scenario: MCP server requires no changes
When the server registers tools, it should work identically to before.

**Acceptance Criteria:**
- `src/lorekeeper_mcp/server.py` requires no changes
- Tools still registered with `mcp.tool()` decorator
- Server starts and serves all 5 tools correctly
- Tool invocations work identically for external clients

#### Scenario: Integration tests work without modification
When running integration tests that don't inject repositories, they should work unchanged.

**Acceptance Criteria:**
- `tests/test_tools/test_integration.py` requires no changes (or minimal)
- Integration tests call tools normally without repository parameter
- Tools use real repositories via factory
- Caching behavior unchanged

---

### Requirement: Documentation Accuracy
The system SHALL update all tool docstrings and comments to reflect the internal repository pattern.

#### Scenario: Docstrings don't mention repository parameter
When reading tool function docstrings, developers should see accurate parameters.

**Acceptance Criteria:**
- All tool docstrings updated to remove repository parameter from Args section
- Module-level docstrings mention repository pattern is used internally
- Examples in docstrings show usage without repository parameter
- Comments about repository usage clarify it's internal only
