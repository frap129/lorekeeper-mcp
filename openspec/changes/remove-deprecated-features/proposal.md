## Why

The codebase contains several deprecated features that were kept for backward compatibility during migration periods. These deprecation periods have passed, and the deprecated code adds maintenance burden, confusion, and noise. Additionally, the architecture has evolved to use Milvus as the sole cache backend. This change removes all deprecated features while preserving the hybrid search architecture that combines structured filters with semantic search.

Additionally, the tool naming convention is inconsistent (`lookup_*` vs `search_dnd_content`). This change standardizes all tools to use the `search_*` prefix for consistency.

## What Changes

### Model Deprecations (BREAKING)
- **BREAKING**: Remove `Monster` model alias from `lorekeeper_mcp.models` - use `Creature` instead
- **BREAKING**: Remove `Monster` import support from `lorekeeper_mcp.api_clients.models`
- **BREAKING**: Remove `MonsterClient`, `MonsterCache`, `MonsterRepository` aliases from `repositories/monster.py`
- **BREAKING**: Remove deprecated model re-exports from `lorekeeper_mcp.api_clients` package
- **BREAKING**: Remove deprecated `api_clients/models/` module entirely

### SQLite Removal (BREAKING)
- **BREAKING**: Remove SQLite cache backend entirely - Milvus is the only backend
- **BREAKING**: Remove `SQLiteCache` class from `lorekeeper_mcp.cache`
- **BREAKING**: Remove `sqlite` backend option from cache factory
- **BREAKING**: Remove `LOREKEEPER_SQLITE_DB_PATH` environment variable support
- Remove `src/lorekeeper_mcp/cache/sqlite.py`
- Remove `src/lorekeeper_mcp/cache/db.py` (legacy SQLite utilities)
- Remove `src/lorekeeper_mcp/cache/schema.py` (SQLite schema)

### Search Toggle Cleanup (BREAKING) - Remove Deprecated Toggles Only
- **BREAKING**: Remove `enable_semantic` parameter from `search_dnd_content()` - semantic is always on
- **BREAKING**: Remove `semantic` parameter from `search_dnd_content()` - semantic is always on
- **BREAKING**: Remove `enable_fuzzy` parameter from `search_dnd_content()` - fuzzy matching is deprecated

### Tool Renaming (BREAKING)
- **BREAKING**: Rename `lookup_spell` → `search_spell`
- **BREAKING**: Rename `lookup_creature` → `search_creature`
- **BREAKING**: Rename `lookup_equipment` → `search_equipment`
- **BREAKING**: Rename `lookup_character_option` → `search_character_option`
- **BREAKING**: Rename `lookup_rule` → `search_rule`
- **BREAKING**: Rename `search_dnd_content` → `search_all`

### Structured Filters Preserved (NO CHANGE)
All existing structured filter parameters are **preserved** and work in combination with semantic search:
- `search_spell`: Keep all parameters (`name`, `level`, `level_min`, `level_max`, `school`, `class_key`, `concentration`, `ritual`, `casting_time`, `damage_type`, `documents`, `semantic_query`, `limit`)
- `search_creature`: Keep all parameters (`name`, `cr`, `cr_min`, `cr_max`, `type`, `size`, `armor_class_min`, `hit_points_min`, `documents`, `semantic_query`, `limit`)
- `search_equipment`: Keep all parameters (`type`, `name`, `rarity`, `damage_dice`, `is_simple`, `requires_attunement`, `cost_min`, `cost_max`, `weight_max`, `is_finesse`, `is_light`, `is_magic`, `documents`, `semantic_query`, `limit`)
- `search_character_option`: Keep all parameters (`type`, `name`, `documents`, `semantic_query`, `limit`)
- `search_rule`: Keep all parameters (`rule_type`, `name`, `section`, `documents`, `semantic_query`, `limit`)

### Cache Table Deprecations
- Remove "monsters" table name alias in entity cache (use "creatures" only)

### Deprecated Function Removal
- Remove deprecated `clear_spell_cache()`, `clear_creature_cache()`, `clear_character_option_cache()` stub functions

## Impact

- Affected specs: `canonical-models`, `entity-cache`, `mcp-tools`, `database-setup`
- Affected code:
  - `src/lorekeeper_mcp/models/creature.py` - Remove `Monster` class
  - `src/lorekeeper_mcp/models/__init__.py` - Remove `Monster` export
  - `src/lorekeeper_mcp/api_clients/__init__.py` - Remove model re-exports
  - `src/lorekeeper_mcp/api_clients/models/` - Remove entire module
  - `src/lorekeeper_mcp/repositories/monster.py` - Remove `Monster*` aliases, rename to `creature.py`
  - `src/lorekeeper_mcp/cache/sqlite.py` - Remove entirely
  - `src/lorekeeper_mcp/cache/db.py` - Remove entirely
  - `src/lorekeeper_mcp/cache/schema.py` - Remove entirely
  - `src/lorekeeper_mcp/cache/__init__.py` - Remove SQLite exports
  - `src/lorekeeper_mcp/cache/factory.py` - Remove SQLite backend support
  - `src/lorekeeper_mcp/tools/search_dnd_content.py` - Rename to `search_all.py`, remove deprecated toggle parameters
  - `src/lorekeeper_mcp/tools/spell_lookup.py` - Rename to `search_spell.py`, remove `clear_spell_cache()` function
  - `src/lorekeeper_mcp/tools/creature_lookup.py` - Rename to `search_creature.py`, remove `clear_creature_cache()` function
  - `src/lorekeeper_mcp/tools/equipment_lookup.py` - Rename to `search_equipment.py`
  - `src/lorekeeper_mcp/tools/character_option_lookup.py` - Rename to `search_character_option.py`, remove `clear_character_option_cache()` function
  - `src/lorekeeper_mcp/tools/rule_lookup.py` - Rename to `search_rule.py`
  - `src/lorekeeper_mcp/tools/__init__.py` - Update exports with new tool names
  - `src/lorekeeper_mcp/server.py` - Update tool registrations
  - `src/lorekeeper_mcp/config.py` - Remove SQLite config
  - `src/lorekeeper_mcp/cli.py` - Remove SQLite references
  - `tests/` - Update all tests, remove SQLite-specific tests, update tool names
