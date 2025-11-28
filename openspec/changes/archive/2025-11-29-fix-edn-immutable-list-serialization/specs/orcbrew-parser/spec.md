## MODIFIED Requirements

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
**And** the result can be serialized to JSON without errors

#### Scenario: Handle edn_format ImmutableList type
**Given** the edn_format library returns an `ImmutableList` for EDN arrays
**When** the parser's `_edn_to_python` method processes the value
**Then** the `ImmutableList` is converted to a standard Python `list`
**And** nested items within the list are also recursively converted
