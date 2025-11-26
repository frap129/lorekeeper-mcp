## REMOVED Requirements

### Requirement: D&D 5e API Character Options Endpoints

**Reason**: Open5e v2 API provides equivalent endpoints for all character options (backgrounds, classes, races, feats, traits). The SRD content is identical, and Open5e already aggregates multiple sources including the SRD.

**Migration**: Use Open5eV2Client methods:
- `get_backgrounds_v2()` replaces `get_backgrounds_dnd5e()`
- `get_classes_v2()` replaces `get_classes_dnd5e()`
- `get_races_v2()` replaces `get_races_dnd5e()`
- `get_feats_v2()` replaces `get_feats_dnd5e()`

For subclasses, subraces, and traits:
- Open5e v2 includes subclass data within class responses
- Open5e v2 includes subrace data within race responses
- Open5e v2 includes trait data within race responses

### Requirement: D&D 5e API Equipment Endpoints

**Reason**: Open5e v2 API provides equivalent equipment endpoints. The `/v2/items/` and `/v2/armor/` and `/v2/weapons/` endpoints cover all equipment types with the same SRD content.

**Migration**: Use Open5eV2Client methods:
- `get_equipment_v2()` replaces `get_equipment()`
- `get_magic_items_v2()` replaces `get_magic_items_dnd5e()`
- `get_weapons_v2()` replaces weapon-specific queries
- `get_armor_v2()` replaces armor-specific queries

Equipment categories are handled implicitly through the equipment type filters in Open5e v2.

### Requirement: D&D 5e API Spells and Magic Endpoints

**Reason**: Open5e v2 API provides the `/v2/spells/` endpoint with identical SRD spell content and superior filtering capabilities (document filtering, multiple schools, etc.).

**Migration**: Use `Open5eV2Client.get_spells_v2()` method. The Open5e v2 endpoint supports:
- Level filtering
- School filtering
- Class filtering via document parameter
- Text search

### Requirement: D&D 5e API Monster Endpoints

**Reason**: Open5e v2 API provides the `/v2/creatures/` endpoint with comprehensive monster data including the complete SRD bestiary.

**Migration**: Use `Open5eV2Client.get_creatures()` method. Supports CR filtering, type filtering, and name search.

### Requirement: D&D 5e API Conditions Endpoint

**Reason**: Open5e v2 API provides the `/v2/conditions/` endpoint with identical SRD condition data.

**Migration**: Use `Open5eV2Client.get_conditions()` method.

### Requirement: D&D 5e API Features Endpoint

**Reason**: Open5e v2 API includes feature data within class and race responses. Dedicated feature endpoints are not needed when features are embedded in their parent entities.

**Migration**: Access features through:
- `get_classes_v2()` - includes class features
- `get_races_v2()` - includes racial traits/features
- `get_backgrounds_v2()` - includes background features
