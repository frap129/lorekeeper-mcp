# Change Proposal: Add Source-Agnostic Document Filtering

## Why

Users need visibility into which source documents their D&D content comes from and the ability to filter content by document. Currently, the system ingests data from multiple sources (Open5e API, D&D 5e API, OrcBrew imports) without providing users any way to discover available documents or filter queries to specific documents. This creates licensing ambiguity and prevents users from controlling which published materials they want to use.

The cache already stores document metadata in the `document` field for all entities, but this information is not exposed to end users through MCP tools.

## What Changes

- **Add document discovery**: New `list_documents()` MCP tool queries cache to show all available documents across all sources
- **Add document filtering to search**: `search_dnd_content()` gains `document_keys` parameter for filtering results
- **Add document filtering to lookup tools**: All lookup tools (`lookup_spell`, `lookup_creature`, etc.) gain `document_keys` parameter
- **Enhance cache queries**: Support filtering by multiple documents (IN clause) in `query_cached_entities()`
- **Add cache discovery functions**: New functions to query distinct documents and document metadata from cache
- **Source-agnostic design**: All operations query the cache layer, completely abstracted from API sources

This is **not a breaking change**. All new parameters are optional and default to existing behavior (no filtering).

## Impact

### Affected Specs
- `entity-cache` - Add document discovery and multi-document filtering functions
- `mcp-tools` - Add document listing tool and document filtering to all search/lookup tools
- `enhanced-search` - Add document filtering capability to search functionality

### Affected Code
- `src/lorekeeper_mcp/cache/db.py` - Add `get_available_documents()` and `get_document_metadata()`, enhance `query_cached_entities()`
- `src/lorekeeper_mcp/tools/` - Add `list_documents.py`, update all lookup/search tools with `document_keys` parameter
- `src/lorekeeper_mcp/repositories/*.py` - Update `search()` methods to accept and pass through `document` parameter as list

### Benefits
- **User control**: Filter content by licensing/preference without knowing which API it came from
- **Transparency**: Discover available documents across all sources
- **Source independence**: Works identically for Open5e, D&D 5e API, OrcBrew, and future sources
- **Future-proof**: Adding new sources requires zero changes to document filtering logic

### Risks
- **Minimal risk**: All changes are additive with optional parameters
- **No schema changes**: Leverages existing `document` field in cache
- **No API dependencies**: All operations query cache, not external APIs
