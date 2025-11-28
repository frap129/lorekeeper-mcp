## Why

The specification directory contains 26 spec files, all of which have "TBD" in their purpose section (created via archiving changes without proper consolidation). There are also clear groupings that should be merged:

1. **API Client Specs**: `open5e-v1-client` + `complete-open5e-v1-client`, `open5e-v2-client` + `complete-open5e-v2-client` (D&D 5e API specs were removed in `remove-dnd5e-api-client`)
2. **Search/Filter Specs**: `enhanced-search`, `filter-enhancement`, `search-parameter-correction`, `api-parameter-usage` overlap significantly
3. **Narrow Fix Specs**: `spell-school-filtering`, `weapon-model-correction` are narrow fixes that should be absorbed into parent specs
4. **Repository Specs**: `tool-repository-migration` could be absorbed into `repository-infrastructure`
5. **MCP Specs**: `mcp-tool-cleanup` could be absorbed into `mcp-tools`

This fragmentation makes it difficult to understand the full requirements for any given component and leads to specification drift where requirements in one spec may contradict those in another.

## What Changes

- **MERGE** Open5e v1 client specs into single comprehensive spec
- **MERGE** Open5e v2 client specs into single comprehensive spec
- **MERGE** search-related specs (`filter-enhancement`, `search-parameter-correction`, `api-parameter-usage`) into `enhanced-search`
- **ABSORB** narrow fix specs into parent specs
- **ABSORB** `tool-repository-migration` into `repository-infrastructure`
- **ABSORB** `mcp-tool-cleanup` into `mcp-tools`
- **UPDATE** all 26 "TBD" purpose sections with clear descriptions
- **STANDARDIZE** spec format with consistent structure

## Impact

- Affected specs: 26 specs reduced to ~16-18 comprehensive specs
- No code changes required - documentation consolidation only
- All specs will have meaningful purpose sections
- Improves developer experience and reduces confusion
