# orcbrew-parser Specification

## Purpose
TBD - created by archiving change import-orcbrew-data. Update Purpose after archive.
## Requirements
### Requirement: EDN Format Parsing
The parser SHALL read and parse .orcbrew files in EDN (Extensible Data Notation) format.

#### Scenario: Parse valid EDN file with single book
**Given** a .orcbrew file with structure:
```edn
{"Book Name"
 {:orcpub.dnd.e5/spells
  {:spell-key {:name "Spell Name", :level 1}}}}
```
**When** the parser reads the file
**Then** the parser successfully parses the EDN structure
**And** extracts the book name "Book Name"
**And** identifies entity type `orcpub.dnd.e5/spells`

#### Scenario: Parse EDN file with multiple entity types
**Given** a .orcbrew file containing spells, monsters, and classes
**When** the parser reads the file
**Then** the parser extracts all three entity types
**And** maintains separate lists for each entity type

#### Scenario: Parse file with malformed EDN
**Given** a file with invalid EDN syntax (unmatched braces)
**When** the parser attempts to read the file
**Then** the parser raises a `ParserError` with message "Invalid EDN syntax"
**And** includes the line number of the syntax error

---

### Requirement: Entity Extraction
The parser SHALL extract individual entities from the parsed EDN structure with all their fields.

#### Scenario: Extract spell entity with all fields
**Given** a parsed spell entity with fields: `:key`, `:name`, `:level`, `:school`, `:description`
**When** the parser extracts the entity
**Then** the extracted entity includes all fields
**And** preserves field names and values
**And** includes the source book name as `option-pack` or top-level key

#### Scenario: Extract entity with nested structures
**Given** an entity with nested maps and lists (e.g., spell components)
**When** the parser extracts the entity
**Then** the parser preserves the nested structure
**And** maintains data types (lists remain lists, maps remain dicts)

#### Scenario: Handle entity with missing required fields
**Given** an entity missing the `:name` field
**When** the parser extracts entities
**Then** the parser logs a warning "Entity missing required field 'name', slug: <slug>"
**And** skips the entity
**And** continues processing remaining entities

---

### Requirement: Entity Normalization
The parser SHALL normalize extracted entities to a consistent format compatible with the cache schema.

#### Scenario: Normalize entity with OrcBrew field names
**Given** an entity with fields `:key`, `:name`, `:option-pack`, `:description`
**When** the parser normalizes the entity
**Then** the normalized entity has fields:
- `slug` (from `:key`)
- `name` (from `:name`)
- `source` (from `:option-pack`)
- `desc` (from `:description`)
- `data` (full original entity as dict)

#### Scenario: Generate slug when :key is missing
**Given** an entity with `:name` but no `:key`
**When** the parser normalizes the entity
**Then** the parser generates a slug from the name (lowercase, hyphenated)
**And** logs "Generated slug '<slug>' for entity '<name>'"

#### Scenario: Handle entity with source_api marker
**Given** a normalized entity
**When** the parser finalizes the entity
**Then** the entity includes `source_api: "orcbrew"` to distinguish from API data

---

### Requirement: Entity Type Mapping
The parser SHALL map OrcBrew entity type namespaces to LoreKeeper entity types.

#### Scenario: Map standard entity types
**Given** entities of type `:orcpub.dnd.e5/spells`
**When** the parser maps the entity type
**Then** the parser returns `"spells"` as the LoreKeeper entity type

**Given** entities of type `:orcpub.dnd.e5/monsters`
**When** the parser maps the entity type
**Then** the parser returns `"creatures"` (following LoreKeeper's nomenclature)

#### Scenario: Map renamed entity types
**Given** entities of type `:orcpub.dnd.e5/races`
**When** the parser maps the entity type
**Then** the parser returns `"species"` (LoreKeeper uses species not races)

#### Scenario: Handle unsupported entity type
**Given** entities of type `:orcpub.dnd.e5/invocations` (not yet supported)
**When** the parser maps the entity type
**Then** the parser returns `None`
**And** logs "Skipping unsupported entity type: orcpub.dnd.e5/invocations"
**And** excludes these entities from import

---

### Requirement: Indexed Field Extraction
The parser SHALL extract indexed fields from entity data for entity types that define indexed fields in the cache schema.

#### Scenario: Extract indexed fields for spells
**Given** a spell entity with `:level 3`, `:school "evocation"`, `:concentration false`
**When** the parser extracts indexed fields
**Then** the normalized entity includes:
- `level: 3` (integer)
- `school: "evocation"` (string)
- `concentration: false` (boolean)

#### Scenario: Extract indexed fields for monsters/creatures
**Given** a monster entity with `:challenge 5`, `:type :aberration`, `:size :large`
**When** the parser extracts indexed fields
**Then** the normalized entity includes:
- `challenge_rating: 5.0` (float)
- `type: "aberration"` (string)
- `size: "large"` (string)

#### Scenario: Handle missing indexed fields
**Given** a spell entity missing the `:level` field
**When** the parser extracts indexed fields
**Then** the parser does not include `level` in indexed fields
**And** logs "Warning: Missing indexed field 'level' for spell '<name>'"
**And** continues with import (field remains in data JSON)

---

### Requirement: Batch Processing
The parser SHALL process entities in batches to optimize memory usage and provide progress reporting.

#### Scenario: Parse large file in batches
**Given** a .orcbrew file with 5000 entities
**When** the parser processes the file
**Then** the parser yields entities in batches of 500
**And** allows the caller to process each batch before continuing

#### Scenario: Track parsing progress
**Given** a file being parsed
**When** the parser processes entities
**Then** the parser provides progress information:
- Current entity type
- Number of entities processed
- Total entities found

---

### Requirement: Error Recovery
The parser SHALL handle errors gracefully and continue processing when possible.

#### Scenario: Skip malformed entity and continue
**Given** a file with 100 entities where entity #50 is malformed
**When** the parser processes the file
**Then** the parser logs an error for entity #50
**And** continues processing entities #51-100
**And** returns 99 successfully parsed entities

#### Scenario: Report multiple errors in summary
**Given** a file with multiple malformed entities
**When** the parse completes
**Then** the parser returns a summary including:
- Total entities found
- Successfully parsed entities
- Failed entities with error types (missing field, invalid type, etc.)

---

### Requirement: Data Type Handling
The parser SHALL correctly handle and convert EDN data types to Python types.

#### Scenario: Convert EDN keywords to strings
**Given** an entity field `:type :aberration`
**When** the parser converts the value
**Then** the value becomes `"aberration"` (string)

#### Scenario: Preserve numeric types
**Given** fields `:level 3` (integer) and `:challenge 5.5` (float)
**When** the parser converts values
**Then** level remains integer `3`
**And** challenge becomes float `5.5`

#### Scenario: Handle EDN collections
**Given** a field with EDN list `[:verbal :somatic :material]`
**When** the parser converts the value
**Then** the value becomes Python list `["verbal", "somatic", "material"]`

### Requirement: Treat OrcBrew Book as Document
The parser SHALL treat the highest-level OrcBrew book heading as the source document for all entities contained within that book.

#### Scenario: Normalize OrcBrew book heading into document metadata
- **GIVEN** a .orcbrew file with a top-level book name such as `"Book Name"`
- **WHEN** the parser reads and normalizes entities from that book
- **THEN** each normalized entity includes `document_name="Book Name"` and a stable `document_key` derived from that name (for example, a lowercased, hyphenated slug)
- **AND** the parser preserves the existing `source` / `source_api` markers to distinguish OrcBrew data from API-derived entities

### Requirement: Expose OrcBrew Document Metadata to Cache
The parser SHALL expose OrcBrew document metadata in a form that can be stored in the entity cache.

#### Scenario: Pass OrcBrew document metadata into normalized entity structure
- **GIVEN** an OrcBrew entity that has been parsed and normalized
- **WHEN** the parser returns the normalized entity to the caller that writes into the cache
- **THEN** the normalized structure includes document metadata fields (`document_key`, `document_name`, `document_source="orcbrew"`)
- **AND** these fields are preserved when entities are stored in the cache and later used by repositories and tools for document-based filtering
