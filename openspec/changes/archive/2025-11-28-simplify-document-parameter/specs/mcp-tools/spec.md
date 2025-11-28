# mcp-tools Specification Delta

## Purpose

Update all MCP tool signatures to use a unified `documents` parameter for document filtering, replacing the inconsistent `document` and `document_keys` parameters.

## MODIFIED Requirements

### Requirement: Document Filtering in Search Tool
The search tool SHALL support filtering results by document keys.

#### Scenario: Search with single document filter
- **WHEN** the user invokes `search_dnd_content(query="fireball", documents=["srd-5e"])`
- **THEN** only results from the "srd-5e" document are returned
- **AND** results from other documents are excluded
- **AND** search still respects fuzzy and semantic matching parameters

#### Scenario: Search with multiple document filters
- **WHEN** the user invokes `search_dnd_content(query="dragon", documents=["srd-5e", "tce", "phb"])`
- **THEN** results from all three documents are returned
- **AND** results from other documents are excluded
- **AND** results are merged and deduplicated

#### Scenario: Search without document filter
- **WHEN** the user invokes `search_dnd_content(query="healing")` without documents
- **THEN** results from all documents are returned
- **AND** behavior is identical to current implementation (backward compatible)

#### Scenario: Search with non-existent document
- **WHEN** the user invokes `search_dnd_content(query="spell", documents=["non-existent"])`
- **THEN** an empty result list is returned
- **AND** no errors are raised
- **AND** a message indicates no results match the document filter

---

### Requirement: Document Filtering in Spell Lookup Tool
The spell lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup spell with document filter
- **WHEN** the user invokes `lookup_spell(name="fireball", documents=["srd-5e"])`
- **THEN** only "Fireball" from "srd-5e" is returned
- **AND** if "Fireball" exists in other documents, those versions are excluded

#### Scenario: Lookup spells by level with document filter
- **WHEN** the user invokes `lookup_spell(level=3, documents=["srd-5e", "tce"])`
- **THEN** all level 3 spells from both documents are returned
- **AND** spells from other documents are excluded

#### Scenario: Lookup without document filter
- **WHEN** the user invokes `lookup_spell(name="fireball")` without documents
- **THEN** all versions of "Fireball" from all documents are returned
- **AND** behavior is identical to current implementation (backward compatible)

---

### Requirement: Document Filtering in Creature Lookup Tool
The creature lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup creature with document filter
- **WHEN** the user invokes `lookup_creature(name="dragon", documents=["srd-5e"])`
- **THEN** only dragons from "srd-5e" are returned
- **AND** creatures from other documents are excluded

#### Scenario: Lookup creatures by type with document filter
- **WHEN** the user invokes `lookup_creature(type="dragon", challenge_rating=10, documents=["tce"])`
- **THEN** only dragons from "tce" with CR 10 are returned
- **AND** all filter parameters work together (type AND cr AND document)

---

### Requirement: Document Filtering in Equipment Lookup Tool
The equipment lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup weapon with document filter
- **WHEN** the user invokes `lookup_equipment(item_type="weapon", name="longsword", documents=["srd-5e"])`
- **THEN** only "Longsword" from "srd-5e" is returned
- **AND** equipment from other documents is excluded

#### Scenario: Lookup all weapons with document filter
- **WHEN** the user invokes `lookup_equipment(item_type="weapon", documents=["srd-5e", "phb"])`
- **THEN** all weapons from both documents are returned
- **AND** weapons from other documents are excluded

---

### Requirement: Document Filtering in Character Option Lookup Tool
The character option lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup class with document filter
- **WHEN** the user invokes `lookup_character_option(option_type="class", name="wizard", documents=["srd-5e"])`
- **THEN** only the "Wizard" class from "srd-5e" is returned
- **AND** classes from other documents are excluded

#### Scenario: Lookup all backgrounds with document filter
- **WHEN** the user invokes `lookup_character_option(option_type="background", documents=["phb"])`
- **THEN** all backgrounds from "phb" are returned
- **AND** backgrounds from other documents are excluded

---

### Requirement: Document Filtering in Rule Lookup Tool
The rule lookup tool SHALL support filtering by document keys.

#### Scenario: Lookup rule with document filter
- **WHEN** the user invokes `lookup_rule(rule_type="rule", name="combat", documents=["srd-5e"])`
- **THEN** only combat rules from "srd-5e" are returned
- **AND** rules from other sources are excluded

---

### Requirement: Consistent Document Filter Parameter
All lookup and search tools SHALL use consistent parameter naming and behavior for document filtering.

#### Scenario: Consistent parameter naming
- **GIVEN** all lookup tools (spell, creature, equipment, character_option, rule) and search tool
- **WHEN** any tool is invoked with document filtering
- **THEN** the parameter is named `documents` (not `document` or `document_keys`)
- **AND** the parameter accepts a list of strings
- **AND** the parameter is optional with default None (no filtering)

#### Scenario: Consistent filtering behavior
- **GIVEN** any lookup or search tool with documents parameter
- **WHEN** documents is None
- **THEN** no document filtering is applied
- **WHEN** documents is an empty list
- **THEN** an empty result is returned
- **WHEN** documents is a non-empty list
- **THEN** only results from those documents are returned

---

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
