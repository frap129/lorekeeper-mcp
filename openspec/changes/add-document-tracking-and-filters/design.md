## Context
LoreKeeper already has:
- Open5e v2 document support and listing (`get_documents()` in the complete Open5e v2 client, plus the `list-open5e-documents` change for discovery and configuration).
- An entity cache that stores normalized entities with indexed fields for filtering.
- Repositories and MCP tools that aggregate data across sources (Open5e v1/v2, D&D 5e API, OrcBrew) and expose filtering options.
- A requirement for source attribution in tool responses, but without a fully standardized, queryable `document` field across all entities.

The user wants LoreKeeper to track which document every item comes from and allow filtering by document name. Open5e provides explicit document objects with names (e.g., "System Reference Document 5.1", "Adventurer's Guide", "Tome of Beasts"), the D&D 5e API provides SRD content (which maps to "System Reference Document 5.1"), and OrcBrew uses the top-level book name as the document.

## Goals / Non-Goals
- Goals:
  - Store document name for all entities (Open5e v2 document name, D&D 5e SRD as "System Reference Document 5.1", OrcBrew book name).
  - Store document name in the entity cache so repositories and tools can query/filter by document without extra API calls.
  - Allow repositories and tools to filter results by document name while preserving existing filter behavior and limits.
  - Keep the solution compatible with existing `list-open5e-documents` configuration for included/excluded documents.
- Non-Goals:
  - Implement a full document hierarchy or collections model beyond what Open5e and OrcBrew already expose.
  - Change existing MCP tool parameters in a breaking way.
  - Implement UI/UX beyond CLI and MCP surfaces already covered by other specs.
  - Expose API source (`source_api`) as a user-facing filter (it remains internal tracking only).

## Decisions
- Store document name as a single indexed field: `document TEXT`
  - Open5e v2: Extract from `document.name` field (e.g., "System Reference Document 5.1", "Adventurer's Guide")
  - D&D 5e API: Normalize all content to "System Reference Document 5.1" (same as Open5e's SRD)
  - OrcBrew: Extract from top-level book name or `option-pack` field
- Keep existing `source_api` field for internal tracking (which API provided the data), but do NOT expose it as a user-facing filter
- Store document name in the entity cache as an indexed column so document-based filters can be applied at the database level (no client-side filtering).
- Treat the existing document inclusion/exclusion configuration from `list-open5e-documents` as a global filter layer that can constrain repositories and tools; per-call document filters will be additive and intersect with global configuration.
- Users filter by document name only - they don't care which API LoreKeeper used internally.

## Risks / Trade-offs
- Risk: Incomplete or inconsistent document metadata from upstream sources (e.g., older Open5e v1 endpoints, some OrcBrew files without clear book names) could lead to partial document coverage.
  - Mitigation: Define clear defaults (e.g., `document="Unknown"`) and ensure filters behave predictably when document data is missing.
- Risk: Adding document field as an indexed column requires schema changes in the entity cache.
  - Mitigation: Scope schema changes narrowly and keep migration logic simple, leveraging existing migration patterns.
- Risk: Overcomplicating MCP tool parameters with too many document-related options.
  - Mitigation: Expose only one document filter parameter (`document`) that accepts the document name.

## Migration Plan
- Add document name field to the entity normalization layer first, then extend cache schema and repositories.
- Provide a lightweight migration or background refresh path to populate document names for already cached entities when feasible.
- Roll out repository-level document filters behind additive parameters and configuration; keep existing behavior as the default when no document filters are provided.
- Update documentation and examples (e.g., how to request SRD-only data, how to target specific Open5e documents or OrcBrew books).

## Open Questions
- Should document filters be exposed on all tools uniformly (e.g., a `document` parameter everywhere), or only on tools where document granularity is most valuable (spells, creatures, equipment, character options, rules)?
- Both Open5e and D&D 5e API provide SRD content under the same document name "System Reference Document 5.1" - is this the correct normalization?
