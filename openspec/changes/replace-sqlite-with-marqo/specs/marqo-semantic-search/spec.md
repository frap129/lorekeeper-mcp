# marqo-semantic-search Specification

**Spec ID**: `marqo-semantic-search`
**Change**: `2025-11-08-replace-sqlite-with-marqo`
**Status**: Proposed

## Purpose

Add semantic search capabilities using Marqo's vector embeddings to enable natural language queries and similarity-based retrieval for D&D content.

## ADDED Requirements

### Requirement: Natural language semantic search

The system SHALL support natural language queries that return semantically relevant entities based on vector similarity.

**Rationale**: Users can describe what they need in plain language without knowing exact spell names or requiring complex filters.

#### Scenario: Semantic spell search with natural language

**Given** multiple protection and defensive spells are indexed
**When** `search_entities("spells", query="protect from fire damage", limit=10)` is called
**Then** semantically relevant spells are returned including:
- "Protection from Energy"
- "Fire Shield"
- "Absorb Elements"
**And** each result includes a relevance `_score` field
**And** results are sorted by descending relevance score

#### Scenario: Semantic monster search

**Given** various monster types are indexed
**When** `search_entities("monsters", query="undead creatures that drain life", limit=5)` is called
**Then** relevant undead monsters are returned such as:
- Vampire
- Wraith
- Wight
**And** irrelevant monsters (e.g., beasts, constructs) are excluded

#### Scenario: Semantic equipment search

**Given** weapons and armor are indexed
**When** `search_entities("weapons", query="light weapon for rogues", limit=10)` is called
**Then** relevant light/finesse weapons are returned:
- Dagger
- Shortsword
- Rapier
**And** heavy weapons (greatsword, maul) are not in top results

---

### Requirement: Combined semantic search with structured filters

The system SHALL support combining natural language queries with structured metadata filters.

**Rationale**: Users often need both semantic relevance AND specific criteria (e.g., "healing spells for level 2 clerics").

#### Scenario: Semantic search with level filter

**Given** healing spells at various levels are indexed
**When** `search_entities("spells", query="healing magic", filters={"level": 2}, limit=10)` is called
**Then** only 2nd level healing spells are returned
**And** results are semantically relevant to healing
**And** 1st and 3rd level spells are excluded

#### Scenario: Semantic search with multiple filters

**Given** various spells are indexed
**When** `search_entities("spells", query="combat damage", filters={"level": 3, "school": "Evocation"}, limit=10)` is called
**Then** only 3rd level Evocation spells are returned
**And** results are semantically related to combat and damage
**And** all results match both filter criteria

#### Scenario: Semantic monster search with CR filter

**Given** monsters at various CRs are indexed
**When** `search_entities("monsters", query="dangerous flying creature", filters={"challenge_rating": [5.0, 6.0]}, limit=5)` is called
**Then** only flying monsters with CR 5-6 are returned
**And** results are sorted by semantic relevance to "dangerous"

---

### Requirement: Similarity-based entity discovery

The system SHALL support finding entities similar to a reference entity using its vector embedding.

**Rationale**: Users can discover related items (e.g., "spells like Fireball", "monsters similar to a goblin").

#### Scenario: Find similar spells

**Given** a spell "Fireball" is indexed
**When** `find_similar_entities("spells", reference_slug="fireball", limit=5)` is called
**Then** similar damage-dealing spells are returned:
- Lightning Bolt
- Cone of Cold
- Meteor Swarm
**And** the reference spell "Fireball" is NOT included in results
**And** results are ranked by vector similarity

#### Scenario: Find similar monsters

**Given** a monster "Goblin" is indexed
**When** `find_similar_entities("monsters", reference_slug="goblin", limit=5)` is called
**Then** similar small humanoid monsters are returned:
- Kobold
- Hobgoblin
- Orc
**And** dissimilar monsters (dragon, beholder) are excluded

#### Scenario: Find similar weapons

**Given** a weapon "Longsword" is indexed
**When** `find_similar_entities("weapons", reference_slug="longsword", limit=5)` is called
**Then** similar martial melee weapons are returned:
- Greatsword
- Shortsword
- Scimitar
**And** ranged weapons (bow, crossbow) are not in top results

---

### Requirement: Relevance scoring and ranking

The system SHALL return relevance scores with search results and rank by semantic similarity.

**Rationale**: Users need to understand why results were returned and judge relevance quality.

#### Scenario: Search results include relevance scores

**Given** a semantic search is performed
**When** results are returned
**Then** each result includes a `_score` field
**And** scores are floating-point values between 0 and 1
**And** higher scores indicate greater semantic relevance

#### Scenario: Results sorted by relevance

**Given** a semantic search returns 10 results
**When** examining the result order
**Then** results are sorted in descending order by `_score`
**And** the most relevant result is first
**And** the least relevant result is last

#### Scenario: Low relevance results excluded

**Given** a semantic search with many indexed documents
**When** `search_entities("spells", query="heal wounds", limit=20)` is called
**Then** only relevant healing spells are returned
**And** completely unrelated spells (e.g., teleportation, illusions) are excluded
**And** all returned results have `_score` > 0.3

---

### Requirement: Semantic search pagination

The system SHALL support pagination for semantic search results.

**Rationale**: Large result sets need pagination for performance and usability.

#### Scenario: Limit search results

**Given** 100 spells match a semantic query
**When** `search_entities("spells", query="damage spell", limit=10)` is called
**Then** exactly 10 results are returned
**And** the 10 most relevant results are selected

#### Scenario: Default limit applied

**Given** a semantic search with no limit specified
**When** `search_entities("spells", query="healing")` is called
**Then** the default limit (20) is applied
**And** at most 20 results are returned

---

### Requirement: Multi-field vector embeddings

The system SHALL embed multiple text fields per entity for rich semantic understanding.

**Rationale**: D&D entities have multiple descriptive fields; embedding all relevant text improves search quality.

#### Scenario: Spell description and effects embedded

**Given** a spell with `name`, `desc`, and `higher_level` fields
**When** the spell is indexed
**Then** all three fields are vectorized
**And** searches match content from any embedded field
**And** higher-level effects influence semantic similarity

#### Scenario: Monster abilities embedded

**Given** a monster with `name`, `desc`, `special_abilities`, and `actions` fields
**When** the monster is indexed
**Then** all descriptive fields are vectorized
**And** searches for "paralysis attack" match monsters with paralyzing special abilities

---

### Requirement: Search performance targets

The system SHALL meet performance targets for semantic search operations.

**Rationale**: MCP server must remain responsive; slow searches degrade user experience.

#### Scenario: Semantic search completes quickly

**Given** an index with 2000 entities
**When** `search_entities("spells", query="fire damage", limit=20)` is called
**Then** results are returned in < 100ms
**And** the search includes vector similarity computation
**And** filters (if any) are applied efficiently

#### Scenario: Similarity search is fast

**Given** an index with 500 monsters
**When** `find_similar_entities("monsters", reference_slug="goblin", limit=10)` is called
**Then** results are returned in < 80ms
**And** vector similarity is computed across all documents

---

### Requirement: Semantic search error handling

The system SHALL handle semantic search errors gracefully with appropriate logging and fallbacks.

**Rationale**: Search failures should not crash the system; degrade gracefully to direct API calls.

#### Scenario: Handle invalid entity type

**Given** an invalid entity type "invalid_type"
**When** `search_entities("invalid_type", query="test")` is called
**Then** a `ValueError` is raised
**And** the error message indicates "Invalid entity type"

#### Scenario: Handle empty query

**Given** an empty query string
**When** `search_entities("spells", query="", limit=10)` is called
**Then** results are returned (may be all documents or empty)
**And** no exception is raised

#### Scenario: Handle Marqo search failure

**Given** Marqo service encounters an error during search
**When** `search_entities("spells", query="fireball")` is called
**Then** an error is logged
**And** an appropriate exception is raised with context
**And** the system suggests checking Marqo health

---

## MODIFIED Requirements

### Requirement: Tool functions use semantic search by default

All MCP tool functions (`lookup_spell`, `lookup_creature`, etc.) SHALL use semantic search instead of exact API parameter matching.

**Rationale**: Semantic search provides more relevant results for natural language queries than exact substring matching.

**Previous Behavior**: Tools passed `name` parameter to API as exact/substring match
**New Behavior**: Tools use `search_entities()` for natural language queries

#### Scenario: Spell lookup uses semantic search

**Given** a user calls `lookup_spell(name="protect from fire")`
**When** the tool processes the request
**Then** `search_entities("spells", query="protect from fire")` is called
**And** semantically relevant spells are returned
**And** no direct API call is made for "protect from fire"

#### Scenario: Creature lookup uses semantic search

**Given** a user calls `lookup_creature(name="flying monster")`
**When** the tool processes the request
**Then** `search_entities("monsters", query="flying monster")` is called
**And** flying creatures are returned based on semantic relevance

---

## REMOVED Requirements

None - Semantic search is a new capability.

---

## Cross-References

- Related Spec: `marqo-cache-implementation` - Provides the underlying indexing and storage
- Related Spec: `mcp-tools` - Tools updated to use semantic search

---

## Notes

- Semantic search quality depends on embedding model (hf/e5-base-v2)
- Users can still do exact matches by searching for exact names
- Relevance scores are model-dependent (not absolute measures)
- Complex multi-hop reasoning (e.g., "spells to counter invisibility") may require multiple searches
- Future: Fine-tune embeddings on D&D corpus for better domain specificity
