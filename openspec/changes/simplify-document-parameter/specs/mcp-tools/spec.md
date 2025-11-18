# mcp-tools Specification Delta

## Purpose

Update all MCP tool signatures to use a unified `documents` parameter for document filtering, replacing the inconsistent `document` and `document_keys` parameters.

## Requirements

### Requirement: Unified Documents Parameter

All lookup and search tools SHALL use a single `documents: list[str] | None = None` parameter for document filtering.

**Implementation:**
- Remove `document: str | None` parameter from `lookup_spell`, `lookup_creature`, `lookup_equipment`
- Remove `document_keys: list[str] | None` parameter from all tools
- Add `documents: list[str] | None = None` parameter to all tools
- Internal logic passes `documents` to repository as `document` parameter (no repository changes needed)

#### Scenario: Spell lookup with documents filter
**Given** a user calls `lookup_spell(name="fireball", documents=["srd-5e"])`
**When** the tool is invoked
**Then** the system filters spells to only those from the "srd-5e" document
**And** passes the filter to the repository layer as `document=["srd-5e"]`

#### Scenario: Creature lookup with multiple documents
**Given** a user calls `lookup_creature(type="dragon", documents=["srd-5e", "tce"])`
**When** the tool is invoked
**Then** the system filters creatures to those from either "srd-5e" or "tce" documents
**And** uses the repository's IN clause filtering

#### Scenario: Equipment lookup with documents filter
**Given** a user calls `lookup_equipment(type="weapon", documents=["srd-5e"])`
**When** the tool is invoked
**Then** the system filters weapons to only those from the "srd-5e" document
**And** applies the filter to all equipment types (weapons, armor, magic items)

#### Scenario: Character option lookup with documents filter
**Given** a user calls `lookup_character_option(type="class", documents=["srd-5e"])`
**When** the tool is invoked
**Then** the system filters character options to only those from the "srd-5e" document

#### Scenario: Rule lookup with documents filter
**Given** a user calls `lookup_rule(rule_type="condition", documents=["srd-5e"])`
**When** the tool is invoked
**Then** the system filters rules to only those from the "srd-5e" document

#### Scenario: Search with documents post-filter
**Given** a user calls `search_dnd_content(query="fire", documents=["srd-5e"])`
**When** the tool is invoked
**Then** the system searches across all content types
**And** post-filters results to only those from the "srd-5e" document

#### Scenario: Default behavior without documents filter
**Given** a user calls any tool without the `documents` parameter
**When** the tool is invoked
**Then** the system searches all documents (no filtering)
**And** behavior is identical to previous implementation

#### Scenario: Empty documents list short-circuits
**Given** a user calls any tool with `documents=[]`
**When** the tool is invoked
**Then** the system returns an empty result immediately
**And** no database queries are executed

---

### Requirement: Consistent Parameter Interface

All tools SHALL have identical `documents` parameter behavior and documentation.

**Implementation:**
- Parameter name: `documents`
- Parameter type: `list[str] | None`
- Default value: `None`
- Position: After domain-specific filters, before `limit`

#### Scenario: Consistent docstring format
**Given** any lookup or search tool
**When** viewing the docstring
**Then** the `documents` parameter documentation includes:
- Description: "Filter to specific source documents"
- Usage: "Provide a list of document names/identifiers from list_documents() tool"
- Examples: `["srd-5e"]` for SRD only, `["srd-5e", "tce"]` for multiple

#### Scenario: Tool discovery via list_documents
**Given** a user wants to filter by document
**When** they call `list_documents()`
**Then** the result includes document names they can use in the `documents` parameter
**And** the docstring references this workflow
