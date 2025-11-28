# enhanced-search Specification

## Purpose
Defines comprehensive search and filtering capabilities for all MCP tools, including case-insensitive matching, wildcard support, slug fallback, database-level filtering, range operators, and API parameter optimization. This spec consolidates all search-related functionality to ensure consistent, performant, and user-friendly search behavior across spell lookup, creature lookup, equipment lookup, and character option lookup tools.
## Requirements
### Requirement: Enhanced Case-Insensitive Name Filtering
The system SHALL enhance the existing `name` parameter to use case-insensitive matching by default.

#### Scenario: Case-insensitive name search
**Given** a user searches with `name="fireball"`
**When** any lookup tool is invoked
**Then** the system uses `LOWER(name) = LOWER(?)` SQL query
**And** returns "Fireball" spell data regardless of input case

---

### Requirement: Automatic Slug Fallback
The system SHALL automatically attempt slug field search when name search returns no results.

#### Scenario: Automatic slug fallback
**Given** a user searches with `name="fireball"`
**When** the `lookup_spell` tool is invoked and no name match exists
**Then** the system automatically tries `slug = "fireball"`
**And** returns the spell if slug matches
**And** provides fallback behavior transparently to users

---

### Requirement: Wildcard Partial Matching
The system SHALL support partial matching when the `name` parameter contains wildcard characters.

#### Scenario: Explicit wildcard matching
**Given** a user searches with `name="fire*"` or `name="%fire"`
**When** any lookup tool is invoked
**Then** the system detects wildcards in the name parameter
**And** uses `LOWER(name) LIKE LOWER(?)` with processed wildcards
**And** returns partial matches containing "fire"

---

### Requirement: Enhanced Case-Insensitive Default Behavior
The system SHALL change all name filtering from case-sensitive to case-insensitive by default.

**Implementation:**
- Replace `name = ?` with `LOWER(name) = LOWER(?)` SQL queries
- Maintain existing `name` parameter interface unchanged
- Ensure all tools inherit this enhancement automatically

#### Scenario: Case-insensitive default across all tools
**Given** a user searches with `name="fireball"` (any case combination)
**When** any lookup tool is invoked
**Then** the system finds matches regardless of input case
**And** uses efficient case-insensitive SQL queries
**And** provides consistent behavior across all 5 tools

#### Scenario: Enhanced creature lookup with case-insensitivity
**Given** a user searches for `name="ancient red dragon"` (any case)
**When** the `lookup_creature` tool is invoked
**Then** the system returns Ancient Red Dragon data
**And** performs filtering at database level
**And** eliminates the 11x over-fetching performance bug

#### Scenario: Perfect backward compatibility
**Given** existing code uses `name="Fireball"` (proper case)
**When** any lookup tool is invoked
**Then** the system returns identical results as before
**And** adds case-insensitive capability without breaking changes
**And** maintains exact same parameter interface

---

### Requirement: Automatic Slug Fallback Implementation
The system SHALL implement transparent slug fallback when name search returns no results.

**Implementation:**
- First attempt enhanced case-insensitive name search
- If no results, automatically try exact slug match using same input value
- Fallback occurs transparently without user interaction or parameter changes

#### Scenario: Transparent slug fallback for spells
**Given** a user searches with `name="fireball"` and no name match exists
**When** the `lookup_spell` tool is invoked
**Then** the system automatically tries `slug = "fireball"` as fallback
**And** returns spell data using efficient PRIMARY KEY lookup
**And** provides this fallback behavior invisibly to users

#### Scenario: Equipment search with slug fallback
**Given** a user searches with `name="wand of magic missiles"` (exact slug)
**When** the `lookup_equipment` tool is invoked
**Then** name search fails, automatic slug search succeeds
**And** returns equipment item using slug PRIMARY KEY
**And** maintains single-parameter interface

#### Scenario: Performance optimization via fallback
**Given** slug search provides better performance than name search
**When** automatic fallback triggers for exact slug matches
**Then** system leverages PRIMARY KEY index for optimal query performance
**And** reduces query time compared to case-insensitive name matching

---

### Requirement: Wildcard-Based Partial Name Matching
The system SHALL support partial matching when the `name` parameter contains explicit wildcard characters.

**Implementation:**
- Detect `*` or `%` characters in the `name` parameter value
- Convert to `LOWER(name) LIKE LOWER(?)` SQL queries with processed wildcards
- Only perform partial matching when explicitly requested via wildcards

#### Scenario: Explicit wildcard partial matching
**Given** a user searches for `name="fire*"` or `name="%fire"`
**When** any lookup tool is invoked
**Then** the system detects wildcard characters in the parameter
**And** returns partial matches like "Fireball", "Fire Bolt", "Wall of Fire"
**And** uses efficient `LOWER(name) LIKE LOWER(?)` database queries
**And** respects the `limit` parameter

#### Scenario: Equipment partial search with wildcards
**Given** a user searches for `name="*sword*"` with `limit=5`
**When** the `lookup_equipment` tool is invoked
**Then** the system processes wildcards for partial matching
**And** returns up to 5 equipment items containing "sword"
**And** includes "Longsword", "Shortsword", "Greatsword", "Flame Tongue", "Frost Brand"
**And** performs all filtering at database level

#### Scenario: No wildcard means exact matching
**Given** a user searches for `name="Fireball"` (no wildcards)
**When** the `lookup_spell` tool is invoked
**Then** the system performs case-insensitive exact matching only
**And** returns only "Fireball" spell if found
**And** does not perform partial matching unless wildcards present

#### Scenario: Wildcard search with no results
**Given** a user searches for `name="xyz123*"`
**When** any lookup tool is invoked
**Then** the system performs partial match query efficiently
**And** returns empty result list without error
**And** query executes with proper indexing

---

### Requirement: Database-Level Filtering Performance
The system SHALL perform all filtering operations at the database level to eliminate client-side filtering and reduce data transfer.

**Implementation:**
- Remove all client-side filtering from affected tools
- Ensure database queries include all filter criteria
- Optimize SQL queries with proper indexes

#### Scenario: Efficient creature filtering
**Given** a user searches `lookup_creature(name="dragon", cr=10, limit=20)`
**When** the tool is invoked
**Then** the system builds a single SQL query with all WHERE conditions
**And** the database returns exactly matching results (not 220 items)
**And** memory usage is proportional to actual results (20 items max)
**And** network transfer is minimized

#### Scenario: Equipment search with multiple filters
**Given** a user searches `lookup_equipment(type="weapon", name="sword", limit=15)`
**When** the tool is invoked
**Then** the system performs filtering at database level
**And** does not fetch all weapons then filter client-side
**And** query performance uses indexes effectively
**And** response time is under 100ms for typical queries

#### Scenario: Performance comparison validation
**Given** the enhanced filtering is implemented
**When** comparing before/after performance metrics
**Then** database queries return exactly `limit` results (not `limit * 11`)
**And** memory usage reduction is 90% or more for filtered queries
**And** query execution time improves by factor of 5 or more
**And** client CPU usage for filtering is eliminated

---

### Requirement: Consistent Enhanced Tool Interface
The system SHALL provide consistent enhanced search behavior across all MCP tools using unchanged existing parameters.

**Implementation:**
- All tools maintain exact existing parameter interface: `name`, `limit`, plus tool-specific filters
- The existing `name` parameter is enhanced with case-insensitive, wildcard, and slug fallback behavior
- Tools preserve their specific parameters (e.g., `level` for spells, `cr` for creatures)
- Enhanced behavior applies automatically without parameter changes

#### Scenario: Identical interface across all tools
**Given** examining the parameter definitions for all 5 tools
**When** checking tool interfaces
**Then** all tools have exactly the same parameters as before
**And** each tool maintains its domain-specific parameters unchanged
**And** parameter types and defaults remain identical
**And** FastMCP parameter validation works as before

#### Scenario: Enhanced behavior with existing parameters
**Given** a user searches `lookup_spell(name="fire", level=3, school="evocation")`
**When** the spell tool is invoked
**Then** the system uses enhanced case-insensitive matching for "fire"
**And** combines with spell-specific filters (level=3, school="evocation")
**And** performs efficient database query with all conditions
**And** respects the `limit` parameter without over-fetching

#### Scenario: Unchanged parameter validation
**Given** invalid parameters provided to any tool
**When** the tool is invoked
**Then** FastMCP validation behaves exactly as before
**And** error messages remain consistent and user-friendly
**And** error handling follows the same pattern for all tools
**And** no new validation rules are introduced

---

### Requirement: Perfect Backward Compatibility
The system SHALL maintain 100% backward compatibility with all existing tool parameters and behavior.

**Implementation:**
- All existing parameters work exactly as before
- All existing parameter types and defaults remain unchanged
- Enhanced behavior is transparent and automatic
- No existing integrations require changes

#### Scenario: Identical behavior for existing calls
**Given** existing code uses `lookup_spell(name="Fireball", level=3)`
**When** the tool is invoked
**Then** the system returns exactly the same results as before
**And** adds case-insensitive capability transparently
**And** maintains exact same parameter interface
**And** performs filtering efficiently at database level

#### Scenario: Unchanged limit parameter behavior
**Given** existing code uses `lookup_creature(limit=20)` without name filters
**When** the tool is invoked
**Then** the system returns exactly 20 creatures as expected
**And** maintains the same ordering behavior
**And** performance is improved without changing results
**And** response format remains identical

#### Scenario: Enhanced capability with existing parameters
**Given** a user searches `lookup_spell(name="fire", level=3, school="evocation", limit=10)`
**When** the tool is invoked
**Then** the system uses enhanced case-insensitive matching for "fire"
**And** combines with spell-specific filters (level=3, school="evocation)
**And** performs efficient database query with all conditions
**And** respects the limit parameter without the 11x over-fetching bug

#### Scenario: Zero impact on existing integrations
**Given** existing client code or MCP clients
**When** using current tool interfaces
**Then** all existing functionality works unchanged
**And** no API or interface changes are required
**And** enhanced features work automatically without awareness

---

### Requirement: SQL Security and Parameter Binding
The system SHALL use proper SQL parameter binding for all user input to prevent SQL injection attacks.

**Implementation:**
- All user input uses parameterized queries with `?` placeholders
- No string concatenation of user input in SQL queries
- Input validation and sanitization for special characters

#### Scenario: Safe parameter binding for names
**Given** a user searches for `name="Robert'; DROP TABLE spells; --"`
**When** any lookup tool is invoked
**Then** the system uses parameterized query `LOWER(name) = LOWER(?)`
**And** the malicious input is treated as a literal string value
**And** no SQL injection is possible
**And** query executes safely with no matches found

#### Scenario: Safe LIKE query handling
**Given** a user searches for `name="%; DROP TABLE creatures; --"`
**When** any lookup tool is invoked
**Then** the system safely escapes LIKE wildcards
**And** uses parameter binding `LOWER(name) LIKE LOWER(?)`
**And** SQL injection is prevented
**And** query executes safely

#### Scenario: Input validation and sanitization
**Given** extremely long input strings or special characters
**When** any lookup tool is invoked
**Then** the system validates input length limits
**And** escapes or rejects dangerous characters
**And** provides appropriate error messages for invalid input
**And** maintains database security while allowing valid searches

---

### Requirement: Document-Based Search Filtering

The unified search functionality SHALL support filtering search results by source document, now leveraging Milvus Lite's native filtering capabilities.

#### Scenario: Filter search results by single document
- **GIVEN** the search index contains content from multiple documents
- **WHEN** a search is performed with document filter for a single document
- **THEN** only results from that document are included in search results
- **AND** results from other documents are excluded
- **AND** search relevance scoring is unaffected by document filtering
- **AND** filtering is performed at the database level using Milvus filter expressions

#### Scenario: Filter search results by multiple documents
- **GIVEN** the search index contains content from multiple documents
- **WHEN** a search is performed with document filter for multiple documents
- **THEN** results from all specified documents are included
- **AND** results from other documents are excluded
- **AND** results maintain relevance order across all included documents
- **AND** Milvus IN clause is used for efficient multi-document filtering

#### Scenario: Semantic search with document filter
- **GIVEN** the cache contains entities from multiple documents
- **WHEN** a semantic search is performed with query "fire magic" and documents=["srd-5e"]
- **THEN** vector similarity search is combined with document filter
- **AND** only entities from "srd-5e" with high semantic similarity are returned
- **AND** filtering and ranking occur in a single Milvus query

### Requirement: Document Filter Performance Optimization

Document filtering SHALL be optimized to minimize performance impact on search operations, leveraging Milvus Lite's native filtering.

#### Scenario: Database-level document filtering
- **GIVEN** search results need to be filtered by document
- **WHEN** filtering is applied
- **THEN** document filter is applied at the Milvus query level
- **AND** filter expression uses indexed document field
- **AND** no post-filtering is required (filtering occurs during vector search)
- **AND** filtering completes in <50ms for typical result sets

#### Scenario: Early termination for empty document list
- **GIVEN** a search is requested with an empty document_keys list
- **WHEN** the search function receives document_keys=[]
- **THEN** an empty result list is returned immediately
- **AND** no Milvus query is executed (short-circuit optimization)

### Requirement: Range Filtering Operators
API clients SHALL utilize range filtering operators (`__gte`, `__lte`, `__gt`, `__lt`) for numeric fields where available.

**Rationale**: Open5e v2 supports range operators for numeric fields like level, challenge rating, cost, weight, armor class, ability scores, etc. These enable precise server-side range queries.

#### Scenario: Spell level range filtering
- **Given**: User searches for spells of levels 2-4
- **When**: Open5e v2 API request is made with level_min=2, level_max=4
- **Then**: Request includes `?level__gte=2&level__lte=4`
- **And**: API returns only spells within specified range
- **And**: No client-side filtering is needed

#### Scenario: Challenge rating range filtering
- **Given**: User searches for monsters with CR 1-3
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?challenge_rating_decimal__gte=1&challenge_rating_decimal__lte=3`
- **And**: API returns only monsters within CR range
- **And**: Filtering is performed server-side

#### Scenario: Cost and weight range filtering
- **Given**: User searches for equipment costing 10-100gp weighing under 5lbs
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?cost__gte=10&cost__lte=100&weight__lte=5`
- **And**: API returns only equipment matching all criteria
- **And**: Efficient server-side filtering

---

### Requirement: Boolean Filtering
API clients SHALL utilize boolean filters for properties where available.

**Rationale**: Open5e v2 provides boolean filters for equipment and spell properties that enable precise filtering.

#### Scenario: Boolean equipment property filters
- **Given**: User searches for finesse, light weapons
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?is_finesse=true&is_light=true`
- **And**: API returns only weapons matching both properties
- **And**: Efficient server-side filtering replaces client-side logic

#### Scenario: Boolean spell property filters
- **Given**: User searches for concentration spells that are also rituals
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?concentration=true&ritual=true`
- **And**: API returns only spells matching both criteria

#### Scenario: Magic item filtering
- **Given**: User searches for magic items requiring attunement
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?is_magic_item=true&requires_attunement=true`
- **And**: API returns only attuned magic items

---

### Requirement: Multi-Value Filtering
API clients SHALL support array/multi-value parameters for filters accepting multiple values.

**Rationale**: Both APIs support filtering by multiple values efficiently in a single request.

#### Scenario: Multiple spell levels via D&D API
- **Given**: User searches for spells of levels 1, 2, and 3
- **When**: D&D 5e API request uses multi-value filter
- **Then**: Request includes `?level=1,2,3`
- **And**: API returns spells from all specified levels
- **And**: Single API call instead of three separate requests

#### Scenario: Multiple spell schools via Open5e
- **Given**: User searches for evocation and illusion spells
- **When**: Open5e v2 API request uses in operator
- **Then**: Request includes `?school__in=evocation,illusion` or `?school=evocation,illusion`
- **And**: API returns spells from both schools
- **And**: Results are efficiently filtered server-side

#### Scenario: Multiple creature types
- **Given**: User searches for dragon and undead creatures
- **When**: Open5e v2 API request is made
- **Then**: Request uses appropriate multi-value type filter
- **And**: API returns creatures matching any specified type

---

### Requirement: Entity-Specific Specialized Filters
API clients SHALL implement entity-specific filters that provide more precise search capabilities.

**Rationale**: Different entity types have specialized filters (e.g., spell casting time, weapon damage type, creature ability scores) that enable precise searches.

#### Scenario: Specialized spell filtering
- **Given**: User searches for 1-action spells of level 3+ in evocation school with fire damage
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?casting_time=1 action&level__gte=3&school__key=evocation&damage_type=fire`
- **And**: API returns spells matching all criteria
- **And**: Results are precisely filtered server-side

#### Scenario: Specialized equipment filtering
- **Given**: User searches for rare magic weapons that are finesse and don't require attunement
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?is_magic_item=true&is_weapon=true&is_finesse=true&rarity=rare&requires_attunement=false`
- **And**: API returns only equipment matching all criteria

#### Scenario: Specialized creature filtering
- **Given**: User searches for large creatures with high strength (16+) and low intelligence (<10)
- **When**: Open5e v2 API request is made
- **Then**: Request includes `?size=large&ability_score_strength__gte=16&ability_score_intelligence__lt=10`
- **And**: API returns creatures matching both criteria

---

### Requirement: Open5e v2 Filter Operators
Open5e v2 API clients SHALL use proper Django-style filter operators (`name__icontains`, `school__key`, `level__gte`, etc.) for server-side filtering on individual endpoints.

**Rationale**: Open5e v2 uses Django REST framework filter operators. Using `name__icontains` provides case-insensitive partial matching server-side. Currently, the code fetches all records and filters client-side, which is inefficient.

#### Scenario: Server-side partial name matching
- **Given**: User searches for spells with name="fire"
- **When**: Open5e v2 client makes API request
- **Then**: Request includes `?name__icontains=fire` parameter
- **And**: API returns only spells containing "fire" in name
- **And**: No client-side filtering is needed

#### Scenario: Server-side school filtering
- **Given**: User searches for evocation spells
- **When**: Open5e v2 client makes API request
- **Then**: Request includes `?school__key=evocation` parameter
- **And**: API returns only evocation spells server-side
- **And**: No client-side school filtering is performed

---

### Requirement: Search Parameter Standardization
All Open5e API tools SHALL use the correct `search` parameter for name-based text searches instead of the incorrect `name` parameter.

**Rationale**: The Open5e API (both v1 and v2) expects `search` as the query parameter for text-based name searches. The current implementation uses `name`, which causes all name-based searches to return zero results.

#### Scenario: Spell lookup search parameter
- **Given**: User calls `lookup_spell(name="fireball")`
- **When**: Tool makes API request to Open5e v2 `/spells/` endpoint
- **Then**: API request includes `?search=fireball` parameter
- **And**: Response contains fireball-related spells (non-zero result count)

#### Scenario: Creature lookup search parameter
- **Given**: User calls `lookup_creature(name="dragon")`
- **When**: Tool makes API request to Open5e v1 `/monsters/` endpoint
- **Then**: API request includes `?search=dragon` parameter
- **And**: Response contains dragon-related creatures (non-zero result count)

#### Scenario: Equipment lookup search parameter
- **Given**: User calls `lookup_equipment(type="weapon", name="longsword")`
- **When**: Tool makes API request to Open5e v2 `/weapons/` endpoint
- **Then**: API request includes `?search=longsword` parameter
- **And**: Response contains longsword-related weapons (non-zero result count)

#### Scenario: Character option lookup search parameter
- **Given**: User calls `lookup_character_option(type="class", name="wizard")`
- **When**: Tool makes API request to Open5e API for classes
- **Then**: API request includes `?search=wizard` parameter
- **And**: Response contains wizard class information (non-zero result count)

---

### Requirement: Unified Search Endpoint
The search system SHALL use the `/v2/search/` endpoint with `query`, `fuzzy`, and `vector` parameters for advanced cross-entity searches.

**Rationale**: The `/v2/search/` endpoint provides unified search across all content types with built-in fuzzy and semantic search capabilities.

#### Scenario: Unified search with fuzzy and semantic matching
- **Given**: User performs advanced search for "firbal" (typo)
- **When**: Request is made to `/v2/search/?query=firbal&fuzzy=true&vector=true`
- **Then**: API returns "Fireball" spell via fuzzy matching
- **And**: May include semantically related fire spells via vector search
- **And**: Results are deduplicated and ranked by relevance

#### Scenario: Cross-entity search
- **Given**: User searches for "dragon" without specifying entity type
- **When**: Unified search is used with `/v2/search/?query=dragon&fuzzy=true&vector=true`
- **Then**: Results include dragon creatures, dragon-themed spells, dragon-related items
- **And**: Results span multiple content types
- **And**: All results relevant to "dragon"

#### Scenario: Entity-specific unified search
- **Given**: User searches for "fire" limited to spells
- **When**: Request uses `/v2/search/?query=fire&fuzzy=true&vector=true&object_model=Spell`
- **Then**: Results include only spell entities
- **And**: Fuzzy and semantic matching still applied
- **And**: Type filter works with advanced search

### Requirement: Local Semantic Search with Milvus Lite

The system SHALL provide semantic/vector search capabilities using Milvus Lite as an embedded vector database, enabling natural language similarity queries without requiring external services.

#### Scenario: Semantic search for spells by description
**Given** the cache contains spells "Fireball", "Fire Shield", "Ice Storm"
**When** a semantic search is performed with query "protect from fire damage"
**Then** "Fire Shield" is ranked higher than "Ice Storm"
**And** results are ordered by semantic similarity score descending
**And** no external services are required (fully local)

#### Scenario: Semantic search combined with structured filters
**Given** the cache contains spells at various levels and schools
**When** a semantic search is performed with query "fire damage" and filters level=3, school="Evocation"
**Then** only level 3 Evocation spells are searched
**And** results are ranked by semantic similarity within the filtered set
**And** structured filters are applied before vector search for efficiency

#### Scenario: Semantic search for creatures by concept
**Given** the cache contains creatures "Ancient Red Dragon", "Fire Elemental", "Ice Devil"
**When** a semantic search is performed with query "fire breathing monster"
**Then** "Ancient Red Dragon" and "Fire Elemental" rank higher than "Ice Devil"
**And** results capture semantic meaning beyond keyword matching

#### Scenario: Semantic search fallback on empty query
**Given** the cache contains entities
**When** a semantic search is performed with an empty query string
**Then** the system falls back to structured retrieval
**And** returns entities without semantic ranking
**And** any provided filters are still applied

### Requirement: Embedding Generation for Search

The system SHALL automatically generate vector embeddings for searchable content using a local embedding model.

#### Scenario: Automatic embedding on entity storage
**Given** a spell entity with name "Fireball" and description "A bright streak flashes..."
**When** the entity is stored in the cache
**Then** searchable text is extracted from name, description, and relevant fields
**And** a 384-dimensional embedding vector is generated using all-MiniLM-L6-v2
**And** both the entity data and embedding are stored together

#### Scenario: Lazy loading of embedding model
**Given** a newly initialized cache
**When** no store or semantic search operations have been performed
**Then** the embedding model is not loaded into memory
**When** the first semantic operation is performed
**Then** the model (~80MB) is downloaded if not cached locally
**And** the model is loaded and reused for subsequent operations

#### Scenario: Entity-type-specific text extraction
**Given** entities of different types (spells, creatures, equipment)
**When** generating embeddings for each entity type
**Then** spell embeddings include name, description, and higher_level text
**And** creature embeddings include name, description, type, and ability names
**And** equipment embeddings include name, description, and properties
**And** irrelevant mechanical data (pure numbers) is excluded from embedding text

### Requirement: Hybrid Search Strategy

The system SHALL support hybrid search combining vector similarity with structured filters for optimal search results.

#### Scenario: Hybrid search with document filter
**Given** the cache contains spells from documents "srd-5e" and "tce"
**When** a semantic search is performed with query "healing magic" and document filter "srd-5e"
**Then** only spells from "srd-5e" are included in the vector search
**And** semantic ranking is applied within the document-filtered set
**And** results from "tce" are excluded regardless of semantic similarity

#### Scenario: Hybrid search performance
**Given** a cache with ~10,000 entities
**When** performing hybrid search with filters and semantic query
**Then** query completes in < 100ms
**And** structured filters reduce the search space before vector similarity
**And** results have reasonable recall (>80% of relevant items in top 20)

#### Scenario: Pure structured search without semantics
**Given** the cache supports semantic search
**When** a query is performed without a semantic query parameter
**Then** the system performs structured filtering only
**And** no embedding generation or vector search occurs
**And** behavior is identical to pre-Milvus implementation (backward compatible)

#### Scenario: Similarity score in results
**Given** a semantic search is performed
**When** results are returned
**Then** each result includes a `similarity_score` field (0.0 to 1.0)
**And** results are ordered by similarity_score descending
**And** higher scores indicate greater semantic similarity

#### Scenario: Query text normalization
**Given** a semantic search query with extra whitespace or punctuation
**When** generating the query embedding
**Then** the query text is normalized (trimmed, lowercased)
**And** embedding quality is consistent regardless of query formatting
