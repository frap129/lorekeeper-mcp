# Change Proposal: Simplify Document Filtering Parameter

## Why

The current document filtering interface has inconsistencies that make it confusing for users:

1. **Duplicate parameters**: Some tools have both `document: str` and `document_keys: list[str]`, while others only have `document_keys`. This creates ambiguity about which parameter to use.

2. **Deprecated parameter still present**: The `document` parameter is marked as deprecated in docstrings but remains in the function signatures of `lookup_spell`, `lookup_creature`, and `lookup_equipment`.

3. **Awkward naming**: `document_keys` suggests identifiers/slugs, but users pass document names. The name doesn't clearly convey that it's a list of documents to filter by.

4. **Inconsistent across tools**:
   - `lookup_spell`, `lookup_creature`, `lookup_equipment`: Have both `document` and `document_keys`
   - `lookup_character_option`, `lookup_rule`, `search_dnd_content`: Only have `document_keys`

A unified, simpler interface will improve usability and reduce confusion.

## What Changes

- **Remove `document` parameter**: Delete the deprecated `document: str` parameter from all tools
- **Remove `document_keys` parameter**: Delete `document_keys: list[str]` from all tools
- **Add `documents` parameter**: Add `documents: list[str] | None = None` to all lookup and search tools

The new parameter:
- Uses a clearer name (`documents` instead of `document_keys`)
- Accepts a list of document identifiers (from `list_documents()` output)
- Defaults to `None` to search all documents (no breaking change for existing usage)
- Is consistent across all tools

### Example Usage

Before:
```python
# Confusing - which parameter to use?
await lookup_spell(name="fireball", document="srd-5e")  # deprecated
await lookup_spell(name="fireball", document_keys=["srd-5e"])  # new
```

After:
```python
# Clear and consistent
await lookup_spell(name="fireball", documents=["srd-5e"])
await lookup_creature(name="dragon", documents=["srd-5e", "tce"])
await search_dnd_content(query="healing", documents=["srd-5e"])
```

## Impact

### Affected Specs
- `mcp-tools` - Update tool signatures to use `documents` parameter

### Affected Code

**Tools to update:**
- `src/lorekeeper_mcp/tools/spell_lookup.py` - Remove `document`, rename `document_keys` to `documents`
- `src/lorekeeper_mcp/tools/creature_lookup.py` - Remove `document`, rename `document_keys` to `documents`
- `src/lorekeeper_mcp/tools/equipment_lookup.py` - Remove `document`, rename `document_keys` to `documents`
- `src/lorekeeper_mcp/tools/character_option_lookup.py` - Rename `document_keys` to `documents`
- `src/lorekeeper_mcp/tools/rule_lookup.py` - Rename `document_keys` to `documents`
- `src/lorekeeper_mcp/tools/search_dnd_content.py` - Rename `document_keys` to `documents`

**Tests to update:**
- `tests/test_tools/test_spell_lookup.py`
- `tests/test_tools/test_creature_lookup.py`
- `tests/test_tools/test_equipment_lookup.py`
- `tests/test_tools/test_character_option_lookup.py`
- `tests/test_tools/test_rule_lookup.py`
- `tests/test_tools/test_search_dnd_content.py`
- `tests/test_tools/test_document_filtering.py`

**Documentation to update:**
- `docs/document-filtering.md`
- `docs/tools.md`
- `README.md`

### Benefits
- **Clearer interface**: Single, well-named parameter across all tools
- **Reduced confusion**: No deprecated parameters cluttering signatures
- **Better discoverability**: `documents` clearly indicates it's a list of documents
- **Consistency**: Same parameter name and type in all tools

### Risks
- **Minor breaking change**: Users calling `document_keys=` will need to update to `documents=`
- **Mitigation**: This is a new feature with limited adoption; breaking change is acceptable
- **No data changes**: Only function signatures change, no cache or storage impact
