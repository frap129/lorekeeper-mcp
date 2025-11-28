# mcp-tools Specification Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
