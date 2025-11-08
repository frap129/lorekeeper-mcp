# weapon-model-correction Specification

## Purpose
TBD - created by archiving change fix-open5e-api-issues. Update Purpose after archive.
## Requirements
### Requirement: Accurate API Response Modeling
The `Weapon` Pydantic model SHALL accurately reflect the actual structure and field types returned by the Open5e API v2 weapons endpoint.

**Rationale**: The current `Weapon` model contains fields that don't exist in the API response and uses incorrect data types, causing validation errors when parsing weapon data.

**Scope**: `src/lorekeeper_mcp/api_clients/models/equipment.py` - `Weapon` class

**Related Capabilities**:
- Impacts: `equipment-lookup` tool
- Depends on: None (standalone model fix)
- Related: May affect armor model if similar issues exist

#### Scenario: Verify weapon model validation works with real API data
- **Given**: The corrected Weapon model is used
- **When**: Equipment lookup is performed for weapons
- **Then**: No Pydantic validation errors occur

### Requirement: Weapon Model Field Structure
The `Weapon` model SHALL be updated to match the Open5e API v2 weapon response structure.

**Before** (Current incorrect model):
```python
class Weapon(BaseModel):
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

**After** (Corrected model based on API response):
```python
class Weapon(BaseModel):
    # Fields that exist in API response with correct types
    name: str = Field(..., description="Weapon name")
    damage_dice: str = Field(..., description="Damage dice (e.g., 1d8)")
    damage_type: dict | list[dict] = Field(..., description="Damage type information")
    weight: float = Field(..., ge=0, description="Weight in pounds")
    cost: str = Field(..., description="Cost in gold pieces")

    # Optional fields from API response
    properties: list[str] | None = Field(None, description="Weapon properties")
    range_normal: int | None = Field(None, description="Normal range in feet")
    range_long: int | None = Field(None, description="Long range in feet")
    versatile_dice: str | None = Field(None, description="Versatile damage dice")
    weapon_range: str = Field(None, description="Melee or Ranged classification")
    throw_range: dict | None = Field(None, description="Throw range information")
```

**File**: `src/lorekeeper_mcp/api_clients/models/equipment.py`

#### Scenario: Parse simple weapon response
- **Given**: API returns a basic weapon like "Longsword"
- **When**: `Weapon.model_validate()` is called with the response
- **Then**: Model validation succeeds without errors
- **And**: All relevant weapon fields are properly extracted

#### Scenario: Parse complex weapon with properties
- **Given**: API returns a weapon with special properties like "Longbow"
- **When**: `Weapon.model_validate()` is called with the response
- **Then**: Model validation succeeds including optional property fields
- **And**: Properties list is correctly populated

#### Scenario: Handle weapons with damage type objects
- **Given**: API returns weapon with nested damage type information
- **When**: `Weapon.model_validate()` is called with the response
- **Then**: Model handles both dict and list[dict] damage_type formats
- **And**: No validation errors occur

### Requirement: Equipment Lookup Integration
The `lookup_equipment` tool SHALL continue to work seamlessly with the corrected weapon model.

**Before**: Equipment lookup fails with Pydantic validation errors when processing weapons

**After**: Equipment lookup successfully processes all weapon types without validation errors

**File**: `src/lorekeeper_mcp/tools/equipment_lookup.py`

#### Scenario: Lookup weapons by name
- **Given**: User calls `lookup_equipment(type="weapon", name="sword")`
- **When**: Tool fetches weapons from Open5e v2 API
- **Then**: Weapons are successfully parsed using the corrected model
- **And**: Valid weapon data is returned in the response

#### Scenario: Filter weapons by damage dice
- **Given**: User calls `lookup_equipment(type="weapon", damage_dice="1d8")`
- **When**: Tool fetches and processes weapons from API
- **Then**: Weapons are successfully validated and filtered
- **And**: Only weapons with 1d8 damage are returned

### Requirement: Non-Existent Fields
Fields that don't exist in the Open5e API v2 weapon response SHALL be removed.

**Removed Fields**:
- `category: str` - This field doesn't exist in the API response
- Any other fields not present in actual API responses

**Rationale**: Including non-existent fields causes model validation to fail when the API response doesn't contain these fields.

#### Scenario: Validate model with API response structure
- **Given**: The Weapon model accurately reflects API response structure
- **When**: `Weapon.model_validate()` is called with real API response
- **Then**: Model validation succeeds without requiring non-existent fields
- **And**: No validation errors for missing fields not in API
- **And**: All existing API response fields are properly parsed

#### Scenario: Verify API response field accuracy
- **Given**: A sample of Open5e v2 weapon API responses
- **When**: Analyzing the response structure
- **Then**: Model only includes fields present in API responses
- **And**: No fields in model are absent from API data
- **And**: Field types match API response structure

#### Scenario: Equipment lookup integration
- **Given**: Equipment lookup tool uses Weapon model matching API structure
- **When**: User calls `lookup_equipment(type="weapon", name="longsword")`
- **Then**: Weapon data is successfully parsed and returned
- **And**: All weapon properties from API are accessible in results
- **And**: Model validation works seamlessly with API responses

## Validation Criteria

1. **Model Validation**: All sample weapon responses from Open5e API v2 validate successfully
2. **Type Safety**: Damage type and other complex fields use appropriate data types
3. **Backward Compatibility**: Equipment lookup continues to return expected data structure
4. **Error Handling**: No Pydantic validation errors when processing real API responses

## Success Metrics

- 100% of weapon API responses validate successfully against the new model
- Zero Pydantic validation errors when processing weapon data
- Equipment lookup tool returns expected weapon information
- No breaking changes to the public equipment lookup interface

## API Research Notes

Before implementing this fix, the actual Open5e v2 weapons API response structure should be verified by making a test request:
```bash
curl "https://api.open5e.com/v2/weapons/?limit=1" -H "Accept: application/json"
```

This ensures the model accurately reflects the real API response structure rather than assumptions.
