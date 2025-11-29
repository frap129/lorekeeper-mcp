## MODIFIED Requirements

### Requirement: Spell Search Tool

The system SHALL provide a `search_spell` tool that supports hybrid search combining semantic search with structured filtering.

**Implementation:**
- Optional `search: str | None` parameter for natural language similarity search
- When `search` is provided, use `cache.semantic_search()` for semantic ranking
- Combine semantic search with existing filters (level, school, concentration, ritual, etc.)
- When `search` is None, use structured filtering only

#### Scenario: Hybrid spell search with semantic query
**Given** a user searches with `search="damage over time", level=3, school="Evocation"`
**When** the `search_spell` tool is invoked
**Then** the system performs semantic search with query "damage over time"
**And** filters to level 3 Evocation spells
**And** returns spells ranked by semantic similarity within filtered set
**And** respects the `limit` parameter

#### Scenario: Spell search combining semantic and document filter
**Given** a user searches with `search="healing", documents=["srd-5e"]`
**When** the `search_spell` tool is invoked
**Then** the system performs semantic search on SRD spells only
**And** combines document filter with semantic ranking
**And** all existing document filtering continues to work

### Requirement: Creature Search Tool

The system SHALL provide a `search_creature` tool that supports hybrid search combining semantic search with structured filtering.

**Implementation:**
- Optional `search: str | None` parameter for semantic creature discovery
- Combine semantic search with existing filters (type, cr, size, etc.)
- Maintain backward compatibility for callers not using semantic search

#### Scenario: Semantic creature search by concept
**Given** a user searches with `search="undead that drain life", type="undead"`
**When** the `search_creature` tool is invoked
**Then** the system performs semantic search filtered to undead type
**And** returns creatures like "Vampire", "Wraith", "Specter" ranked by relevance
**And** structured filters reduce search space before vector search

#### Scenario: Creature search without semantic query
**Given** a user searches with `type="dragon", cr="10", limit=5`
**When** the `search_creature` tool is invoked without search parameter
**Then** behavior uses structured filtering only
**And** no embedding generation occurs
**And** database-level filtering only

### Requirement: Character Option Search Tool

The system SHALL provide a `search_character_option` tool that supports hybrid search.

**Implementation:**
- Optional `search: str | None` parameter
- Enable semantic discovery of character options by concept
- Maintain backward compatibility for existing callers

#### Scenario: Semantic character option search
**Given** a user searches with `search="divine warrior", type="class"`
**When** the `search_character_option` tool is invoked
**Then** semantic search ranks "Paladin" and "Cleric" higher than "Rogue"
**And** results are filtered to classes only
**And** results capture conceptual match beyond keywords

### Requirement: Equipment Search Tool

The system SHALL provide a `search_equipment` tool that supports hybrid search.

**Implementation:**
- Optional `search: str | None` parameter
- Enable semantic discovery of equipment by description/properties
- Maintain backward compatibility for existing callers

#### Scenario: Semantic equipment search
**Given** a user searches with `search="protects against projectiles", type="armor"`
**When** the `search_equipment` tool is invoked
**Then** semantic search finds armor with protective properties
**And** "Shield" and items with deflection abilities rank higher
**And** structured type filter is applied before semantic ranking

### Requirement: Rule Search Tool

The system SHALL provide a `search_rule` tool that supports hybrid search.

**Implementation:**
- Optional `search: str | None` parameter
- Enable semantic discovery of rules by description
- Maintain backward compatibility for existing callers

#### Scenario: Semantic rule search
**Given** a user searches with `search="what happens when I fall", rule_type="rule"`
**When** the `search_rule` tool is invoked
**Then** semantic search finds falling damage rules
**And** returns rules about falling, jumping, and environmental hazards
**And** structured rule_type filter is applied

### Requirement: Consistent Tool Interface Standards
The system SHALL ensure all 5 MCP tools have consistent search behavior using the unified `search` parameter.

**Parameters:**
- All tools use `search` parameter for semantic/natural language queries
- The `name` parameter is removed from all tools
- The `semantic_query` parameter is renamed to `search`
- All tool-specific filters (level, type, cr, etc.) remain unchanged

**Implementation:**
- All filtering performed at database level (no client-side filtering)
- Consistent SQL parameter binding for security
- Uniform error handling and validation

#### Scenario: Identical parameter availability
**Given** examining all 5 MCP tool interfaces
**When** checking parameter definitions
**Then** all tools have a `search: str | None` parameter
**And** no tools have a `name` parameter
**And** no tools have a `semantic_query` parameter
**And** all tools maintain their tool-specific parameters unchanged
**And** FastMCP parameter validation works as before

#### Scenario: Consistent search behavior
**Given** using the same search parameters across different tools
**When** performing searches with `search="fire"`
**Then** all tools return semantically relevant results for "fire"
**And** all tools use vector search when `search` is provided
**And** all tools respect limit parameters exactly
**And** performance characteristics are similar across tools

### Requirement: Semantic Query Parameter for Search Tools

All search tools SHALL support an optional `search` parameter that enables natural language similarity search using the Milvus Lite vector backend.

#### Scenario: Spell search with semantic query
**Given** the cache contains spells with embeddings
**When** `search_spell(search="protect from fire", level=3)` is invoked
**Then** the system performs semantic search with query "protect from fire"
**And** filters results to level 3 spells
**And** returns spells ranked by semantic similarity to the query
**And** "Fire Shield" ranks higher than "Ice Storm" for this query

#### Scenario: Creature search with semantic query
**Given** the cache contains creatures with embeddings
**When** `search_creature(search="fire breathing beast", type="dragon")` is invoked
**Then** the system performs semantic search filtered to dragon type
**And** returns dragons ranked by semantic similarity
**And** results capture conceptual meaning beyond keyword matching

#### Scenario: Equipment search with semantic query
**Given** the cache contains equipment with embeddings
**When** `search_equipment(search="weapon that returns when thrown", type="weapon")` is invoked
**Then** the system performs semantic search filtered to weapons
**And** returns weapons like "Dwarven Thrower" ranked by relevance
**And** structured filters are applied before semantic ranking

#### Scenario: Character option search with semantic query
**Given** the cache contains character options with embeddings
**When** `search_character_option(search="masters of arcane magic", type="class")` is invoked
**Then** the system performs semantic search filtered to classes
**And** "Wizard" and "Sorcerer" rank higher than "Fighter"

#### Scenario: Rule search with semantic query
**Given** the cache contains rules with embeddings
**When** `search_rule(search="attacking while hidden", rule_type="rule")` is invoked
**Then** the system performs semantic search on rules
**And** returns rules about stealth, surprise, and attacking from hidden position

#### Scenario: Search without search parameter (backward compatible)
**Given** any search tool is invoked without search parameter
**When** the tool executes
**Then** the system performs structured filtering only
**And** no embedding generation or vector search occurs
**And** existing tool callers using only structured filters continue working
