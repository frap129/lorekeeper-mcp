# LoreKeeper CLI Usage

The LoreKeeper CLI provides commands for importing and managing D&D 5e content.

## Installation

The `lorekeeper` command is available after installing the package:

```bash
uv sync
```

## Commands

### import

Import D&D content from an OrcBrew (.orcbrew) file into the local cache.

**Usage:**
```bash
lorekeeper import <file>
```

**Options:**
- `--dry-run` - Parse file but don't import to database
- `--force` - Overwrite existing entities (default behavior)

**Global Options:**
- `--db-path PATH` - Custom database location (default: data/lorekeeper.db)
- `-v, --verbose` - Enable verbose logging

**Examples:**

Import a content pack:
```bash
lorekeeper import MegaPak_-_WotC_Books.orcbrew
```

Test parsing without importing:
```bash
lorekeeper import --dry-run homebrew.orcbrew
```

Import with verbose output:
```bash
lorekeeper -v import custom-content.orcbrew
```

Use custom database path:
```bash
lorekeeper --db-path ./my-cache.db import data.orcbrew
```

## Supported Entity Types

The import command supports these OrcBrew entity types:

| OrcBrew Type | LoreKeeper Type | Description |
|--------------|-----------------|-------------|
| orcpub.dnd.e5/spells | spells | Spells with level, school |
| orcpub.dnd.e5/monsters | creatures | Creatures/monsters with CR, type, size |
| orcpub.dnd.e5/classes | classes | Character classes |
| orcpub.dnd.e5/subclasses | subclasses | Class archetypes |
| orcpub.dnd.e5/races | species | Player species/races |
| orcpub.dnd.e5/subraces | subraces | Species variants |
| orcpub.dnd.e5/backgrounds | backgrounds | Character backgrounds |
| orcpub.dnd.e5/feats | feats | Character feats |
| orcpub.dnd.e5/weapons | weapons | Weapons with damage type |
| orcpub.dnd.e5/armor | armor | Armor with AC |
| orcpub.dnd.e5/magic-items | magicitems | Magic items |
| orcpub.dnd.e5/languages | languages | Languages |

Unsupported types are skipped with a warning.

## Troubleshooting

**Import fails with "Failed to parse EDN":**
- Ensure the file is valid EDN/Clojure format
- Check for Unicode encoding issues
- Try opening the file in a text editor to verify it's readable

**Entities are skipped:**
- Entities without a `key` or `name` field are skipped
- Check verbose output with `-v` flag to see specific warnings
- Ensure entity data matches expected structure

**Database errors:**
- Ensure the database directory exists and is writable
- Try specifying a different path with `--db-path`
- Check disk space

## Performance

Typical import times:
- Small files (< 100 entities): < 1 second
- Medium files (100-1000 entities): 1-5 seconds
- Large files (1000+ entities): 5-30 seconds

The MegaPak file (43,000+ lines) imports in approximately 10-20 seconds.
