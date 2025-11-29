## REMOVED Requirements

### Requirement: Backward compatibility with Monster alias

**Reason**: The deprecation period for the Monster alias has passed. The canonical model name is `Creature`, aligning with Open5e v2 terminology. All code should use `Creature` directly.

**Migration**: Replace all imports of `Monster` with `Creature`:
- Change `from lorekeeper_mcp.models import Monster` to `from lorekeeper_mcp.models import Creature`
- Change `from lorekeeper_mcp.api_clients.models import Monster` to `from lorekeeper_mcp.models import Creature`
- Replace all `Monster(...)` instantiations with `Creature(...)`

#### Scenario: Monster alias no longer available
- **GIVEN** existing code using `from lorekeeper_mcp.models import Monster`
- **WHEN** the import is executed
- **THEN** an `ImportError` is raised
- **AND** the error message suggests using `Creature` instead

---

### Requirement: Deprecated api_clients.models module

**Reason**: The `api_clients.models` module was a backward compatibility shim. All models should be imported from `lorekeeper_mcp.models`.

**Migration**: Change all imports from `lorekeeper_mcp.api_clients.models` to `lorekeeper_mcp.models`.

#### Scenario: api_clients.models module no longer available
- **GIVEN** existing code using `from lorekeeper_mcp.api_clients.models import Spell`
- **WHEN** the import is executed
- **THEN** an `ImportError` is raised
- **AND** the canonical import path is `from lorekeeper_mcp.models import Spell`
