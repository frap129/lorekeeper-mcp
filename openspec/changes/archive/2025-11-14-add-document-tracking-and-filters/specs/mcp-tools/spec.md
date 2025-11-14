## ADDED Requirements

### Requirement: Document-Aware Tool Filtering
The system SHALL support optional document-based filtering for MCP tools that fetch entities from the cache.

#### Scenario: Filter spells by Open5e document key
- **WHEN** a caller invokes `lookup_spell` with a document filter (for example, `document_key="srd-5e"` or another Open5e document key)
- **THEN** the tool limits results to entities whose normalized document metadata matches the specified document key
- **AND** combines this constraint with existing filters such as name, level, and school
- **AND** respects the existing `limit` parameter without over-fetching or client-side filtering

#### Scenario: Filter creatures to SRD-only content
- **WHEN** a caller invokes `lookup_creature` with a document filter indicating SRD-only content
- **THEN** the tool returns only creatures whose document metadata corresponds to SRD documents (from Open5e or the D&D 5e API)
- **AND** continues to apply other filters (e.g., challenge rating, type) at the database level
- **AND** returns an empty list (not an error) if no entities match the specified document filter

### Requirement: Document Metadata in Tool Responses
The system SHALL include normalized document metadata in tool responses, aligned with underlying entity document metadata.

#### Scenario: Spell response includes document information
- **WHEN** a spell lookup returns one or more entities
- **THEN** each result includes document metadata fields such as `document_key`, `document_name`, and `document_source`
- **AND** these values are derived from the same normalized entity metadata used for filtering
- **AND** remain consistent regardless of whether results were filtered by document

#### Scenario: OrcBrew spell response includes book as document
- **WHEN** a spell or other entity originates from an OrcBrew file
- **THEN** the tool response includes the OrcBrew book name as `document_name` and a normalized `document_key` derived from that book
- **AND** `document_source` identifies the origin as `orcbrew`
- **AND** downstream callers can distinguish OrcBrew-derived content from Open5e or D&D 5e API data using this metadata

## MODIFIED Requirements

### Requirement: Response Formatting
The system SHALL format all tool responses as structured data suitable for AI consumption.

**Formatting Requirements:**
- Return JSON-serializable data structures
- Include source attribution (document name, API source)
- Use consistent field names across similar data types
- Format text descriptions as plain text or markdown where appropriate
- Include relevant metadata (timestamp, cache status)

#### Scenario: Structured spell response
**Given** a successful spell lookup
**When** results are returned
**Then** the response includes all specified spell fields
**And** the data is JSON-serializable
**And** includes source attribution

#### Scenario: Source attribution
**Given** any successful lookup
**When** results are returned
**Then** each result includes source document information
**And** identifies which API provided the data

#### Scenario: Normalized document metadata in responses
- **WHEN** any lookup tool returns results with document metadata available
- **THEN** the response includes normalized document fields (`document_key`, `document_name`, `document_source`) in addition to existing source attribution
- **AND** tools use these fields consistently across all entity types (spells, creatures, equipment, character options, rules)
- **AND** responses remain backward compatible for callers that ignore the new fields
