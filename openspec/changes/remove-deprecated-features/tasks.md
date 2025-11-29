## 1. Remove Monster Model Alias
- [x] 1.1 Remove `Monster` class from `src/lorekeeper_mcp/models/creature.py`
- [x] 1.2 Remove `Monster` from exports in `src/lorekeeper_mcp/models/__init__.py`
- [x] 1.3 Update `tests/test_models/test_creature.py` to remove Monster deprecation test

## 2. Remove Deprecated API Client Models Module
- [x] 2.1 Delete `src/lorekeeper_mcp/api_clients/models/__init__.py`
- [x] 2.2 Delete `src/lorekeeper_mcp/api_clients/models/` directory
- [x] 2.3 Remove model re-exports from `src/lorekeeper_mcp/api_clients/__init__.py`
- [x] 2.4 Update `tests/test_api_clients/test_models.py` to import from `lorekeeper_mcp.models`

## 3. Remove Monster Repository Aliases
- [x] 3.1 Remove `MonsterClient`, `MonsterCache`, `MonsterRepository` aliases from `src/lorekeeper_mcp/repositories/monster.py`
- [x] 3.2 Rename `monster.py` to `creature.py`
- [x] 3.3 Update `src/lorekeeper_mcp/tools/creature_lookup.py` to use `CreatureRepository` from `creature.py`
- [x] 3.4 Update `src/lorekeeper_mcp/repositories/factory.py` to rename `create_monster_repository` to `create_creature_repository`
- [x] 3.5 Update `src/lorekeeper_mcp/repositories/__init__.py` exports
- [x] 3.6 Update all tests using `MonsterRepository` to use `CreatureRepository`

## 4. Remove SQLite Cache Backend
- [x] 4.1 Delete `src/lorekeeper_mcp/cache/sqlite.py`
- [x] 4.2 Delete `src/lorekeeper_mcp/cache/db.py`
- [x] 4.3 Delete `src/lorekeeper_mcp/cache/schema.py`
- [x] 4.4 Update `src/lorekeeper_mcp/cache/__init__.py` to remove SQLite exports
- [x] 4.5 Update `src/lorekeeper_mcp/cache/factory.py` to remove SQLite backend support
- [x] 4.6 Update `src/lorekeeper_mcp/config.py` to remove SQLite configuration
- [x] 4.7 Update `src/lorekeeper_mcp/cli.py` to remove SQLite references
- [x] 4.8 Delete `tests/test_cache/test_sqlite.py`
- [x] 4.9 Delete `tests/test_cache/test_db.py`
- [x] 4.10 Delete `tests/test_cache/test_schema.py`
- [x] 4.11 Update all tests that reference SQLite to use Milvus only

## 5. Remove Deprecated Search Toggle Parameters
- [x] 5.1 Remove `enable_semantic` parameter from `search_dnd_content()`
- [x] 5.2 Remove `semantic` parameter from `search_dnd_content()`
- [x] 5.3 Remove `enable_fuzzy` parameter from `search_dnd_content()`
- [x] 5.4 Update docstrings to reflect semantic search is always enabled
- [x] 5.5 Update any tests using removed parameters

## 6. Rename Tools to search_* Convention
- [ ] 6.1 Rename `src/lorekeeper_mcp/tools/spell_lookup.py` to `search_spell.py`
- [ ] 6.2 Rename function `lookup_spell` to `search_spell` in `search_spell.py`
- [ ] 6.3 Rename `src/lorekeeper_mcp/tools/creature_lookup.py` to `search_creature.py`
- [ ] 6.4 Rename function `lookup_creature` to `search_creature` in `search_creature.py`
- [ ] 6.5 Rename `src/lorekeeper_mcp/tools/equipment_lookup.py` to `search_equipment.py`
- [ ] 6.6 Rename function `lookup_equipment` to `search_equipment` in `search_equipment.py`
- [ ] 6.7 Rename `src/lorekeeper_mcp/tools/character_option_lookup.py` to `search_character_option.py`
- [ ] 6.8 Rename function `lookup_character_option` to `search_character_option` in `search_character_option.py`
- [ ] 6.9 Rename `src/lorekeeper_mcp/tools/rule_lookup.py` to `search_rule.py`
- [ ] 6.10 Rename function `lookup_rule` to `search_rule` in `search_rule.py`
- [ ] 6.11 Rename `src/lorekeeper_mcp/tools/search_dnd_content.py` to `search_all.py`
- [ ] 6.12 Rename function `search_dnd_content` to `search_all` in `search_all.py`
- [ ] 6.13 Update `src/lorekeeper_mcp/tools/__init__.py` with new exports
- [ ] 6.14 Update `src/lorekeeper_mcp/server.py` tool registrations
- [ ] 6.15 Update all test files to use new tool names

## 7. Remove Deprecated Clear Cache Functions
- [ ] 7.1 Remove `clear_spell_cache()` function from `search_spell.py`
- [ ] 7.2 Remove `clear_creature_cache()` function from `search_creature.py`
- [ ] 7.3 Remove `clear_character_option_cache()` function from `search_character_option.py`
- [ ] 7.4 Update any tests that reference these functions

## 8. Remove "monsters" Table Alias in Entity Cache
- [ ] 8.1 Remove "monsters" → "creatures" alias handling from cache query functions
- [ ] 8.2 Remove deprecation warning logging for "monsters" table queries
- [ ] 8.3 Update any tests that use "monsters" table name to use "creatures"

## 9. Update Specs
- [ ] 9.1 Update `canonical-models` spec to remove Monster backward compatibility scenario
- [ ] 9.2 Update `entity-cache` spec to remove "monsters" table alias scenario
- [ ] 9.3 Update `entity-cache` spec to remove SQLite references
- [ ] 9.4 Update `mcp-tools` spec to reflect new tool names and remove deprecated toggle parameters
- [ ] 9.5 Update `database-setup` spec to remove SQLite

## 10. Update Documentation
- [ ] 10.1 Update docstrings in all tool files
- [ ] 10.2 Update `docs/architecture.md` to remove SQLite/Monster references
- [ ] 10.3 Update `docs/cache.md` to reflect Milvus-only
- [ ] 10.4 Update `docs/tools.md` to reflect new tool names
- [ ] 10.5 Update `.env.example` to remove SQLite variables

## 11. Validation
- [ ] 11.1 Run full test suite to verify no regressions (`just test`)
- [ ] 11.2 Run type checking (`just type-check`)
- [ ] 11.3 Run linting (`just lint`)
- [ ] 11.4 Run live tests to ensure everything works (`pytest -m live`)
- [ ] 11.5 Verify MCP server starts correctly (`just serve`)
