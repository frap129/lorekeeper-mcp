# LoreKeeper MCP Tools Specification

This document defines the MCP tools for LoreKeeper, organized by domain.

## API Assignment Strategy

- **Use Open5e API** for all content lookups
- **Prefer Open5e v2** over v1 when available
- **Unified source**: Single API ensures consistent behavior and simplified maintenance

---

## Semantic Search

LoreKeeper supports **semantic search** for finding content by meaning rather than exact text matches. This is powered by the Milvus Lite cache backend with sentence-transformers embeddings.

### Overview

All search tools accept an optional `search` parameter:

```python
# Find spells conceptually related to "fire damage"
spells = await search_spell(search="explosive fire damage")

# Combine semantic search with filters
fire_spells = await search_spell(
    search="area of effect fire damage",
    level=3,
    school="evocation"
)
```

### How It Works

1. Your natural language query is converted to a 384-dimensional embedding vector
2. The vector is compared against all cached entity embeddings using cosine similarity
3. Results are ranked by semantic similarity (highest first)
4. Optional filters (level, type, etc.) are applied as constraints

### Semantic Search Examples

#### Spells by Concept

```python
# Find healing spells without knowing exact names
healing = await search_spell(search="restore health and cure wounds")
# Returns: Cure Wounds, Healing Word, Mass Cure Wounds, etc.

# Find crowd control spells
control = await search_spell(search="stop enemies from moving or acting")
# Returns: Hold Person, Web, Entangle, etc.

# Find protective magic
protection = await search_spell(search="shield and protect allies from harm")
# Returns: Shield, Shield of Faith, Protection from Evil and Good, etc.

# Find spells by damage type (without using damage_type filter)
lightning = await search_spell(search="electricity and lightning damage")
# Returns: Lightning Bolt, Call Lightning, Witch Bolt, etc.
```

#### Creatures by Behavior

```python
# Find flying enemies
flyers = await search_creature(search="creatures that fly and attack from above")
# Returns: Dragon, Wyvern, Harpy, etc.

# Find undead by theme
undead = await search_creature(search="risen dead that drain life force")
# Returns: Wraith, Specter, Vampire, etc.

# Find ambush predators
ambushers = await search_creature(search="stealthy hunters that attack by surprise")
# Returns: Assassin, Displacer Beast, Invisible Stalker, etc.
```

#### Equipment by Use Case

```python
# Find ranged weapons
ranged = await search_equipment(
    search="weapons for attacking from a distance",
    type="weapon"
)
# Returns: Longbow, Crossbow, Javelin, etc.

# Find defensive gear
defensive = await search_equipment(
    search="armor and shields for protection"
)
# Returns: Plate Armor, Shield, Chain Mail, etc.

# Find magical utility items
utility = await search_equipment(
    search="magic items for utility and exploration",
    type="magic-item"
)
# Returns: Bag of Holding, Rope of Climbing, Decanter of Endless Water, etc.
```

#### Hybrid Search (Semantic + Filters)

Combine semantic queries with structured filters for precise results:

```python
# Low-level fire spells
low_fire = await search_spell(
    search="fire and burning damage",
    level=1,
    limit=5
)

# Undead under CR 5
weak_undead = await search_creature(
    search="undead creatures",
    cr_max=5,
    type="undead"
)

# Rare magic weapons
rare_weapons = await search_equipment(
    search="magical swords and blades",
    type="magic-item",
    rarity="rare"
)

# SRD-only results
srd_healing = await search_spell(
    search="healing magic",
    documents=["srd-5e"]
)
```

### Similarity Scores

Semantic search results include a `_score` field (0.0 to 1.0):

```python
results = await search_spell(search="fire explosion")
for spell in results[:3]:
    print(f"{spell['name']}: {spell.get('_score', 0):.3f}")
# Output:
# Fireball: 0.892
# Fire Storm: 0.834
# Flame Strike: 0.789
```

### When to Use Semantic Search

**Use semantic search when:**
- You don't know exact names or terminology
- You want conceptually related results
- Natural language queries feel more intuitive
- You're exploring content by theme or use case

**Use structured filters when:**
- You know the exact spell level, CR, or type
- You need precise filtering (e.g., all level 3 evocation spells)
- Performance is critical (filters are faster than semantic search)

### Backend Requirements

Semantic search requires the **Milvus Lite** cache backend (the only supported backend).

---

## Document Filtering

### Overview

All LoreKeeper search tools support filtering content by source document. This enables precise control over which sources you query, allowing you to:

- **Limit searches to SRD (free) content only** - Use only freely available System Reference Document content
- **Filter by specific published books** - Query only content from "Tasha's Cauldron of Everything", "Xanathar's Guide", etc.
- **Separate homebrew from official content** - Filter imported OrcBrew content separately from published books
- **Control licensing** - Respect licensing requirements by limiting queries to appropriate sources

### Available Documents

Use `list_documents()` to discover what's available in your cache:

```python
# List all available documents
documents = await list_documents()
# Returns list with document names, sources, entity counts, etc.

# List only Open5e documents
open5e_docs = await list_documents(source="open5e_v2")

# List only OrcBrew homebrew imports
homebrew_docs = await list_documents(source="orcbrew")
```

Each document in the results contains:
- `document`: The document name/identifier (use this in `documents`)
- `source_api`: Which source provided this (open5e_v2, orcbrew)
- `entity_count`: Total number of entities from this document
- `entity_types`: Breakdown by type (spells, creatures, equipment, etc.)
- `publisher`: Publisher name (Open5e documents)
- `license`: License type (Open5e documents)

### Using Document Filters

#### In Lookup Tools

All search tools (`search_spell`, `search_creature`, `search_character_option`, `search_equipment`, `search_rule`) accept a `documents` parameter:

```python
# Filter to SRD only
srd_spells = await search_spell(level=3, documents=["srd-5e"])

# Filter to multiple documents
multi_source = await search_creature(
    type="dragon",
    documents=["srd-5e", "tce", "phb"]
)

# Complex filtering with multiple parameters
wizard_evocations = await search_spell(
    class_key="wizard",
    school="evocation",
    level_min=1,
    level_max=5,
    documents=["srd-5e", "xgte"]
)

# Equipment filtering by source
plate_armor = await search_equipment(
    type="armor",
    search="plate",
    documents=["srd-5e"]
)

# Character options from specific books
tasha_feats = await search_character_option(
    type="feat",
    documents=["tce"]  # Tasha's Cauldron of Everything
)
```

#### In Search Tool

The `search_all()` tool also supports document filtering:

```python
# Search spells in SRD only
srd_results = await search_all(
    query="fireball",
    documents=["srd-5e"]
)

# Search across multiple books
published_results = await search_all(
    query="dragon",
    documents=["srd-5e", "tce", "xgte"]
)

# General search with no filter (all documents)
all_results = await search_all(query="magic item")
```

### Common Document Keys

Here are frequently-used document identifiers (use output from `list_documents()` for exact names):

**Official D&D 5e SRD**:
- `"srd-5e"` or `"System Reference Document 5.1"` - Core rules

**Published Supplements** (examples - use `list_documents()` for current list):
- `"phb"` - Player's Handbook
- `"dmg"` - Dungeon Master's Guide
- `"mm"` - Monster Manual
- `"tce"` - Tasha's Cauldron of Everything
- `"xgte"` - Xanathar's Guide to Everything
- `"vrgr"` - Van Richten's Guide to Ravenloft

**Homebrew**:
- Document names from imported OrcBrew files (e.g., `"Homebrew Grimoire"`)

### Cross-Source Filtering Examples

#### SRD-Only Content

Get only free, System Reference Document content:

```python
# Only SRD spells
srd_spells = await search_spell(documents=["srd-5e"])

# Only SRD creatures up to CR 5
srd_creatures = await search_creature(
    cr_max=5,
    documents=["srd-5e"]
)

# Only SRD equipment
srd_gear = await search_equipment(documents=["srd-5e"])
```

#### Published Books Only

Get only officially published content (excluding homebrew):

```python
published = await search_spell(
    school="evocation",
    documents=[
        "srd-5e", "phb", "tce", "xgte", "vrgr", "dmg", "mm"
    ]
)
```

#### Specific Supplement

Query a specific book without mixing sources:

```python
# Only Tasha's content
tasha_content = await search_character_option(
    type="feat",
    documents=["tce"]
)

# Only Xanathar's Guide
xgte_content = await search_spell(
    school="evocation",
    documents=["xgte"]
)
```

#### Homebrew Only

Isolate homebrew content from official sources:

```python
# First, identify homebrew documents
docs = await list_documents(source="orcbrew")
homebrew_keys = [d["document"] for d in docs]

# Query only homebrew
homebrew_creatures = await search_creature(
    documents=homebrew_keys
)
```

#### Exclude Specific Sources

Query everything except a particular document:

```python
# Note: LoreKeeper doesn't have explicit exclusion, so:
# 1. Get all documents
all_docs = await list_documents()
# 2. Filter out ones you don't want
all_keys = [d["document"] for d in all_docs]
excluded = "homebrew-grimoire"
filtered_keys = [k for k in all_keys if excluded not in k.lower()]
# 3. Query with remaining documents
results = await search_spell(documents=filtered_keys)
```

### Performance Notes

- **Indexed Queries**: The `document` field has a database index, making filtering efficient
- **Combined Filters**: Document filters combine efficiently with other parameters (level, type, etc.)
- **Empty Results**: Filtering may return fewer results if few entities exist in selected documents
- **Backward Compatible**: The `documents` parameter is optional; omitting it queries all documents

### Implementation Details

- **Document Keys**: Use exact names from `list_documents()` output
- **Case Sensitive**: Document names are case-sensitive
- **Multiple Documents**: Pass a list to filter across multiple documents (OR logic)
- **Empty List**: Passing an empty `documents=[]` returns no results (short-circuit)

---

## Tool 1: `search_spell`

**Purpose**: Search and retrieve spell information

**API**: Open5e `/v2/spells/` (primary, comprehensive)

**Parameters**:
- `search` (string, optional): Natural language search query for semantic/vector search
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
- "What does Fireball do?" → `search="fireball"`
- "Show me 3rd level wizard evocation spells" → `level=3, class_key="wizard", school="evocation"`
- "Find all concentration spells" → `concentration=true`

---

## Tool 2: `search_creature`

**Purpose**: Search and retrieve monster/creature stat blocks

**API**: Open5e `/v1/monsters/` (most comprehensive monster database)

**Parameters**:
- `search` (string, optional): Natural language search query for semantic/vector search
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
- "Show me the Ancient Red Dragon" → `search="ancient red dragon"`
- "Medium beasts CR 1 or less" → `cr_max=1, type="beast", size="Medium"`

---

## Tool 3: `search_character_option`

**Purpose**: Get character creation and advancement options

**API Coverage**:
- **Classes**: Open5e `/v1/classes/` (includes subclasses/archetypes)
- **Races**: Open5e `/v1/races/` (includes subraces)
- **Backgrounds**: Open5e `/v2/backgrounds/`
- **Feats**: Open5e `/v2/feats/`

**Parameters**:
- `type` (string, required): One of: `class`, `race`, `background`, `feat`
- `search` (string, optional): Natural language search query for semantic/vector search
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
- "What features does a Paladin get?" → `type="class", search="paladin"`
- "Show me the Eldritch Knight" → `type="class", search="eldritch knight"`
- "What traits do Half-Elves have?" → `type="race", search="half-elf"`
- "Find the Sharpshooter feat" → `type="feat", search="sharpshooter"`

---

## Tool 4: `search_equipment`

**Purpose**: Search for weapons, armor, adventuring gear, and magic items

**API Coverage**:
- **Weapons**: Open5e `/v2/weapons/`
- **Armor**: Open5e `/v2/armor/`
- **Magic Items**: Open5e `/v1/magicitems/`

**Parameters**:
- `type` (string, optional): One of: `weapon`, `armor`, `magic-item`, `all` (default: `all`)
- `search` (string, optional): Natural language search query for semantic/vector search
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
- "What's the damage for a longsword?" → `type="weapon", search="longsword"`
- "Show me rare magic weapons" → `type="magic-item", rarity="rare"`
- "Find light armor" → `type="armor"`
- "What does a Bag of Holding do?" → `type="magic-item", search="bag of holding"`

---

## Tool 5: `search_rule`

**Purpose**: Look up game rules, mechanics, conditions, and reference information

**API Coverage**:
- **Rules & Rule Sections**: Open5e `/v2/rules/`, `/v2/rule-sections/`
- **Conditions**: Open5e `/v2/conditions/`
- **Reference Info**: Open5e (damage-types, weapon-properties, skills, ability-scores, magic-schools, languages, proficiencies, alignments)

**Parameters**:
- `rule_type` (string, required): One of: `rule`, `condition`, `damage-type`, `weapon-property`, `skill`, `ability-score`, `magic-school`, `language`, `proficiency`, `alignment`
- `search` (string, optional): Natural language search query for semantic/vector search
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
- "What does the Grappled condition do?" → `rule_type="condition", search="grappled"`
- "Explain opportunity attacks" → `rule_type="rule", section="combat", search="opportunity attack"`
- "What is radiant damage?" → `rule_type="damage-type", search="radiant"`
- "How does the Stealth skill work?" → `rule_type="skill", search="stealth"`
- "What are weapon properties?" → `rule_type="weapon-property"`

---

## Tool 6: `search_all`

**Purpose**: General-purpose search across all D&D content types with semantic search support

**Parameters**:
- `query` (string, required): Search query (supports natural language with semantic search)
- `content_types` (list[string], optional): Limit search to specific types (spells, creatures, equipment, etc.)
- `documents` (list[string], optional): Filter by source documents
- `limit` (integer, optional, default=20): Maximum results per entity type

**Returns**:
- Results grouped by entity type
- Each result includes entity data and similarity score

**Example Queries**:
```python
# Semantic search across all content
results = await search_all(query="fire damage")

# Search specific entity types
results = await search_all(
    query="healing magic",
    content_types=["Spell", "Item"]
)

# Search within specific documents
results = await search_all(
    query="dragon breath",
    documents=["srd-5e"]
)
```

---

## Implementation Notes

### Caching Strategy

LoreKeeper uses **Milvus Lite** for caching:

- Stores entity data with embedding vectors
- Supports semantic/vector search
- Entity embeddings generated automatically on storage
- TTL: Infinite (entities never expire)

### Semantic Search

When `search` is provided (Milvus backend):
1. Query text is converted to a 384-dimensional embedding vector
2. Vector similarity search finds semantically related content
3. Results are ranked by cosine similarity (0.0 to 1.0)
4. Structured filters are applied as constraints

**Embedding Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- 384 dimensions
- ~80MB model (downloaded on first use)
- <10ms encoding time per query

### Error Handling
- If primary API fails, log error and return user-friendly message
- Log detailed errors for debugging
- Cache errors with short TTL (5 minutes) to avoid hammering failed endpoints
- Semantic search falls back to structured search on error

### Search Behavior
- **Semantic search**: Natural language queries find conceptually related results
- **Exact match**: If `search` parameter exactly matches, return single result
- **Partial match**: If `search` is partial, return up to `limit` results ranked by relevance
- **No search**: If no `search` provided, filter by other parameters and return up to `limit` results

### Response Formatting
- Return structured data suitable for AI consumption
- Include source attribution (document name/title)
- Include similarity score (`_score`) for semantic search results
- Format text descriptions as markdown where appropriate
- Include URLs to original API resources for reference

---

## API Endpoint Summary

### Primary APIs by Tool

| Tool | Category | API Endpoint | Version |
|------|----------|-------------|---------|
| search_spell | Spells | Open5e `/v2/spells/` | v2 ✓ |
| search_creature | Monsters | Open5e `/v1/monsters/` | v1 |
| search_character_option | Classes | Open5e `/v1/classes/` | v1 |
| search_character_option | Races | Open5e `/v1/races/` | v1 |
| search_character_option | Backgrounds | Open5e `/v2/backgrounds/` | v2 ✓ |
| search_character_option | Feats | Open5e `/v2/feats/` | v2 ✓ |
| search_equipment | Weapons | Open5e `/v2/weapons/` | v2 ✓ |
| search_equipment | Armor | Open5e `/v2/armor/` | v2 ✓ |
| search_equipment | Magic Items | Open5e `/v1/magicitems/` | v1 |
| search_rule | Rules | Open5e `/v2/rules/`, `/v2/rule-sections/` | v2 ✓ |
| search_rule | Conditions | Open5e `/v2/conditions/` | v2 ✓ |
| search_rule | Reference | Open5e (various) | v2 ✓ |

### Why Open5e Was Chosen
- **Comprehensive coverage**: Open5e v2 provides comprehensive, well-structured game data
- **Open source**: Open5e data is freely available and community-supported
- **Consistent maintenance**: Single API source ensures consistent updates and behavior
- **Extensive content**: Includes both official SRD content and community-created content
