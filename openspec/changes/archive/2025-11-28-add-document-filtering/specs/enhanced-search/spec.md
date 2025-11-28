# Enhanced Search Specification - Document Filtering Delta

## ADDED Requirements

### Requirement: Document-Based Search Filtering
The unified search functionality SHALL support filtering search results by source document.

#### Scenario: Filter search results by single document
- **GIVEN** the search index contains content from multiple documents
- **WHEN** a search is performed with document filter for a single document
- **THEN** only results from that document are included in search results
- **AND** results from other documents are excluded
- **AND** search relevance scoring is unaffected by document filtering

#### Scenario: Filter search results by multiple documents
- **GIVEN** the search index contains content from multiple documents
- **WHEN** a search is performed with document filter for multiple documents
- **THEN** results from all specified documents are included
- **AND** results from other documents are excluded
- **AND** results maintain relevance order across all included documents

#### Scenario: Post-filter unified search results
- **GIVEN** the Open5e unified search does not support document filtering natively
- **WHEN** a search with document filter is executed
- **THEN** the search is performed without document filter first
- **AND** results are post-filtered by document field before returning to user
- **AND** post-filtering respects the limit parameter (may return fewer than limit if filtered out)

#### Scenario: Combine document filter with content type filter
- **GIVEN** search supports both document and content_type filtering
- **WHEN** both filters are applied: `search(query="fire", content_types=["Spell"], document_keys=["srd-5e"])`
- **THEN** only spells from "srd-5e" matching "fire" are returned
- **AND** both filters are applied (AND logic, not OR)

### Requirement: Document Filter Performance Optimization
Document filtering SHALL be optimized to minimize performance impact on search operations.

#### Scenario: Cache-based document filtering
- **GIVEN** search results need to be filtered by document
- **WHEN** post-filtering is required
- **THEN** document field is extracted from cached entity data
- **AND** no additional API calls are made for document validation
- **AND** filtering completes in <50ms for typical result sets

#### Scenario: Early termination for empty document list
- **GIVEN** a search is requested with an empty document_keys list
- **WHEN** the search function receives document_keys=[]
- **THEN** an empty result list is returned immediately
- **AND** no search query or API call is executed (short-circuit optimization)

## MODIFIED Requirements

None - all changes are additive.

## REMOVED Requirements

None - no functionality is being removed.
