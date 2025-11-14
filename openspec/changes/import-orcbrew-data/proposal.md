# import-orcbrew-data Change Proposal

## Summary
Add CLI command to parse .orcbrew files and import D&D content into the LoreKeeper cache. OrcBrew files are a standard EDN/Clojure format used by OrcPub and DungeonMastersVault for exporting and importing D&D 5e game data.

## Why
- **Enable offline data**: Users can import comprehensive D&D content directly from .orcbrew files without relying solely on API calls
- **Reduce API load**: Pre-populate cache with data from homebrew and third-party sources
- **Support custom content**: Allow users to import custom/homebrew content packaged in the OrcBrew format
- **Faster startup**: Enable pre-caching of frequently used data before running the MCP server

## What Changes

### New Capabilities
1. **CLI Interface** - Command-line tool for LoreKeeper operations
2. **OrcBrew Parser** - Parser for EDN/Clojure formatted .orcbrew files
3. **Batch Import** - Import hundreds/thousands of entities at once

### Modified Capabilities
1. **Entity Cache** - Enhanced to track import source ("orcbrew" vs API data)

## Impact

**Positive**:
- Users can import large content packs (like the 43,000+ line MegaPak file) into their local cache
- Reduced dependency on external APIs for frequently accessed data
- Support for homebrew and custom content not available via APIs
- Faster response times for cached content

**Negative**:
- Minimal - this is an additive feature that doesn't affect existing functionality
- Adds two new dependencies (EDN parser and CLI framework)

## Scope
This change introduces:
1. **New CLI interface** - Command-line tool for data import operations
2. **OrcBrew parser** - Parser for EDN/Clojure formatted .orcbrew files
3. **Modified entity cache** - Enhanced to handle batch imports and map OrcBrew entity types

## Related Work
- Depends on: `entity-cache` spec (existing)
- Enables: Future CLI commands for cache management and data operations

## Implementation Approach
1. Add CLI framework (Click) for command-line interface
2. Implement EDN parser using Python's `edn_format` library
3. Create entity type mapper to convert OrcBrew types to LoreKeeper types
4. Build batch import functionality using existing cache APIs
5. Add progress reporting and error handling

## Open Questions
1. **Entity type mapping**: How should we handle OrcBrew entity types not yet supported in LoreKeeper's cache schema?
   - Proposed: Log warnings and skip unsupported types initially, add support incrementally

2. **Data conflicts**: What happens when imported data conflicts with API-fetched data?
   - Proposed: Source priority system: API data > OrcBrew data (API is canonical), but allow flag to override

3. **Validation**: Should we validate imported data against schemas?
   - Proposed: Basic validation (required fields), log warnings for malformed entries, continue import

4. **Duplicate handling**: How to handle duplicate slugs?
   - Proposed: Use "last write wins" strategy, log duplicates for user review

## Alternatives Considered
1. **Web UI for imports** - Rejected: CLI is simpler and fits developer workflow better
2. **Auto-detection of .orcbrew files** - Rejected: Explicit commands provide better control
3. **JSON conversion tool** - Rejected: Direct EDN parsing is more maintainable

## Dependencies
- Python library: `edn-format` (for parsing EDN/Clojure data)
- Python library: `click` (for CLI framework)

## Success Metrics
- Successfully parse the 43K+ line MegaPak file
- Import time: < 30 seconds for MegaPak file
- Zero data corruption in cache
- Clear error messages for malformed files
- 100% test coverage for parser and CLI

## Timeline
Estimated: 2-3 days
- Day 1: CLI framework and basic parser
- Day 2: Entity mapping and cache integration
- Day 3: Testing, error handling, documentation
