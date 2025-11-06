# Implement D&D 5e API Client

## Why

The previous change (build-api-clients) successfully implemented Open5e v1 and v2 clients but omitted the D&D 5e API client (`Dnd5eApiClient`), leaving the system unable to fetch rules and reference data that are not available in Open5e (e.g., combat rules, rule sections, damage types, skills, ability scores).

## What Changes

- Add `Dnd5eApiClient` class in `src/lorekeeper_mcp/api_clients/dnd5e_api.py` inheriting from `BaseHttpClient`
- Add API version handling and redirect support for `/api/2014/` endpoints
- Implement `get_rules()` method for fetching rule categories (adventuring, combat, equipment, spellcasting, using-ability-scores, appendix)
- Implement `get_rule_sections()` method for fetching detailed rule sections with cross-references
- Implement reference data methods: `get_damage_types()`, `get_weapon_properties()`, `get_skills()`, `get_ability_scores()`, `get_magic_schools()`, `get_languages()`, `get_proficiencies()`, `get_alignments()`
- Add extended caching with 30-day TTL (2,592,000 seconds) for static reference data
- Add `ClientFactory.create_dnd5e_api()` factory method
- Update `__init__.py` to export `Dnd5eApiClient`
- Add comprehensive unit tests in `tests/test_api_clients/test_dnd5e_api.py` achieving >90% coverage

## Impact

**Affected specs:**
- `dnd5e-api-client` (implementing existing requirements from previous change)

**Affected code:**
- `src/lorekeeper_mcp/api_clients/dnd5e_api.py` - New file with Dnd5eApiClient implementation
- `src/lorekeeper_mcp/api_clients/factory.py` - Add create_dnd5e_api() factory method
- `src/lorekeeper_mcp/api_clients/__init__.py` - Export Dnd5eApiClient
- `tests/test_api_clients/test_dnd5e_api.py` - New test file with comprehensive test coverage
