# Design Document: Source-Agnostic Document Filtering

## Context

The LoreKeeper MCP server aggregates D&D 5e content from three sources:
1. **Open5e API v2**: Community-maintained database with 23+ documents (SRD, Kobold Press, EN Publishing, etc.)
2. **D&D 5e API**: Official SRD content ("System Reference Document 5.1")
3. **OrcBrew imports**: User-imported homebrew content from .orcbrew files

All sources populate the `document` field when caching entities, but users have no way to:
- Discover which documents are available in their cache
- Filter queries to specific documents
- Distinguish content by licensing or source book

## Goals / Non-Goals

### Goals
- Provide source-agnostic document discovery (query cache, not APIs)
- Enable document filtering in all MCP tools
- Support filtering by multiple documents simultaneously
- Work uniformly across all current and future sources
- Require zero code changes when adding new sources

### Non-Goals
- Fetching document metadata from APIs in real-time (use cache only)
- Automatic document filtering based on configuration (user must explicitly pass `document_keys`)
- Document validation (assume document names in cache are correct)
- Rich metadata for non-Open5e sources (D&D 5e API and OrcBrew have minimal metadata)

## Architectural Principles

### Principle 1: Cache-First Architecture
**Decision**: All document operations query the cache, never APIs.

**Rationale**:
- Cache already has `document` field indexed on all 60+ entity types
- Cache is source-agnostic (doesn't know about Open5e vs D&D 5e API vs OrcBrew)
- Eliminates API dependency and network latency
- Works offline once cache is populated

**Alternative considered**: Query APIs for document lists
- ❌ Couples document discovery to API availability
- ❌ Requires API-specific code for each source
- ❌ Can't discover OrcBrew documents (not from API)
- ❌ Adds network latency

### Principle 2: Single Implementation
**Decision**: One code path handles all sources (Open5e, D&D 5e API, OrcBrew, future sources).

**Rationale**:
- Cache schema is uniform across sources
- `document` field stores document name regardless of origin
- `source_api` field tracks origin without affecting filtering logic
- Future sources automatically work without code changes

**Alternative considered**: Source-specific filtering implementations
- ❌ Violates DRY principle
- ❌ Requires updates when adding sources
- ❌ Increases maintenance burden

### Principle 3: Repository Layer Abstraction
**Decision**: Tools call repositories, repositories call cache. Tools never directly query cache or APIs.

**Rationale**:
- Maintains existing architectural layers
- Repositories already handle cache-aside pattern
- Easy to add caching strategies later
- Consistent with current codebase patterns

## Technical Decisions

### Decision 1: Document Discovery via UNION Query

Query all entity type tables for distinct documents:

```sql
SELECT DISTINCT document, source_api
FROM spells WHERE document IS NOT NULL
UNION ALL
SELECT DISTINCT document, source_api
FROM creatures WHERE document IS NOT NULL
UNION ALL
-- ... for all 60+ entity types
```

**Rationale**:
- Single query fetches all documents across all entity types
- No need to maintain separate document registry
- Automatically reflects current cache state
- Simple to implement

**Trade-offs**:
- Slower for large caches (mitigated by indexing on `document` field)
- Can be cached with TTL if performance becomes issue

### Decision 2: Multi-Document Filtering with IN Clause

Enhance `query_cached_entities()` to accept `document` as a list:

```python
document=["srd-5e", "tce", "phb"]  # Multiple documents
# Generates: WHERE document IN (?, ?, ?)
```

**Rationale**:
- Natural SQL pattern for multiple values
- No API changes needed
- Backward compatible (single string still works)

**Alternative considered**: Multiple separate queries
- ❌ Slower (N queries instead of 1)
- ❌ Harder to limit total results

### Decision 3: Optional Document Metadata Enrichment

Store Open5e document metadata in `documents` entity type:

```python
# From Open5e /v2/documents/
{
  "slug": "srd-5e",
  "name": "System Reference Document",
  "publisher": "Wizards of the Coast",
  "license": "OGL-1.0a",
  "game_system": "5e",
  "source_api": "open5e_v2"
}
```

**Rationale**:
- Leverages existing `documents` entity type in cache schema
- Provides rich metadata for Open5e documents
- Optional (document discovery works without it)
- Can be populated on-demand or via background job

**For other sources**:
- D&D 5e API: Hardcode metadata for "System Reference Document 5.1"
- OrcBrew: Minimal metadata (book name only, source="orcbrew")

### Decision 4: Tool Parameter Design

Add `document_keys` parameter (list of strings) to all lookup/search tools:

```python
async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    document_keys: list[str] | None = None,  # NEW
    ...
) -> list[dict[str, Any]]:
```

**Rationale**:
- Consistent naming across all tools
- List type supports single or multiple documents
- Optional parameter (None = no filtering)
- Clear intent (keys not names)

**Alternative considered**: `documents` (plural)
- ❌ Ambiguous (document names or keys?)
- ✅ `document_keys` is explicit

## Implementation Flow

### Document Discovery Flow
```
User → list_documents() MCP tool
  ↓
cache.get_available_documents()
  ↓
UNION query across all entity tables
  ↓
Group by document, source_api
  ↓
Optional: Enrich with cache.get_document_metadata()
  ↓
Return unified list
```

### Document Filtering Flow
```
User → lookup_spell(document_keys=["srd-5e", "tce"])
  ↓
SpellRepository.search(document=["srd-5e", "tce"])
  ↓
cache.query_cached_entities("spells", document=["srd-5e", "tce"])
  ↓
SQL: WHERE document IN (?, ?)
  ↓
Return filtered results
```

## Data Model

### Available Document Structure
```python
{
  "document_name": str,      # Display name
  "document_key": str,       # Normalized slug (if available)
  "source_api": str,         # "open5e_v2" | "dnd5e_api" | "orcbrew"
  "entity_count": int,       # Total entities from this document
  "entity_types": dict[str, int],  # Breakdown by type
  # Optional metadata (from documents cache):
  "publisher": str | None,
  "license": str | None,
  "game_system": str | None
}
```

### Cache Schema (No Changes)
```sql
CREATE TABLE spells (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    source_api TEXT NOT NULL,
    document TEXT,  -- Already exists, indexed
    ...
)
```

## Migration Plan

### Phase 1: Cache Functions (Non-Breaking)
- Add `get_available_documents()` to cache layer
- Add `get_document_metadata()` to cache layer
- Enhance `query_cached_entities()` to support list of documents
- No impact on existing code

### Phase 2: Repository Updates (Non-Breaking)
- Update repositories to accept `document` parameter as list
- Pass through to cache layer
- Backward compatible (None = no filtering)

### Phase 3: Tool Updates (Non-Breaking)
- Add `list_documents()` MCP tool
- Add `document_keys` parameter to all lookup/search tools
- All parameters optional (default behavior unchanged)

### Phase 4: Optional Enhancements
- Background job to cache Open5e document metadata
- Document metadata sync on startup
- Configuration for default document filters (if requested)

## Risks / Trade-offs

### Risk: UNION Query Performance
**Impact**: Querying 60+ tables for distinct documents may be slow on large caches.

**Mitigation**:
- `document` field is already indexed on all tables
- UNION ALL with DISTINCT optimization
- Can add result caching with 1-hour TTL
- Expected <100ms even for large caches

### Risk: Document Name Inconsistency
**Impact**: Different sources may use different names for the same document.

**Mitigation**:
- Document as-is from sources (don't normalize)
- User responsibility to know document names
- `list_documents()` shows exact names to use
- Future: Add document aliases if needed

### Trade-off: No Real-Time API Document Lists
**Chosen**: Query cache only, not APIs.

**Benefits**:
- Faster (no network calls)
- Works offline
- Source-agnostic

**Costs**:
- May not show newest documents until cache populated
- Requires cache to be populated first

**Mitigation**: Document in tool descriptions that discovery shows cached documents only.

## Open Questions

None - design is fully specified.

## Success Criteria

- [ ] User can call `list_documents()` and see all cached documents across all sources
- [ ] User can filter `lookup_spell()` by document and get correct results
- [ ] User can filter `search_dnd_content()` by multiple documents
- [ ] Adding a new source requires zero document filtering code changes
- [ ] All operations complete in <500ms on typical cache sizes
- [ ] No breaking changes to existing tools or APIs
