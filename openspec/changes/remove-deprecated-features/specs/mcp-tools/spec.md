## MODIFIED Requirements

### Requirement: Tool Naming Convention

All MCP tools SHALL use the `search_*` naming convention for consistency.

#### Scenario: Tool names are standardized
- **GIVEN** the MCP server is started
- **WHEN** listing available tools
- **THEN** tools are named: `search_spell`, `search_creature`, `search_equipment`, `search_character_option`, `search_rule`, `search_all`, `list_documents`
- **AND** no `lookup_*` prefixed tools exist

### Requirement: Hybrid Search Tool Interface

All MCP tools SHALL support both semantic search AND structured filtering parameters. Users can use either approach independently or combine them for hybrid search.

#### Scenario: Spell search with semantic query only
- **WHEN** calling `search_spell(semantic_query="fire damage explosion")`
- **THEN** the system performs semantic vector search
- **AND** returns spells matching the conceptual meaning of the query
- **AND** structured filters are not applied (all spells considered)

#### Scenario: Spell search with structured filters only
- **WHEN** calling `search_spell(level=3, school="evocation")`
- **THEN** the system performs structured filtering at the database level
- **AND** returns spells matching the exact criteria
- **AND** no semantic ranking is applied

#### Scenario: Spell search with hybrid search
- **WHEN** calling `search_spell(semantic_query="fire damage", level=3, school="evocation")`
- **THEN** the system performs semantic vector search
- **AND** applies structured filters to narrow the search space
- **AND** returns spells ranked by semantic similarity within the filtered set

#### Scenario: Creature search with semantic query
- **WHEN** calling `search_creature(semantic_query="fire breathing dragon")`
- **THEN** the system performs semantic vector search
- **AND** returns creatures matching the conceptual meaning

#### Scenario: Creature search with structured filters
- **WHEN** calling `search_creature(type="dragon", cr_min=10)`
- **THEN** the system performs structured filtering
- **AND** returns dragons with CR 10 or higher

#### Scenario: Creature search with hybrid search
- **WHEN** calling `search_creature(semantic_query="fire breathing", type="dragon", cr_min=10)`
- **THEN** the system combines semantic search with structured filters
- **AND** returns fire-related dragons ranked by semantic similarity

#### Scenario: Equipment search with semantic query
- **WHEN** calling `search_equipment(type="weapon", semantic_query="slashing blade")`
- **THEN** the system performs semantic vector search within the equipment type
- **AND** returns equipment matching the conceptual meaning

#### Scenario: Equipment search with structured filters
- **WHEN** calling `search_equipment(type="weapon", is_finesse=True, is_light=True)`
- **THEN** the system performs structured filtering
- **AND** returns finesse light weapons

#### Scenario: Character option search with semantic query
- **WHEN** calling `search_character_option(type="class", semantic_query="martial warrior")`
- **THEN** the system performs semantic vector search within the option type
- **AND** returns options matching the conceptual meaning

#### Scenario: Character option search with structured filters
- **WHEN** calling `search_character_option(type="class", name="fighter")`
- **THEN** the system performs structured filtering
- **AND** returns the Fighter class

#### Scenario: Rule search with semantic query
- **WHEN** calling `search_rule(rule_type="condition", semantic_query="cannot move")`
- **THEN** the system performs semantic vector search within the rule type
- **AND** returns rules matching the conceptual meaning

#### Scenario: Rule search with structured filters
- **WHEN** calling `search_rule(rule_type="condition", name="paralyzed")`
- **THEN** the system performs structured filtering
- **AND** returns the Paralyzed condition

#### Scenario: Search all content with semantic query
- **WHEN** calling `search_all(query="healing magic")`
- **THEN** the system performs semantic vector search across all content types
- **AND** returns results ranked by semantic similarity

---

## REMOVED Requirements

### Requirement: Deprecated Tool Names

**Reason**: The `lookup_*` naming convention is inconsistent with `search_dnd_content`. All tools are renamed to use the `search_*` prefix.

**Migration**: Update all tool calls:
- `lookup_spell()` → `search_spell()`
- `lookup_creature()` → `search_creature()`
- `lookup_equipment()` → `search_equipment()`
- `lookup_character_option()` → `search_character_option()`
- `lookup_rule()` → `search_rule()`
- `search_dnd_content()` → `search_all()`

#### Scenario: Old tool names no longer available
- **GIVEN** code calling `lookup_spell(name="fireball")`
- **WHEN** the function is invoked
- **THEN** an `AttributeError` is raised
- **AND** `search_spell()` should be used instead

### Requirement: Deprecated Cache Clear Functions

**Reason**: The `clear_spell_cache()`, `clear_creature_cache()`, and `clear_character_option_cache()` functions were no-op stubs kept for backward compatibility. Cache management is handled by the repository pattern with database-backed persistence. These functions provided no functionality and were misleading.

**Migration**: Remove all calls to these functions. Cache clearing is not needed with the current architecture - the cache is persistent and managed automatically.

#### Scenario: Clear cache functions no longer available
- **GIVEN** code calling `clear_spell_cache()`
- **WHEN** the function is invoked
- **THEN** an `AttributeError` is raised
- **AND** no import path exists for these functions

---

### Requirement: Fuzzy Search Parameter

**Reason**: Fuzzy search is deprecated. Semantic search provides superior typo tolerance and conceptual matching without the need for explicit fuzzy matching parameters.

**Migration**: Remove `enable_fuzzy` parameter usage. Semantic search handles typos naturally.

#### Scenario: Fuzzy parameter no longer available
- **GIVEN** code calling `search_all(query="firbal", enable_fuzzy=True)`
- **WHEN** the function is invoked
- **THEN** a `TypeError` is raised for unexpected keyword argument
- **AND** semantic search handles the typo automatically

---

### Requirement: Semantic Toggle Parameter

**Reason**: Semantic search is now always enabled. The `semantic` and `enable_semantic` parameters are removed because semantic search is the default and only search mode for `search_all`.

**Migration**: Remove `semantic` and `enable_semantic` parameter usage.

#### Scenario: Semantic parameter no longer available
- **GIVEN** code calling `search_all(query="fireball", semantic=False)`
- **WHEN** the function is invoked
- **THEN** a `TypeError` is raised for unexpected keyword argument
- **AND** the function only accepts `query`, `content_types`, `documents`, `limit`

---

### Requirement: MonsterRepository References

**Reason**: The `MonsterRepository` class was renamed to `CreatureRepository` and the file was renamed from `monster.py` to `creature.py`. All spec examples and documentation that reference `MonsterRepository` must be updated.

**Migration**: Update all imports and references:
- `from lorekeeper_mcp.repositories.monster import MonsterRepository` → `from lorekeeper_mcp.repositories.creature import CreatureRepository`
- `RepositoryFactory.create_monster_repository()` → `RepositoryFactory.create_creature_repository()`

#### Scenario: MonsterRepository no longer available
- **GIVEN** code importing `from lorekeeper_mcp.repositories.monster import MonsterRepository`
- **WHEN** the import is executed
- **THEN** an `ImportError` is raised
- **AND** `CreatureRepository` from `repositories.creature` should be used instead

#### Scenario: Factory method renamed
- **GIVEN** code calling `RepositoryFactory.create_monster_repository()`
- **WHEN** the method is invoked
- **THEN** an `AttributeError` is raised
- **AND** `RepositoryFactory.create_creature_repository()` should be used instead
