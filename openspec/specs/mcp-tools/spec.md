# mcp-tools Specification

## Purpose
TBD - created by archiving change implement-mcp-tools. Update Purpose after archive.
## Requirements
### Requirement: Spell Lookup Tool
The system SHALL provide a `lookup_spell` tool that searches and retrieves spell information from the Open5e v2 API.

**Parameters:**
- `name` (string, optional): Spell name or partial name search
- `level` (integer, optional): Spell level (0-9, where 0 represents cantrips)
- `school` (string, optional): Magic school (abjuration, conjuration, divination, enchantment, evocation, illusion, necromancy, transmutation)
- `class_key` (string, optional): Filter by class (wizard, cleric, druid, etc.)
- `concentration` (boolean, optional): Filter for concentration spells only
- `ritual` (boolean, optional): Filter for ritual spells only
- `casting_time` (string, optional): Casting time filter (e.g., "1 Action", "1 Bonus Action", "Reaction")
- `limit` (integer, optional, default=20): Maximum number of results to return

**Returns:** List of spell objects containing:
- Name, level, school
- Components (verbal, somatic, material) with material details
- Casting time, range, duration
- Concentration requirement
- Full description text
- Higher level effects (if applicable)
- Available classes
- Source document attribution

#### Scenario: Lookup spell by exact name
**Given** a user queries for spell with `name="Fireball"`
**When** the tool is invoked
**Then** the system returns the Fireball spell details from Open5e v2 API
**And** includes damage dice, saving throw, and area of effect information

#### Scenario: Filter spells by level and class
**Given** a user queries with `level=3` and `class_key="wizard"`
**When** the tool is invoked
**Then** the system returns all 3rd-level wizard spells up to the limit
**And** results are sorted by name

#### Scenario: Find concentration spells
**Given** a user queries with `concentration=true`
**When** the tool is invoked
**Then** the system returns only spells that require concentration
**And** the limit parameter restricts the result count

#### Scenario: Handle spell not found
**Given** a user queries for `name="NonexistentSpell123"`
**When** the tool is invoked
**Then** the system returns an empty list
**And** does not raise an error

---

### Requirement: Creature Lookup Tool
The system SHALL provide a `lookup_creature` tool that searches and retrieves monster/creature stat blocks from the Open5e v1 API.

**Parameters:**
- `name` (string, optional): Creature name or partial name search
- `cr` (float, optional): Exact challenge rating (supports 0.125, 0.25, 0.5, 1-30)
- `cr_min` (float, optional): Minimum CR for range searches
- `cr_max` (float, optional): Maximum CR for range searches
- `type` (string, optional): Creature type (aberration, beast, celestial, construct, dragon, elemental, fey, fiend, giant, humanoid, monstrosity, ooze, plant, undead)
- `size` (string, optional): Size category (Tiny, Small, Medium, Large, Huge, Gargantuan)
- `limit` (integer, optional, default=20): Maximum number of results

**Returns:** List of creature stat blocks containing:
- Name, size, type, alignment
- Armor class, hit points, speed
- Ability scores (STR, DEX, CON, INT, WIS, CHA)
- Saving throws, skills, proficiencies
- Damage vulnerabilities, resistances, immunities
- Condition immunities
- Senses, languages
- Challenge rating and experience points
- Special abilities and traits
- Actions, bonus actions, reactions
- Legendary actions (if applicable)
- Source document attribution

#### Scenario: Lookup creature by exact name
**Given** a user queries for `name="Ancient Red Dragon"`
**When** the tool is invoked
**Then** the system returns the complete stat block for Ancient Red Dragon
**And** includes legendary actions and lair actions

#### Scenario: Filter by challenge rating and type
**Given** a user queries with `cr=5` and `type="undead"`
**When** the tool is invoked
**Then** the system returns all CR 5 undead creatures
**And** results include creatures like Wraith

#### Scenario: Filter by CR range
**Given** a user queries with `cr_min=1` and `cr_max=3`
**When** the tool is invoked
**Then** the system returns creatures with CR between 1 and 3 inclusive
**And** respects the limit parameter

#### Scenario: Handle fractional CR values
**Given** a user queries with `cr=0.25`
**When** the tool is invoked
**Then** the system correctly filters for CR 1/4 creatures
**And** returns appropriate low-level monsters

---

### Requirement: Character Option Lookup Tool
The system SHALL provide a `lookup_character_option` tool that retrieves character creation and advancement options including classes, races, backgrounds, and feats.

**Parameters:**
- `type` (string, required): One of: `class`, `race`, `background`, `feat`
- `name` (string, optional): Name or partial name search
- `limit` (integer, optional, default=20): Maximum number of results

**API Routing:**
- `class` → Open5e v1 `/classes/`
- `race` → Open5e v1 `/races/`
- `background` → Open5e v2 `/backgrounds/`
- `feat` → Open5e v2 `/feats/`

**Returns (varies by type):**

**Classes:**
- Hit dice, HP progression
- Proficiencies (armor, weapons, tools, saving throws, skills)
- Starting equipment
- Class features by level
- Subclasses/archetypes
- Spellcasting ability (if applicable)

**Races:**
- Ability score increases
- Age, alignment, size
- Speed, languages
- Racial traits
- Subraces (if applicable)

**Backgrounds:**
- Skill proficiencies
- Tool/language proficiencies
- Equipment
- Special features

**Feats:**
- Prerequisites
- Benefits and mechanical effects
- Type classification

#### Scenario: Lookup class by name
**Given** a user queries with `type="class"` and `name="Paladin"`
**When** the tool is invoked
**Then** the system returns Paladin class details from Open5e v1
**And** includes all class features and subclasses

#### Scenario: Lookup race with subraces
**Given** a user queries with `type="race"` and `name="Elf"`
**When** the tool is invoked
**Then** the system returns Elf racial traits
**And** includes High Elf, Wood Elf, and Drow subraces

#### Scenario: Find feat by name
**Given** a user queries with `type="feat"` and `name="Sharpshooter"`
**When** the tool is invoked
**Then** the system returns the Sharpshooter feat from Open5e v2
**And** includes prerequisites and benefits

#### Scenario: Invalid type parameter
**Given** a user queries with `type="invalid-type"`
**When** the tool is invoked
**Then** the system returns a validation error
**And** provides valid type options (class, race, background, feat)

---

### Requirement: Equipment Lookup Tool
The system SHALL provide a `lookup_equipment` tool that searches for weapons, armor, adventuring gear, and magic items.

**Parameters:**
- `type` (string, optional, default="all"): One of: `weapon`, `armor`, `magic-item`, `all`
- `name` (string, optional): Item name or partial name search
- `rarity` (string, optional): Magic item rarity (common, uncommon, rare, very rare, legendary, artifact)
- `damage_dice` (string, optional): Weapon damage dice filter (e.g., "1d8", "2d6")
- `is_simple` (boolean, optional): Filter for simple weapons only
- `requires_attunement` (string, optional): Attunement requirement filter
- `limit` (integer, optional, default=20): Maximum number of results

**API Routing:**
- `weapon` → Open5e v2 `/weapons/`
- `armor` → Open5e v2 `/armor/`
- `magic-item` → Open5e v1 `/magicitems/`
- `all` → Query all endpoints and merge results

**Returns (varies by type):**

**Weapons:**
- Name, category (simple/martial)
- Damage dice and damage type
- Properties (light, finesse, two-handed, versatile, etc.)
- Range (for ranged weapons)
- Weight, cost

**Armor:**
- Name, armor category (light/medium/heavy/shield)
- AC value and calculation
- Strength requirement
- Stealth disadvantage
- Weight, cost

**Magic Items:**
- Name, type, rarity
- Description and magical effects
- Attunement requirement
- Source document

#### Scenario: Lookup weapon by name
**Given** a user queries with `type="weapon"` and `name="Longsword"`
**When** the tool is invoked
**Then** the system returns longsword details from Open5e v2
**And** includes damage (1d8/1d10 versatile) and properties

#### Scenario: Filter simple weapons
**Given** a user queries with `type="weapon"` and `is_simple=true`
**When** the tool is invoked
**Then** the system returns only simple weapons
**And** excludes martial weapons

#### Scenario: Find rare magic items
**Given** a user queries with `type="magic-item"` and `rarity="rare"`
**When** the tool is invoked
**Then** the system returns all rare magic items
**And** includes items like Flame Tongue and Cloak of Displacement

#### Scenario: Search all equipment types
**Given** a user queries with `type="all"` and `name="chain"`
**When** the tool is invoked
**Then** the system searches weapons, armor, and magic items
**And** returns chain mail armor and chain weapons in merged results

---

### Requirement: Rule Lookup Tool
The system SHALL provide a `lookup_rule` tool that retrieves game rules, conditions, and reference information.

**Parameters:**
- `type` (string, required): One of: `rule`, `condition`, `damage-type`, `weapon-property`, `skill`, `ability-score`, `magic-school`, `language`, `proficiency`, `alignment`
- `name` (string, optional): Name or partial name search
- `section` (string, optional): For rules - section name (combat, spellcasting, adventuring, etc.)
- `limit` (integer, optional, default=20): Maximum number of results

**API Routing:**
- `rule` → D&D 5e API `/rules/`
- `condition` → Open5e v2 `/conditions/`
- `damage-type` → D&D 5e API `/damage-types/`
- `weapon-property` → D&D 5e API `/weapon-properties/`
- `skill` → D&D 5e API `/skills/`
- `ability-score` → D&D 5e API `/ability-scores/`
- `magic-school` → D&D 5e API `/magic-schools/`
- `language` → D&D 5e API `/languages/`
- `proficiency` → D&D 5e API `/proficiencies/`
- `alignment` → D&D 5e API `/alignments/`

**Returns (varies by type):**
- Name and description
- Mechanical effects
- Related rules and references
- Source document attribution

#### Scenario: Lookup condition by name
**Given** a user queries with `type="condition"` and `name="Grappled"`
**When** the tool is invoked
**Then** the system returns the Grappled condition from Open5e v2
**And** includes full description of mechanical effects

#### Scenario: Find combat rules
**Given** a user queries with `type="rule"` and `section="combat"`
**When** the tool is invoked
**Then** the system returns combat rules from D&D 5e API
**And** includes rules like opportunity attacks and initiative

#### Scenario: Lookup damage type
**Given** a user queries with `type="damage-type"` and `name="radiant"`
**When** the tool is invoked
**Then** the system returns radiant damage type information
**And** includes description and examples

#### Scenario: Invalid rule type
**Given** a user queries with `type="invalid-rule-type"`
**When** the tool is invoked
**Then** the system returns a validation error
**And** lists valid type options

---

### Requirement: Error Handling
The system SHALL handle errors gracefully across all tools.

**Error Types:**
- API failures (network errors, timeouts, 5xx responses)
- Invalid parameters (wrong types, out of range values)
- Empty results (valid query but no matches)
- Invalid API responses (malformed JSON, unexpected schema)

**Error Handling Behavior:**
- Return user-friendly error messages (not stack traces)
- Log detailed errors for debugging
- Use cached responses when available (if API fails)
- Respect error cache TTL (default 5 minutes) to avoid hammering failed endpoints

#### Scenario: API network failure
**Given** the Open5e API is unreachable
**When** any tool is invoked
**Then** the system returns a user-friendly error message
**And** logs the detailed error for debugging
**And** does not expose stack traces to the user

#### Scenario: Invalid parameter type
**Given** a user provides `level="invalid"` to lookup_spell
**When** the tool is invoked
**Then** FastMCP's parameter validation catches the error
**And** returns a clear validation error message

#### Scenario: Empty results
**Given** a user queries for a creature that doesn't exist
**When** lookup_creature is invoked
**Then** the system returns an empty list
**And** does not treat this as an error condition

---

### Requirement: Response Formatting
The system SHALL format all tool responses as structured data suitable for AI consumption.

**Formatting Requirements:**
- Return JSON-serializable data structures
- Include source attribution (document name, API source)
- Use consistent field names across similar data types
- Format text descriptions as plain text or markdown where appropriate
- Include relevant metadata (timestamp, cache status)

#### Scenario: Structured spell response
**Given** a successful spell lookup
**When** results are returned
**Then** the response includes all specified spell fields
**And** the data is JSON-serializable
**And** includes source attribution

#### Scenario: Source attribution
**Given** any successful lookup
**When** results are returned
**Then** each result includes source document information
**And** identifies which API provided the data

---

### Requirement: Performance and Caching
The system SHALL leverage the existing cache layer for all API requests.

**Caching Behavior:**
- All API requests automatically use the cache layer
- Cache TTL: 7 days for successful responses
- Error cache TTL: 5 minutes for failed requests
- Cache key based on endpoint URL and query parameters
- No manual cache management required in tool code

#### Scenario: Cache hit
**Given** a spell lookup for "Fireball" was recently performed
**When** the same lookup is requested again within 7 days
**Then** the system returns cached results
**And** does not make a new API request

#### Scenario: Cache miss
**Given** a spell lookup for "Shield" has never been performed
**When** the lookup is requested
**Then** the system queries the Open5e v2 API
**And** caches the response for 7 days

---

### Requirement: Tool Registration
The system SHALL register all tools with the FastMCP server for MCP protocol exposure.

**Registration Requirements:**
- Tools decorated with `@mcp.tool()` decorator
- Parameter types defined for automatic validation
- Tool descriptions provided for AI assistant discovery
- Tools available immediately after server startup

#### Scenario: Tools visible in MCP protocol
**Given** the LoreKeeper server is started
**When** an MCP client connects
**Then** all 5 tools are visible in the protocol schema
**And** parameter definitions are included

#### Scenario: Tool invocation via MCP
**Given** an MCP client is connected
**When** the client invokes lookup_spell
**Then** the tool executes and returns results via MCP protocol
**And** the response conforms to MCP response format

---
