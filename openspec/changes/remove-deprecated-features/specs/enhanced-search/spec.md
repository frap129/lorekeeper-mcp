## MODIFIED Requirements

### Requirement: Hybrid Search Architecture

All search functionality SHALL support both semantic/vector search AND structured filtering. Users can use either approach independently or combine them for hybrid search.

#### Scenario: Search with semantic query only
- **WHEN** calling `search_all(query="fire dragon")`
- **THEN** the system performs vector similarity search
- **AND** returns results ranked by semantic similarity
- **AND** all entity types are searched

#### Scenario: Repository search with semantic query
- **WHEN** calling `repository.search(semantic_query="healing spell")`
- **THEN** the system performs semantic search against embeddings
- **AND** results are ranked by vector similarity

#### Scenario: Repository search with structured filters
- **WHEN** calling `repository.search(level=3, school="evocation")`
- **THEN** the system performs structured filtering at the database level
- **AND** results match the exact criteria specified
- **AND** no semantic ranking is applied

#### Scenario: Repository search with hybrid approach
- **WHEN** calling `repository.search(semantic_query="fire damage", level=3, school="evocation")`
- **THEN** the system combines semantic search with structured filtering
- **AND** structured filters narrow the search space
- **AND** results are ranked by semantic similarity within the filtered set

---

## REMOVED Requirements

### Requirement: Fuzzy Search Toggle

**Reason**: Fuzzy search is deprecated. Semantic search provides superior typo tolerance through embeddings. The `fuzzy` and `enable_fuzzy` parameters added complexity without significant benefit over semantic search.

**Migration**: Remove all fuzzy search parameter usage. Semantic search handles variations naturally.

#### Scenario: Fuzzy search toggle no longer available
- **GIVEN** code using `search_all(query="firbal", enable_fuzzy=True)`
- **WHEN** the function is invoked
- **THEN** a `TypeError` is raised for unexpected keyword argument
- **AND** semantic search handles typos through embedding similarity

---

### Requirement: Semantic Search Toggle

**Reason**: Semantic search is always enabled for `search_all`. The `semantic` and `enable_semantic` parameters are removed because there is no alternative search mode for the unified search tool.

**Migration**: Remove `semantic` and `enable_semantic` parameter usage from `search_all()`.

#### Scenario: Semantic toggle no longer available
- **GIVEN** code using `search_all(query="fireball", semantic=False)`
- **WHEN** the function is invoked
- **THEN** a `TypeError` is raised for unexpected keyword argument
- **AND** semantic search is always used
