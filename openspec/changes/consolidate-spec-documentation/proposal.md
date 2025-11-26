## Why

The specification directory contains 28 spec files, many of which are fragmented, incomplete, or have overlapping coverage. Several specs have "TBD" in their purpose section (created via archiving changes without proper consolidation) and there are clear groupings that should be merged:

1. **API Client Specs**: `dnd5e-api-client` + `complete-dnd5e-client`, `open5e-v1-client` + `complete-open5e-v1-client`, `open5e-v2-client` + `complete-open5e-v2-client`
2. **Search/Filter Specs**: `enhanced-search`, `filter-enhancement`, `search-parameter-correction` overlap significantly
3. **Obsolete Specs**: `spell-school-filtering`, `weapon-model-correction` are narrow fixes that should be absorbed into their parent specs

This fragmentation makes it difficult to understand the full requirements for any given component and leads to specification drift where requirements in one spec may contradict those in another.

## What Changes

- **MERGE** API client specs into single comprehensive specs per client
- **MERGE** search-related specs into `enhanced-search`
- **ARCHIVE** narrow fix specs into their parent specs
- **UPDATE** all "TBD" purpose sections with clear descriptions
- **STANDARDIZE** spec format with consistent structure

## Impact

- Affected specs: 12 specs will be merged/consolidated into ~6 comprehensive specs
- No code changes required - documentation consolidation only
- Improves developer experience and reduces confusion
