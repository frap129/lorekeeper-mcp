# Open5e /v2/search/ Endpoint Test Results

**Date**: 2025-11-11
**Endpoint**: https://api.open5e.com/v2/search/
**Total Tests**: 10
**Successful**: 10
**Errors**: 0

## Test Details

### Test 1: Test 1: Basic Exact Query

**Description**: Search for 'Fireball' spell with defaults

**Parameters**:
```json
{
  "query": "Fireball"
}
```

**Status**: SUCCESS

**Results Found**: 50

**Top Result**:
```json
{
  "document": {
    "key": "a5e-ag",
    "name": "Adventurer's Guide"
  },
  "object_pk": "a5e-ag_fireball",
  "object_name": "Fireball",
  "object": {
    "school": "Evocation",
    "level": 3
  },
  "object_model": "Spell",
  "schema_version": "v2",
  "route": "v2/spells/",
  "text": "Fireball\n\nA fiery mote streaks to a point within range and explodes in a burst of flame. The fire spreads around corners and ignites unattended flammable objects. Each creature in the area takes 6d6 fire damage.",
  "highlighted": "<span class=\"highlighted\">Fireball</span>\n\nA fiery mote streaks to a point within range and explodes in a burst of flame. The fire spreads...",
  "match_type": "exact",
  "matched_term": "Fireball",
  "match_score": 1.0
}
```

### Test 2: Test 2: Fuzzy Matching - Typo

**Description**: Search for 'firbal' (typo) with fuzzy=true

**Parameters**:
```json
{
  "query": "firbal",
  "fuzzy": true
}
```

**Status**: SUCCESS

**Results Found**: 4

**Top Result**:
```json
{
  "document": {
    "key": "a5e-ag",
    "name": "Adventurer's Guide"
  },
  "object_pk": "a5e-ag_delayed-blast-fireball",
  "object_name": "Delayed Blast Fireball",
  "object": {
    "school": "Evocation",
    "level": 7
  },
  "object_model": "Spell",
  "schema_version": "v2",
  "route": "v2/spells/",
  "text": "Delayed Blast Fireball\n\nA glowing bead of yellow light flies from your finger and lingers at a point at the center of the area until you end the spell\u2014either because your concentration is broken or because you choose to end it\u2014and the bead detonates. Each creature in the area takes 12d6 fire damage. If at the end of your turn the bead has not yet detonated, the damage increases by 1d6.\n\nIf touched before the spell ends, the creature touching the bead makes a Dexterity saving throw or the bead detonates. On a successful save, the creature can use an action to throw the bead up to 40 feet, moving the area with it. If the bead strikes a creature or solid object, the bead detonates.\n\nThe fire spreads around corners, and it damages and ignites any flammable unattended objects in the area.",
  "highlighted": "Delayed Blast <span class=\"highlighted\">Fireball</span>\n\nA glowing bead of yellow light flies from your finger and lingers at a point at the center of the area until you end the spell\u2014either because your concentration is broken or because you choose to end it\u2014and the bead detonates. Each creature in the area takes 12d6 fire damage. If at the end of your turn the bead has not yet detonated, the damage increases by 1d6.\n\nIf touched before the spell ends, the creature touching the bead makes a Dexterity saving throw or the bead detonates. On a successful save, the creature can use an action to throw the bead up to 40 feet, moving the area with it. If the bead strikes a creature or solid object, the bead detonates.\n\nThe fire spreads around corners, and it damages and ignites any flammable unattended objects in the area.",
  "match_type": "fuzzy",
  "matched_term": "fireball",
  "match_score": 0.8571428571428572
}
```

### Test 3: Test 3: Typo without Fuzzy

**Description**: Search for 'firbal' (typo) with fuzzy=false

**Parameters**:
```json
{
  "query": "firbal",
  "fuzzy": false
}
```

**Status**: SUCCESS

**Results Found**: 4

**Top Result**:
```json
{
  "document": {
    "key": "a5e-ag",
    "name": "Adventurer's Guide"
  },
  "object_pk": "a5e-ag_delayed-blast-fireball",
  "object_name": "Delayed Blast Fireball",
  "object": {
    "school": "Evocation",
    "level": 7
  },
  "object_model": "Spell",
  "schema_version": "v2",
  "route": "v2/spells/",
  "text": "Delayed Blast Fireball\n\nA glowing bead of yellow light flies from your finger and lingers at a point at the center of the area until you end the spell\u2014either because your concentration is broken or because you choose to end it\u2014and the bead detonates. Each creature in the area takes 12d6 fire damage. If at the end of your turn the bead has not yet detonated, the damage increases by 1d6.\n\nIf touched before the spell ends, the creature touching the bead makes a Dexterity saving throw or the bead detonates. On a successful save, the creature can use an action to throw the bead up to 40 feet, moving the area with it. If the bead strikes a creature or solid object, the bead detonates.\n\nThe fire spreads around corners, and it damages and ignites any flammable unattended objects in the area.",
  "highlighted": "Delayed Blast <span class=\"highlighted\">Fireball</span>\n\nA glowing bead of yellow light flies from your finger and lingers at a point at the center of the area until you end the spell\u2014either because your concentration is broken or because you choose to end it\u2014and the bead detonates. Each creature in the area takes 12d6 fire damage. If at the end of your turn the bead has not yet detonated, the damage increases by 1d6.\n\nIf touched before the spell ends, the creature touching the bead makes a Dexterity saving throw or the bead detonates. On a successful save, the creature can use an action to throw the bead up to 40 feet, moving the area with it. If the bead strikes a creature or solid object, the bead detonates.\n\nThe fire spreads around corners, and it damages and ignites any flammable unattended objects in the area.",
  "match_type": "fuzzy",
  "matched_term": "fireball",
  "match_score": 0.8571428571428572
}
```

### Test 4: Test 4: Vector/Semantic Search

**Description**: Search for 'healing magic' concept with vector=true

**Parameters**:
```json
{
  "query": "healing magic",
  "vector": true
}
```

**Status**: SUCCESS

**Results Found**: 50

**Top 3 Results**:
1. Unknown
2. Unknown
3. Unknown

### Test 5: Test 5: Concept without Vector

**Description**: Search for 'healing magic' with vector=false

**Parameters**:
```json
{
  "query": "healing magic",
  "vector": false
}
```

**Status**: SUCCESS

**Results Found**: 30

### Test 6: Test 6: Object Model Filter - Spell

**Description**: Search for 'cure wounds' filtering to Spell only

**Parameters**:
```json
{
  "query": "cure wounds",
  "object_model": "Spell"
}
```

**Status**: SUCCESS

**Results Found**: 7

**Top Result**:
```json
{
  "document": {
    "key": "a5e-ag",
    "name": "Adventurer's Guide"
  },
  "object_pk": "a5e-ag_cure-wounds",
  "object_name": "Cure Wounds",
  "object": {
    "school": "Evocation",
    "level": 1
  },
  "object_model": "Spell",
  "schema_version": "v2",
  "route": "v2/spells/",
  "text": "Cure Wounds\n\nThe target regains hit points equal to 1d8 + your spellcasting ability modifier.",
  "highlighted": "<span class=\"highlighted\">Cure</span> <span class=\"highlighted\">Wounds</span>\n\nThe target regains hit points equal to 1d8 + your spellcasting ability modifier.",
  "match_type": "exact",
  "matched_term": "cure wounds",
  "match_score": 1.0
}
```

### Test 7: Test 7: Object Model Filter - Creature

**Description**: Search for 'dragon' filtering to Creature only

**Parameters**:
```json
{
  "query": "dragon",
  "object_model": "Creature"
}
```

**Status**: SUCCESS

**Results Found**: 50

**Top 3 Results**:
1. Unknown
2. Unknown
3. Unknown

### Test 8: Test 8: Fuzzy + Vector

**Description**: Search for 'damge spel' (typo) with both fuzzy and vector

**Parameters**:
```json
{
  "query": "damge spel",
  "fuzzy": true,
  "vector": true
}
```

**Status**: SUCCESS

**Results Found**: 0

### Test 9: Test 9: Fuzzy Matching - Another Typo

**Description**: Search for 'cury wounds' (typo) with fuzzy=true

**Parameters**:
```json
{
  "query": "cury wounds",
  "fuzzy": true
}
```

**Status**: SUCCESS

**Results Found**: 0

### Test 10: Test 10: Strict Mode

**Description**: Search with strict=true (only explicit match types)

**Parameters**:
```json
{
  "query": "fireball",
  "fuzzy": true,
  "strict": true
}
```

**Status**: SUCCESS

**Results Found**: 1

## Key Findings

### Fuzzy Matching
✓ Fuzzy matching is supported
- firbal: 4 results
- firbal: 4 results
- damge spel: 0 results
- cury wounds: 0 results

### Vector/Semantic Search
✓ Vector/semantic search is supported
- healing magic: 50 results
- healing magic: 30 results
- damge spel: 0 results

### Object Model Filtering
✓ Object model filtering is supported
- Spell: 7 results
- Creature: 50 results
