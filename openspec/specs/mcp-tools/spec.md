# mcp-tools Specification

## Purpose
Defines the five core MCP tools that provide D&D 5e content lookup capabilities: `lookup_spell`, `lookup_creature`, `lookup_equipment`, `lookup_character_option`, and `lookup_rule`. Also includes the `list_documents` and `search_dnd_content` tools. These tools are the primary interface for AI assistants to access cached game content through the Model Context Protocol with enhanced search features (case-insensitive matching, wildcards, slug fallback) and document-based filtering.
## Requirements
### Requirement: Spell Lookup Tool

The system SHALL update the `lookup_spell` tool to support optional semantic search while maintaining all existing enhanced filtering capabilities.

**MODIFIED Implementation:**
- Add optional `semantic_query: str | None` parameter
- When `semantic_query` is provided, use `cache.semantic_search()` instead of `cache.get_entities()`
- Combine semantic search with existing filters (level, school, concentration, ritual, etc.)
- When `semantic_query` is None, behavior is identical to current implementation

#### Scenario: Enhanced spell search with semantic query
**Given** a user searches with `semantic_query="damage over time", level=3, school="Evocation"`
**When** the `lookup_spell` tool is invoked
**Then** the system performs semantic search with query "damage over time"
**And** filters to level 3 Evocation spells
**And** returns spells ranked by semantic similarity within filtered set
**And** respects the `limit` parameter

#### Scenario: Spell search combining semantic and document filter
**Given** a user searches with `semantic_query="healing", documents=["srd-5e"]`
**When** the `lookup_spell` tool is invoked
**Then** the system performs semantic search on SRD spells only
**And** combines document filter with semantic ranking
**And** all existing document filtering continues to work

### Requirement: Creature Lookup Tool

The system SHALL update the `lookup_creature` tool to support optional semantic search while maintaining all existing enhanced filtering capabilities.

**MODIFIED Implementation:**
- Add optional `semantic_query: str | None` parameter
- When `semantic_query` is provided, use semantic search for creature discovery
- Combine semantic search with existing filters (type, cr, size, etc.)
- Maintain backward compatibility for callers not using semantic search

#### Scenario: Semantic creature search by concept
**Given** a user searches with `semantic_query="undead that drain life", type="undead"`
**When** the `lookup_creature` tool is invoked
**Then** the system performs semantic search filtered to undead type
**And** returns creatures like "Vampire", "Wraith", "Specter" ranked by relevance
**And** structured filters reduce search space before vector search

#### Scenario: Creature search without semantic query
**Given** a user searches with `type="dragon", cr="10", limit=5`
**When** the `lookup_creature` tool is invoked without semantic_query
**Then** behavior is identical to current implementation
**And** no embedding generation occurs
**And** database-level filtering only

### Requirement: Character Option Lookup Tool

The system SHALL update the `lookup_character_option` tool to support optional semantic search.

**MODIFIED Implementation:**
- Add optional `semantic_query: str | None` parameter
- Enable semantic discovery of character options by concept
- Maintain backward compatibility for existing callers

#### Scenario: Semantic character option search
**Given** a user searches with `semantic_query="divine warrior", option_type="class"`
**When** the `lookup_character_option` tool is invoked
**Then** semantic search ranks "Paladin" and "Cleric" higher than "Rogue"
**And** results are filtered to classes only
**And** results capture conceptual match beyond keywords

### Requirement: Equipment Lookup Tool

The system SHALL update the `lookup_equipment` tool to support optional semantic search.

**MODIFIED Implementation:**
- Add optional `semantic_query: str | None` parameter
- Enable semantic discovery of equipment by description/properties
- Maintain backward compatibility for existing callers

#### Scenario: Semantic equipment search
**Given** a user searches with `semantic_query="protects against projectiles", item_type="armor"`
**When** the `lookup_equipment` tool is invoked
**Then** semantic search finds armor with protective properties
**And** "Shield" and items with deflection abilities rank higher
**And** structured item_type filter is applied before semantic ranking

### Requirement: Rule Lookup Tool

The system SHALL update the `lookup_rule` tool to support optional semantic search.

**MODIFIED Implementation:**
- Add optional `semantic_query: str | None` parameter
- Enable semantic discovery of rules by description
- Maintain backward compatibility for existing callers

#### Scenario: Semantic rule search
**Given** a user searches with `semantic_query="what happens when I fall", rule_type="rule"`
**When** the `lookup_rule` tool is invoked
**Then** semantic search finds falling damage rules
**And** returns rules about falling, jumping, and environmental hazards
**And** structured rule_type filter is applied

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

### Requirement: Semantic Query Parameter for Lookup Tools

All lookup tools SHALL support an optional `semantic_query` parameter that enables natural language similarity search using the Milvus Lite vector backend.

#### Scenario: Spell lookup with semantic query
**Given** the cache contains spells with embeddings
**When** `lookup_spell(semantic_query="protect from fire", level=3)` is invoked
**Then** the system performs semantic search with query "protect from fire"
**And** filters results to level 3 spells
**And** returns spells ranked by semantic similarity to the query
**And** "Fire Shield" ranks higher than "Ice Storm" for this query

#### Scenario: Creature lookup with semantic query
**Given** the cache contains creatures with embeddings
**When** `lookup_creature(semantic_query="fire breathing beast", type="dragon")` is invoked
**Then** the system performs semantic search filtered to dragon type
**And** returns dragons ranked by semantic similarity
**And** results capture conceptual meaning beyond keyword matching

#### Scenario: Equipment lookup with semantic query
**Given** the cache contains equipment with embeddings
**When** `lookup_equipment(semantic_query="weapon that returns when thrown", item_type="weapon")` is invoked
**Then** the system performs semantic search filtered to weapons
**And** returns weapons like "Dwarven Thrower" ranked by relevance
**And** structured filters are applied before semantic ranking

#### Scenario: Character option lookup with semantic query
**Given** the cache contains character options with embeddings
**When** `lookup_character_option(semantic_query="masters of arcane magic", option_type="class")` is invoked
**Then** the system performs semantic search filtered to classes
**And** "Wizard" and "Sorcerer" rank higher than "Fighter"

#### Scenario: Rule lookup with semantic query
**Given** the cache contains rules with embeddings
**When** `lookup_rule(semantic_query="attacking while hidden", rule_type="rule")` is invoked
**Then** the system performs semantic search on rules
**And** returns rules about stealth, surprise, and attacking from hidden position

#### Scenario: Lookup without semantic query (backward compatible)
**Given** any lookup tool is invoked without semantic_query parameter
**When** the tool executes
**Then** the system performs structured filtering only
**And** no embedding generation or vector search occurs
**And** behavior is identical to pre-Milvus implementation
**And** existing tool callers continue working without modification

### Requirement: Semantic Search in Unified Search Tool

The `search_dnd_content` tool SHALL use semantic search by default when the Milvus Lite backend is active.

#### Scenario: Default semantic search
**Given** Milvus Lite is the active cache backend
**When** `search_dnd_content(query="spells that heal wounds")` is invoked
**Then** the system performs semantic search across all entity types
**And** returns results ranked by semantic similarity to the query
**And** healing spells rank higher than damage spells

#### Scenario: Semantic search with entity type filter
**Given** Milvus Lite is the active cache backend
**When** `search_dnd_content(query="fire damage", content_types=["Spell"])` is invoked
**Then** semantic search is performed on spells only
**And** results are ranked by semantic similarity within spells
**And** document and content type filters are applied

#### Scenario: Disable semantic search
**Given** Milvus Lite is the active cache backend
**When** `search_dnd_content(query="fireball", semantic=False)` is invoked
**Then** the system performs structured/keyword search only
**And** no vector similarity calculation occurs
**And** results are based on exact/partial name matching

#### Scenario: Fallback when Milvus unavailable
**Given** SQLite is the active cache backend (Milvus not available)
**When** `search_dnd_content(query="healing")` is invoked
**Then** the system falls back to structured search
**And** logs a warning that semantic search is unavailable
**And** returns results based on keyword matching

### Requirement: Semantic Search Error Handling in Tools

Tools SHALL gracefully handle semantic search failures.

#### Scenario: Embedding generation timeout
**Given** the embedding model takes too long to generate embeddings
**When** a semantic search is requested with a timeout
**Then** the tool falls back to structured search
**And** logs a warning about embedding timeout
**And** returns results without semantic ranking

#### Scenario: Empty semantic query handling
**Given** a tool is called with `semantic_query=""`
**When** the tool executes
**Then** the system treats empty string as no semantic query
**And** falls back to structured filtering only
**And** returns results without semantic ranking

#### Scenario: Very long semantic query handling
**Given** a semantic query exceeding 512 characters
**When** the tool executes
**Then** the query is truncated to model's max sequence length
**And** a warning is logged about query truncation
**And** search still returns relevant results

### Requirement: Similarity Score in Results

Tool responses SHALL include similarity scores when semantic search is used.

#### Scenario: Include similarity score in spell results
**Given** a semantic search is performed for spells
**When** results are returned
**Then** each result includes a `similarity_score` field (0.0 to 1.0)
**And** results are ordered by similarity_score descending
**And** the score indicates semantic relevance to the query

#### Scenario: No similarity score for structured search
**Given** a structured search is performed (no semantic_query)
**When** results are returned
**Then** results do not include a `similarity_score` field
**And** results are returned in storage/API order
**And** response format remains backward compatible
