# Change Proposal: List and Filter Open5e Documents

## Overview
Implement functionality to list all available source documents from the Open5e API and allow users to control which documents are used when the server parses and caches game data. This enables users to customize the content available in their MCP server instance based on their licensing and preferences.

## Motivation
Currently, the MCP server ingests data from the Open5e API without visibility into or control over the source documents. The Open5e API v2 exposes a `/documents/` endpoint that provides metadata about available source books and licensed content from various publishers (e.g., EN Publishing, Kobold Press, Wizard's of the Coast, etc.), but this information is not surfaced to users.

Key issues:
1. **No Visibility**: Users cannot see what documents/source books their data comes from
2. **No Control**: Users cannot filter or exclude specific documents based on licensing or preference
3. **Incomplete Information**: Server logs and documentation don't indicate which documents are available or in use
4. **Feature Incompleteness**: The Open5e v2 API client has a `get_documents()` method but it's not exposed anywhere

## Goals
1. **Document Discovery**: Provide a CLI command to list all available documents from the Open5e API
2. **Document Filtering**: Add configuration options to control which documents are included when the server runs
3. **User Transparency**: Make document selection visible and auditable
4. **Extensibility**: Design the solution to support filtering API results by document in future enhancements

## Success Criteria
- [ ] CLI command exists to list all available documents with metadata (name, publisher, license, description)
- [ ] Configuration option added to specify included/excluded documents
- [ ] Document list command shows document keys that can be used in configuration
- [ ] Configuration properly validates selected document keys
- [ ] Server startup logs indicate which documents are configured
- [ ] No breaking changes to existing configuration or CLI behavior
- [ ] Documentation explains how to use the new features

## Impact Assessment

### Benefits
- **User Control**: Users can customize content based on licensing and preferences
- **Transparency**: Clear visibility into data sources and available documents
- **Compliance**: Easier to honor licensing restrictions or selective content inclusion
- **Extensibility**: Foundation for future filtering of API results by document

### Risks
- **None identified**: This is purely additive functionality with no impact on existing behavior

### Implementation Scope
- Minimal: Phase 1 focuses on listing and configuration only
- Document filtering of API results deferred to Phase 2 (future enhancement)
- No changes needed to existing tool interfaces or repositories

## Out of Scope (Phase 2)
- Actually filtering API results to only include items from selected documents
- Caching strategy changes based on document selection
- Document-level content syncing or offline availability
