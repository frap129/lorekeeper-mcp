# Research: Open5e API v2 Weapon Structure

**Date:** November 6, 2025
**Task:** Task 2.1 - Research Open5e API v2 Weapon Structure
**Status:** Complete

---

## Executive Summary

The Open5e API v2 weapon endpoint returns a fundamentally different structure than expected by the current Weapon model. Key findings:

1. **`damage_type` is an object, not a string** - This is the primary breaking issue
2. **Properties are complex objects with nested structure** - Not simple strings
3. **Range fields are floats, not integers** - API returns `20.0`, not `20`
4. **Several new fields exist in API** - `key`, `url`, `document`, `distance_unit`, `is_simple`, `is_improvised`
5. **Several model fields don't exist in API** - `category`, `cost`, `weight`, `properties` (as strings)
6. **No versatile damage dice in main object** - It's nested within the properties array

---

## API v2 Weapon Response Structure

### Full Response Example
```json
{
  "url": "https://api.open5e.com/v2/weapons/srd-2024_dagger/",
  "key": "srd-2024_dagger",
  "document": {
    "name": "System Reference Document 5.2",
    "key": "srd-2024",
    "display_name": "5e 2024 Rules",
    "publisher": {
      "name": "Wizards of the Coast",
      "key": "wizards-of-the-coast",
      "url": "https://api.open5e.com/v2/publishers/wizards-of-the-coast/"
    },
    "gamesystem": {
      "name": "5th Edition 2024",
      "key": "5e-2024",
      "url": "https://api.open5e.com/v2/gamesystems/5e-2024/"
    },
    "permalink": "https://dnd.wizards.com/resources/systems-reference-document"
  },
  "name": "Dagger",
  "damage_dice": "1d4",
  "damage_type": {
    "name": "Piercing",
    "key": "piercing",
    "url": "https://api.open5e.com/v2/damagetypes/piercing/"
  },
  "properties": [
    {
      "property": {
        "name": "Finesse",
        "type": null,
        "url": "/v2/weaponproperties/srd-2024_finesse-wp/"
      },
      "detail": null
    },
    {
      "property": {
        "name": "Light",
        "type": null,
        "url": "/v2/weaponproperties/srd-2024_light-wp/"
      },
      "detail": null
    },
    {
      "property": {
        "name": "Nick",
        "type": "Mastery",
        "url": "/v2/weaponproperties/srd-2024_nick-mastery/"
      },
      "detail": null
    },
    {
      "property": {
        "name": "Thrown",
        "type": null,
        "url": "/v2/weaponproperties/srd-2024_thrown-wp/"
      },
      "detail": null
    }
  ],
  "range": 20.0,
  "long_range": 60.0,
  "distance_unit": "feet",
  "is_simple": true,
  "is_improvised": false
}
```

### Field Inventory - API Response

| Field | Type | Optional/Required | Description | Example |
|-------|------|-------------------|-------------|---------|
| `url` | string | Required | Full API endpoint URL | `"https://api.open5e.com/v2/weapons/srd-2024_dagger/"` |
| `key` | string | Required | Unique identifier | `"srd-2024_dagger"` |
| `name` | string | Required | Weapon name | `"Dagger"` |
| `damage_dice` | string | Required | Damage dice notation | `"1d4"`, `"2d6"`, `"1"` |
| `damage_type` | object | Required | Damage type with metadata | See below |
| `damage_type.name` | string | Required | Damage type name | `"Piercing"`, `"Slashing"`, `"Bludgeoning"` |
| `damage_type.key` | string | Required | Damage type key | `"piercing"`, `"slashing"`, `"bludgeoning"` |
| `damage_type.url` | string | Required | API endpoint for damage type | `"https://api.open5e.com/v2/damagetypes/piercing/"` |
| `properties` | array | Required (can be empty) | List of weapon properties | See below |
| `properties[].property` | object | Required | Property metadata | See below |
| `properties[].property.name` | string | Required | Property name | `"Finesse"`, `"Light"`, `"Topple"` |
| `properties[].property.type` | string\|null | Optional | Property category (e.g., "Mastery") | `"Mastery"` or `null` |
| `properties[].property.url` | string | Required | API endpoint for property | `"/v2/weaponproperties/srd-2024_finesse-wp/"` |
| `properties[].detail` | string\|null | Optional | Additional detail (e.g., versatile dice) | `"1d10"` (for Versatile), `null` |
| `range` | float | Required | Normal range in distance units | `0.0`, `20.0`, `25.0`, `100.0` |
| `long_range` | float | Required | Long range in distance units | `0.0`, `60.0`, `100.0` |
| `distance_unit` | string | Required | Unit of distance measurement | `"feet"` |
| `is_simple` | boolean | Required | Whether weapon is Simple (vs Martial) | `true`, `false` |
| `is_improvised` | boolean | Required | Whether weapon is improvised | `true`, `false` |
| `document` | object | Required | Source document metadata | See below |

#### Document Object Structure
```json
{
  "name": "System Reference Document 5.2",
  "key": "srd-2024",
  "display_name": "5e 2024 Rules",
  "publisher": {
    "name": "Wizards of the Coast",
    "key": "wizards-of-the-coast",
    "url": "https://api.open5e.com/v2/publishers/wizards-of-the-coast/"
  },
  "gamesystem": {
    "name": "5th Edition 2024",
    "key": "5e-2024",
    "url": "https://api.open5e.com/v2/gamesystems/5e-2024/"
  },
  "permalink": "https://dnd.wizards.com/resources/systems-reference-document"
}
```

---

## Current Model Structure

**File:** `src/lorekeeper_mcp/api_clients/models/equipment.py`

```python
class Weapon(BaseModel):
    """Model representing a D&D 5e weapon."""

    category: str = Field(..., description="Weapon category (Simple/Martial, Melee/Ranged)")
    damage_dice: str = Field(..., description="Damage dice (e.g., 1d8)")
    damage_type: str = Field(..., description="Damage type (slashing, piercing, bludgeoning)")
    cost: str = Field(..., description="Cost in gold pieces")
    weight: float = Field(..., ge=0, description="Weight in pounds")

    properties: list[str] | None = Field(None, description="Weapon properties")
    range_normal: int | None = Field(None, description="Normal range in feet")
    range_long: int | None = Field(None, description="Long range in feet")
    versatile_dice: str | None = Field(None, description="Versatile damage dice")
```

Plus inherited from `BaseModel`:
```python
class BaseModel(PydanticBaseModel):
    name: str = Field(..., description="Name of the item")
    slug: str = Field(..., description="URL-safe identifier")
    desc: str | None = Field(None, description="Description text")
    document_url: str | None = Field(None, description="Source document URL")
```

---

## Field-by-Field Comparison

### Fields in API but Missing from Model

| API Field | Type | Importance | Notes |
|-----------|------|-----------|-------|
| `key` | string | HIGH | Unique identifier. Currently model uses `slug` |
| `url` | string | MEDIUM | Full API endpoint. Could be useful for pagination/linking |
| `damage_type.key` | string | HIGH | For programmatic filtering/comparison |
| `damage_type.url` | string | MEDIUM | Link to damage type resource |
| `damage_type.name` | string | HIGH | Human-readable damage type |
| `properties[].property.name` | string | HIGH | Property names with proper casing |
| `properties[].property.type` | string\|null | MEDIUM | Distinguishes Mastery vs regular properties (5e 2024) |
| `properties[].property.url` | string | MEDIUM | Link to property resource |
| `properties[].detail` | string\|null | HIGH | Extra detail (e.g., Versatile damage dice) |
| `distance_unit` | string | MEDIUM | Always "feet" in current data, but could vary |
| `is_simple` | boolean | HIGH | Distinguishes Simple vs Martial weapons |
| `is_improvised` | boolean | MEDIUM | Indicates improvised weapons |
| `document` | object | MEDIUM | Full source document metadata (currently only `document_url`) |
| `document.publisher` | object | LOW | Publisher information |
| `document.gamesystem` | object | LOW | Game system information |

### Fields in Model but Missing from API

| Model Field | Type | Requirement | Notes |
|-------------|------|-------------|-------|
| `cost` | string | Required | **NOT IN API** - Cannot be populated |
| `weight` | float | Required | **NOT IN API** - Cannot be populated |
| `category` | string | Required | **CAN BE DERIVED** from `is_simple`; cannot directly populate |
| `desc` (inherited) | string\|null | Optional | **NOT IN API** - No description data |
| `range_normal` | int\|null | Optional | **TYPE MISMATCH** - API uses float, model expects int |
| `range_long` | int\|null | Optional | **TYPE MISMATCH** - API uses float, model expects int |
| `versatile_dice` | string\|null | Optional | **NESTED IN PROPERTIES** - Must extract from `properties[].detail` where `properties[].property.name == "Versatile"` |

### Critical Type Mismatches

#### 1. `damage_type` (CRITICAL)
- **Model expects:** `str` (e.g., `"piercing"`)
- **API provides:** `object` with structure:
  ```json
  {
    "name": "Piercing",
    "key": "piercing",
    "url": "https://api.open5e.com/v2/damagetypes/piercing/"
  }
  ```
- **Impact:** Current model cannot deserialize API response
- **Fix needed:** Create `DamageType` nested model or alias to extract the key

#### 2. `range` and `long_range` (MODERATE)
- **Model expects:** `int` (e.g., `20`)
- **API provides:** `float` (e.g., `20.0`)
- **Impact:** Type validation failure if strict
- **Fix needed:** Accept `float` or coerce from API

#### 3. `properties` (MODERATE)
- **Model expects:** `list[str]` (e.g., `["Finesse", "Light"]`)
- **API provides:** Complex array of objects:
  ```json
  [
    {
      "property": {
        "name": "Finesse",
        "type": null,
        "url": "/v2/weaponproperties/srd-2024_finesse-wp/"
      },
      "detail": null
    }
  ]
  ```
- **Impact:** Cannot directly deserialize
- **Fix needed:** Create property models or extract property names

---

## Pattern Analysis Across Multiple Weapons

Examined 10 weapons (Battleaxe, Blowgun, Club, Dagger, Dart, Flail, Glaive, Greataxe, Greatclub, Greatsword):

### Consistent Patterns
- All weapons have `name`, `key`, `damage_dice`, `damage_type` object
- All have `range`, `long_range`, `distance_unit`, `is_simple`, `is_improvised`
- All have `properties` array (never null, but can be empty)
- All have `document` object with same structure
- `damage_type` is always an object with `name`, `key`, `url`

### Variations Observed
- Melee weapons: `range: 0.0, long_range: 0.0`
- Ranged weapons: `range: 20.0+, long_range: 60.0+`
- `is_simple` varies: `true` for simple weapons, `false` for martial
- Properties vary: some have Mastery properties (2024 rules feature), some only regular properties
- `properties[].detail` populated only for properties that need it (e.g., Versatile with "1d10")
- `damage_dice` can be various formats: `"1d4"`, `"2d6"`, `"1"` (single damage)

### Never Observed as Null/Missing
- `url`, `key`, `name`, `damage_dice`
- `damage_type` (entire object)
- `range`, `long_range`, `distance_unit`
- `is_simple`, `is_improvised`
- `document`
- `properties` (but can be empty array)

### Difficult to Obtain/Not in API
- `cost` - Not available in API v2
- `weight` - Not available in API v2
- `desc` - Not available in API v2

---

## Recommendations for Model Redesign

### 1. Create Nested Models
```python
class DamageType(BaseModel):
    """Damage type with metadata."""
    name: str
    key: str
    url: str

class PropertyDetail(BaseModel):
    """Weapon property with optional mastery type."""
    name: str
    type: str | None = None  # e.g., "Mastery"
    url: str

class WeaponProperty(BaseModel):
    """Weapon property with optional detail."""
    property: PropertyDetail
    detail: str | None = None  # e.g., "1d10" for Versatile
```

### 2. Redesign Weapon Model
```python
class Weapon(BaseModel):
    """Model representing a D&D 5e weapon."""

    # Core fields - Required
    name: str
    key: str  # Unique identifier (replaces/supplements slug)
    damage_dice: str
    damage_type: DamageType  # Changed from str
    is_simple: bool  # Replaces derived "category"

    # Range information
    range: float  # Changed from int, renamed from range_normal
    long_range: float  # Changed from int
    distance_unit: str  # New: always "feet" currently

    # Properties
    properties: list[WeaponProperty]  # Changed to full objects

    # Improvised status
    is_improvised: bool

    # Document reference
    document: DocumentMetadata  # New, replaces simple document_url

    # Optional/Deprecated fields
    # These cannot be populated from API v2:
    # - cost
    # - weight
    # - desc
```

### 3. Handle Missing Fields
- **Option A:** Remove from model entirely (breaking change)
- **Option B:** Make optional with defaults
- **Option C:** Create separate enrichment layer for additional data
- **Recommendation:** Option B initially, with plan to source data separately

### 4. Extract Versatile Damage
```python
def get_versatile_dice(self) -> str | None:
    """Extract versatile damage dice from properties if available."""
    for prop in self.properties:
        if prop.property.name == "Versatile":
            return prop.detail
    return None
```

### 5. Category Derivation
Instead of required `category` field, derive it:
```python
@property
def category(self) -> str:
    """Derive weapon category from is_simple flag."""
    simple_part = "Simple" if self.is_simple else "Martial"
    # Determine melee vs ranged from range
    range_part = "Ranged" if self.range > 0 else "Melee"
    return f"{simple_part} {range_part}"
```

---

## Action Items for Task 2.2

1. **Create DamageType model** - Handle object instead of string
2. **Create WeaponProperty model** - Handle complex property structure
3. **Update Weapon model** - Change type hints and field names
4. **Add extraction helpers** - Methods to get versatile dice, category, etc.
5. **Handle optional fields** - Provide sensible defaults for cost/weight/desc
6. **Update client code** - Ensure deserialization works
7. **Write tests** - Validate against real API responses
8. **Check dependent code** - Update any code using the old Weapon structure

---

## Conclusion

The Open5e API v2 weapon structure is fundamentally incompatible with the current model:

- **Critical issue:** `damage_type` is an object, not a string
- **Major issue:** Properties are complex objects, not simple strings
- **Data gaps:** Cost, weight, description unavailable from API
- **New capabilities:** Better metadata (document, mastery types, source info)

The model needs substantial refactoring. The recommended approach is to create nested models for `DamageType` and `WeaponProperty`, redesign the Weapon class, and create helper methods for derived/extracted fields.
