# MCP Tools Specification - Document Filtering Delta

## ADDED Requirements

### Requirement: Document Listing Tool
The system SHALL provide an MCP tool to list all available documents in the cache.

#### Scenario: List all documents with metadata
- **WHEN** the user invokes `list_documents()` with no filters
- **THEN** the tool returns all cached documents across all sources
- **AND** each document includes: document_name, source_api, entity_count
- **AND** documents are sorted by entity_count descending
- **AND** the tool description explains it shows cached documents only

#### Scenario: Filter documents by source
- **WHEN** the user invokes `list_documents(source="open5e_v2")`
- **THEN** only Open5e documents are returned
- **AND** documents from other sources are excluded
- **AND** valid source values are documented: "open5e_v2", "dnd5e_api", "orcbrew"

#### Scenario: Format as JSON
- **WHEN** the user invokes `list_documents(format="json")`
- **THEN** the tool returns structured JSON with all document fields
- **AND** JSON is parseable by standard JSON tools
- **AND** includes optional metadata fields (publisher, license) when available

#### Scenario: Format as text
- **WHEN** the user invokes `list_documents(format="text")`
- **THEN** the tool returns human-readable formatted text
- **AND** text includes document name, source, and entity count
- **AND** text is easy to scan (aligned columns or bullet points)

#### Scenario: Handle empty cache
- **WHEN** `list_documents()` is called on an empty cache
- **THEN** the tool returns a message "No documents found in cache"
- **AND** no errors are raised

### Requirement: Document Filtering in Search Tool
The search tool SHALL support filtering results by document keys.

#### Scenario: Search with single document filter
- **WHEN** the user invokes `search_dnd_content(query="fireball", document_keys=["srd-5e"])`
- **THEN** only results from the "srd-5e" document are returned
- **AND** results from other documents are excluded
- **AND** search still respects fuzzy and semantic matching parameters

#### Scenario: Search with multiple document filters
- **WHEN** the user invokes `search_dnd_content(query="dragon", document_keys=["srd-5e", "tce", "phb"])`
- **THEN** results from all three documents are returned
- **AND** results from other documents are excluded
- **AND** results are merged and deduplicated

#### Scenario: Search without document filter
- **WHEN** the user invokes `search_dnd_content(query="healing")` without document_keys
- **THEN** results from all documents are returned
- **AND** behavior is identical to current implementation (backward compatible)

#### Scenario: Search with non-existent document
- **WHEN** the user invokes `search_dnd_content(query="spell", document_keys=["non-existent"])`
- **THEN** an empty result list is returned
- **AND** no errors are raised
- **AND** a message indicates no results match the document filter

### Requirement: Document Filtering in Spell Lookup Tool
The spell lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup spell with document filter
- **WHEN** the user invokes `lookup_spell(name="fireball", document_keys=["srd-5e"])`
- **THEN** only "Fireball" from "srd-5e" is returned
- **AND** if "Fireball" exists in other documents, those versions are excluded

#### Scenario: Lookup spells by level with document filter
- **WHEN** the user invokes `lookup_spell(level=3, document_keys=["srd-5e", "tce"])`
- **THEN** all level 3 spells from both documents are returned
- **AND** spells from other documents are excluded

#### Scenario: Lookup without document filter
- **WHEN** the user invokes `lookup_spell(name="fireball")` without document_keys
- **THEN** all versions of "Fireball" from all documents are returned
- **AND** behavior is identical to current implementation (backward compatible)

### Requirement: Document Filtering in Creature Lookup Tool
The creature lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup creature with document filter
- **WHEN** the user invokes `lookup_creature(name="dragon", document_keys=["srd-5e"])`
- **THEN** only dragons from "srd-5e" are returned
- **AND** creatures from other documents are excluded

#### Scenario: Lookup creatures by type with document filter
- **WHEN** the user invokes `lookup_creature(type="dragon", challenge_rating=10, document_keys=["tce"])`
- **THEN** only dragons from "tce" with CR 10 are returned
- **AND** all filter parameters work together (type AND cr AND document)

### Requirement: Document Filtering in Equipment Lookup Tool
The equipment lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup weapon with document filter
- **WHEN** the user invokes `lookup_equipment(item_type="weapon", name="longsword", document_keys=["srd-5e"])`
- **THEN** only "Longsword" from "srd-5e" is returned
- **AND** equipment from other documents is excluded

#### Scenario: Lookup all weapons with document filter
- **WHEN** the user invokes `lookup_equipment(item_type="weapon", document_keys=["srd-5e", "phb"])`
- **THEN** all weapons from both documents are returned
- **AND** weapons from other documents are excluded

### Requirement: Document Filtering in Character Option Lookup Tool
The character option lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup class with document filter
- **WHEN** the user invokes `lookup_character_option(option_type="class", name="wizard", document_keys=["srd-5e"])`
- **THEN** only the "Wizard" class from "srd-5e" is returned
- **AND** classes from other documents are excluded

#### Scenario: Lookup all backgrounds with document filter
- **WHEN** the user invokes `lookup_character_option(option_type="background", document_keys=["phb"])`
- **THEN** all backgrounds from "phb" are returned
- **AND** backgrounds from other documents are excluded

### Requirement: Document Filtering in Rule Lookup Tool
The rule lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup rule with document filter
- **WHEN** the user invokes `lookup_rule(rule_type="rule", name="combat", document_keys=["srd-5e"])`
- **THEN** only combat rules from "srd-5e" are returned
- **AND** rules from other sources are excluded

### Requirement: Consistent Document Filter Parameter
All lookup and search tools SHALL use consistent parameter naming and behavior for document filtering.

#### Scenario: Consistent parameter naming
- **GIVEN** all lookup tools (spell, creature, equipment, character_option, rule) and search tool
- **WHEN** any tool is invoked with document filtering
- **THEN** the parameter is named `document_keys` (not `documents` or `document`)
- **AND** the parameter accepts a list of strings
- **AND** the parameter is optional with default None (no filtering)

#### Scenario: Consistent filtering behavior
- **GIVEN** any lookup or search tool with document_keys parameter
- **WHEN** document_keys is None
- **THEN** no document filtering is applied
- **WHEN** document_keys is an empty list
- **THEN** an empty result is returned
- **WHEN** document_keys is a non-empty list
- **THEN** only results from those documents are returned

### Requirement: Document Filter Response Metadata
Tool responses SHALL include document information for transparency.

#### Scenario: Include document in spell response
- **WHEN** `lookup_spell(name="fireball")` returns results
- **THEN** each spell in the response includes a `document` field
- **AND** the document field shows which document the spell came from
- **AND** this enables users to verify document filtering worked correctly

#### Scenario: Include document in search response
- **WHEN** `search_dnd_content(query="dragon")` returns results
- **THEN** each result includes document metadata
- **AND** users can see which document each result originated from

## MODIFIED Requirements

None - all changes are additive (new optional parameters).

## REMOVED Requirements

None - no functionality is being removed.
