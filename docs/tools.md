# LoreKeeper MCP Tools Specification

This document defines the MCP tools for LoreKeeper, organized by domain.

## API Assignment Strategy

- **Prefer Open5e API** over D&D 5e API
- **Prefer Open5e v2** over v1 when available
- **Use D&D 5e API** only for content not available in Open5e (primarily rules)
- **Each category maps to ONE API** to avoid complexity

---

## Tool 1: `lookup_spell`

**Purpose**: Search and retrieve spell information

**API**: Open5e `/v2/spells/` (primary, comprehensive)

**Parameters**:
- `name` (string, optional): Spell name or partial name search
- `level` (integer, optional): Spell level (0-9, cantrips are 0)
- `school` (string, optional): Magic school name (e.g., "evocation", "abjuration")
- `class_key` (string, optional): Filter by class key (e.g., "wizard", "cleric")
- `concentration` (boolean, optional): Only concentration spells
- `ritual` (boolean, optional): Only ritual spells
- `casting_time` (string, optional): Casting time (e.g., "action", "1 Minute", "Reaction")
- `limit` (integer, optional, default=20): Maximum results to return

**Available Values**:
- **Schools**: abjuration, conjuration, divination, enchantment, evocation, illusion, necromancy, transmutation
- **Casting Times**: Reaction, 1 Bonus Action, 1 Action, 1 Turn, 1 Round, 1 Minute, 5 Minutes, 10 Minutes, 1 Hour, etc.

**Returns**: List of spells with:
- Name, level, school
- Components (V/S/M), material details, cost
- Casting time, range, duration
- Concentration requirement
- Description, higher level effects
- Classes that can cast it
- Damage roll (if applicable)
- Saving throw ability (if applicable)

**Example Queries**:
- "What does Fireball do?" → `name="fireball"`
- "Show me 3rd level wizard evocation spells" → `level=3, class_key="wizard", school="evocation"`
- "Find all concentration spells" → `concentration=true`

---

## Tool 2: `lookup_creature`

**Purpose**: Search and retrieve monster/creature stat blocks

**API**: Open5e `/v1/monsters/` (most comprehensive monster database)

**Parameters**:
- `name` (string, optional): Creature name or partial name search
- `cr` (float, optional): Challenge rating (supports 0.125, 0.25, 0.5, 1-30)
- `cr_min` (float, optional): Minimum CR (for range searches)
- `cr_max` (float, optional): Maximum CR (for range searches)
- `type` (string, optional): Creature type
- `size` (string, optional): Size category
- `limit` (integer, optional, default=20): Maximum results to return

**Available Values**:
- **Types**: aberration, beast, celestial, construct, dragon, elemental, fey, fiend, giant, humanoid, monstrosity, ooze, plant, undead
- **Sizes**: Tiny, Small, Medium, Large, Huge, Gargantuan

**Returns**: Full stat blocks including:
- Basic stats (AC, HP, speed, abilities)
- Saving throws, skills, proficiencies
- Damage vulnerabilities, resistances, immunities
- Condition immunities
- Senses, languages
- Challenge rating
- Special abilities, traits
- Actions, bonus actions, reactions
- Legendary actions (if applicable)
- Lair actions (if applicable)

**Example Queries**:
- "Find CR 5 undead creatures" → `cr=5, type="undead"`
- "Show me the Ancient Red Dragon" → `name="ancient red dragon"`
- "Medium beasts CR 1 or less" → `cr_max=1, type="beast", size="Medium"`

---

## Tool 3: `lookup_character_option`

**Purpose**: Get character creation and advancement options

**API Coverage**:
- **Classes**: Open5e `/v1/classes/` (includes subclasses/archetypes)
- **Races**: Open5e `/v1/races/` (includes subraces)
- **Backgrounds**: Open5e `/v2/backgrounds/`
- **Feats**: Open5e `/v2/feats/`

**Parameters**:
- `type` (string, required): One of: `class`, `race`, `background`, `feat`
- `name` (string, optional): Name or partial name to search
- `limit` (integer, optional, default=20): Maximum results to return

**Returns by Type**:

**Classes**:
- Hit dice, HP progression
- Proficiencies (armor, weapons, tools, saving throws, skills)
- Starting equipment
- Class features table
- Subclasses/archetypes with full descriptions
- Spellcasting ability (if applicable)

**Races**:
- Ability score increases
- Age, alignment, size
- Speed
- Languages
- Darkvision and other senses
- Racial traits
- Subraces (if applicable)

**Backgrounds**:
- Skill proficiencies
- Tool proficiencies
- Languages
- Equipment
- Special features
- Suggested characteristics

**Feats**:
- Prerequisites
- Benefits
- Type (GENERAL, etc.)

**Example Queries**:
- "What features does a Paladin get?" → `type="class", name="paladin"`
- "Show me the Eldritch Knight" → `type="class", name="eldritch knight"`
- "What traits do Half-Elves have?" → `type="race", name="half-elf"`
- "Find the Sharpshooter feat" → `type="feat", name="sharpshooter"`

---

## Tool 4: `lookup_equipment`

**Purpose**: Search for weapons, armor, adventuring gear, and magic items

**API Coverage**:
- **Weapons**: Open5e `/v2/weapons/`
- **Armor**: Open5e `/v2/armor/`
- **Magic Items**: Open5e `/v1/magicitems/`

**Parameters**:
- `type` (string, optional): One of: `weapon`, `armor`, `magic-item`, `all` (default: `all`)
- `name` (string, optional): Item name or partial name
- `rarity` (string, optional): Magic item rarity (common, uncommon, rare, very rare, legendary, artifact)
- `damage_dice` (string, optional): Weapon damage dice (e.g., "1d8", "2d6")
- `is_simple` (boolean, optional): Simple weapons only
- `requires_attunement` (string, optional): For magic items - "requires attunement" or "" (blank)
- `limit` (integer, optional, default=20): Maximum results to return

**Available Weapon Properties** (filters):
- `is_light`: Light weapons
- `is_versatile`: Versatile weapons
- `is_thrown`: Thrown weapons
- `is_finesse`: Finesse weapons
- `is_two_handed`: Two-handed weapons

**Returns by Type**:

**Weapons**:
- Name, damage dice, damage type
- Properties (light, versatile, thrown, finesse, two-handed, etc.)
- Range (normal and long for ranged weapons)
- Simple vs martial

**Armor**:
- Name, armor type (light/medium/heavy/shield)
- AC value
- Strength requirement
- Stealth disadvantage
- Weight, cost

**Magic Items**:
- Name, type, rarity
- Description and effects
- Attunement requirement

**Example Queries**:
- "What's the damage for a longsword?" → `type="weapon", name="longsword"`
- "Show me rare magic weapons" → `type="magic-item", rarity="rare"`
- "Find light armor" → `type="armor"`
- "What does a Bag of Holding do?" → `type="magic-item", name="bag of holding"`

---

## Tool 5: `lookup_rule`

**Purpose**: Look up game rules, mechanics, conditions, and reference information

**API Coverage**:
- **Rules & Rule Sections**: D&D 5e API `/rules/`, `/rule-sections/` (Open5e doesn't have this!)
- **Conditions**: Open5e `/v2/conditions/` (prefer Open5e for conditions)
- **Reference Info**: D&D 5e API (damage-types, weapon-properties, skills, ability-scores, magic-schools, languages, proficiencies, alignments)

**Parameters**:
- `rule_type` (string, required): One of: `rule`, `condition`, `damage-type`, `weapon-property`, `skill`, `ability-score`, `magic-school`, `language`, `proficiency`, `alignment`
- `name` (string, optional): Name or partial name to search
- `section` (string, optional): For rules - section name (e.g., "combat", "spellcasting")
- `limit` (integer, optional, default=20): Maximum results to return

**Available Rule Sections**:
- adventuring
- appendix
- combat
- equipment
- spellcasting
- using-ability-scores

**Returns by Type**:

**Rules**:
- Rule name, description
- Subsections with detailed mechanics
- References to related rules

**Conditions**:
- Condition name
- Full description of effects
- Game mechanical impact

**Reference Info**:
- Description
- Associated mechanics
- Related game elements

**Example Queries**:
- "What does the Grappled condition do?" → `rule_type="condition", name="grappled"`
- "Explain opportunity attacks" → `rule_type="rule", section="combat", name="opportunity attack"`
- "What is radiant damage?" → `rule_type="damage-type", name="radiant"`
- "How does the Stealth skill work?" → `rule_type="skill", name="stealth"`
- "What are weapon properties?" → `rule_type="weapon-property"`

---

## Implementation Notes

### Caching Strategy
All API responses should be cached in SQLite with:
- Endpoint URL as key
- Response JSON as value
- Timestamp for cache invalidation
- TTL: 7 days (game data rarely changes)

### Error Handling
- If primary API fails, log error and return user-friendly message
- Don't automatically fall back to D&D 5e API unless specified in design
- Cache errors with short TTL (5 minutes) to avoid hammering failed endpoints

### Search Behavior
- **Exact match**: If `name` parameter exactly matches, return single result
- **Partial match**: If `name` is partial, return up to `limit` results ranked by relevance
- **No name**: If no `name` provided, filter by other parameters and return up to `limit` results

### Response Formatting
- Return structured data suitable for AI consumption
- Include source attribution (document name/title)
- Format text descriptions as markdown where appropriate
- Include URLs to original API resources for reference

---

## API Endpoint Summary

### Primary APIs by Tool

| Tool | Category | API Endpoint | Version |
|------|----------|-------------|---------|
| lookup_spell | Spells | Open5e `/v2/spells/` | v2 ✓ |
| lookup_creature | Monsters | Open5e `/v1/monsters/` | v1 |
| lookup_character_option | Classes | Open5e `/v1/classes/` | v1 |
| lookup_character_option | Races | Open5e `/v1/races/` | v1 |
| lookup_character_option | Backgrounds | Open5e `/v2/backgrounds/` | v2 ✓ |
| lookup_character_option | Feats | Open5e `/v2/feats/` | v2 ✓ |
| lookup_equipment | Weapons | Open5e `/v2/weapons/` | v2 ✓ |
| lookup_equipment | Armor | Open5e `/v2/armor/` | v2 ✓ |
| lookup_equipment | Magic Items | Open5e `/v1/magicitems/` | v1 |
| lookup_rule | Rules | D&D 5e API `/rules/`, `/rule-sections/` | Official |
| lookup_rule | Conditions | Open5e `/v2/conditions/` | v2 ✓ |
| lookup_rule | Reference | D&D 5e API (various) | Official |

### Why Each API Was Chosen
- **Open5e v2 preferred**: More comprehensive, better structured, includes community content
- **Open5e v1 for monsters/classes**: Most complete database with extensive third-party content
- **D&D 5e API for rules**: Open5e doesn't have detailed rule mechanics - this is the fallback's primary use case
