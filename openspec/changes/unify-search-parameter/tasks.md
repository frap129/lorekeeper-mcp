## 1. Repository Layer Updates

- [x] 1.1 Update `SpellRepository` to accept `search` instead of `semantic_query`
- [x] 1.2 Update `CreatureRepository` to accept `search` instead of `semantic_query`
- [x] 1.3 Update `EquipmentRepository` to accept `search` instead of `semantic_query`
- [x] 1.4 Update `CharacterOptionRepository` to accept `search` instead of `semantic_query`
- [x] 1.5 Update `RuleRepository` to accept `search` instead of `semantic_query`

## 2. Tool Layer Updates

- [x] 2.1 Update `search_spell` tool: remove `name`, rename `semantic_query` to `search`
- [x] 2.2 Update `search_creature` tool: remove `name`, rename `semantic_query` to `search`
- [x] 2.3 Update `search_equipment` tool: remove `name`, rename `semantic_query` to `search`
- [x] 2.4 Update `search_character_option` tool: remove `name`, rename `semantic_query` to `search`
- [x] 2.5 Update `search_rule` tool: remove `name`, rename `semantic_query` to `search`

## 3. Documentation Updates

- [x] 3.1 Update tool docstrings with new `search` parameter descriptions
- [x] 3.2 Update tool examples to use `search` instead of `name`/`semantic_query`

## 4. Test Updates

- [x] 4.1 Update repository tests to use `search` parameter
- [x] 4.2 Update tool unit tests to use `search` parameter
- [x] 4.3 Update integration tests to use `search` parameter
- [x] 4.4 Run full test suite and fix any failures

## 5. Validation

- [x] 5.1 Run `just check` to verify code quality
- [x] 5.2 Run live tests to confirm MCP tools work correctly
- [x] 5.3 Verify search functionality with manual testing
