## REMOVED Requirements

### Requirement: D&D 5e Rules API Client

**Reason**: Open5e v2 API provides equivalent `/v2/rules/` endpoint with the same SRD content. Maintaining separate clients for identical data creates unnecessary complexity.

**Migration**: Use `Open5eV2Client.get_rules_v2()` method instead. The Open5e rules endpoint returns the same SRD rule content.

### Requirement: D&D 5e Reference Data API Client

**Reason**: Open5e v2 API provides all reference data endpoints (damage types, skills, ability scores, magic schools, languages, alignments, conditions). These return the same SRD content.

**Migration**: Use Open5eV2Client methods:
- `get_damage_types_v2()` replaces `get_damage_types()`
- `get_skills_v2()` replaces `get_skills()`
- `get_abilities()` replaces `get_ability_scores()`
- `get_spell_schools_v2()` replaces `get_magic_schools()`
- `get_languages_v2()` replaces `get_languages()`
- `get_alignments_v2()` replaces `get_alignments()`
- `get_conditions()` replaces `get_conditions_dnd5e()`

### Requirement: D&D 5e API Client Factory

**Reason**: With the D&D 5e API client removed, the factory method is no longer needed.

**Migration**: Use `ClientFactory.create_open5e_v2()` for all API client needs.

### Requirement: API Version Handling

**Reason**: Open5e API has its own versioning (v1/v2) handled by the existing Open5e clients. D&D 5e API version handling is no longer needed.

**Migration**: None required - Open5e client already handles v2 API.

### Requirement: Reference Data Caching Strategy

**Reason**: The caching strategy applies equally to Open5e API. Extended TTLs for reference data can be maintained in the existing cache layer.

**Migration**: Cache TTL configuration should be retained in the cache layer for all reference data regardless of source API.
