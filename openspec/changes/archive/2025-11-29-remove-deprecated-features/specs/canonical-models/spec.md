## ADDED Requirements

### Requirement: No Backward Compatibility Aliases
The system SHALL NOT provide backward compatibility aliases for deprecated model names or import paths.

#### Scenario: Monster alias not available
- **GIVEN** code that previously imported `Monster` from `lorekeeper_mcp.models`
- **WHEN** the import is attempted
- **THEN** an ImportError is raised
- **AND** developers MUST use `Creature` directly

#### Scenario: api_clients.models module not available
- **GIVEN** code that previously imported from `lorekeeper_mcp.api_clients.models`
- **WHEN** the import is attempted
- **THEN** a ModuleNotFoundError is raised
- **AND** developers MUST import from `lorekeeper_mcp.models` instead
