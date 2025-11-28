# Simplify Document Filtering Parameter Implementation Plan

**Goal:** Replace inconsistent `document` and `document_keys` parameters with a unified `documents` parameter across all MCP tools

**Architecture:** Rename-and-remove refactor across 6 tool files. Each tool's function signature changes from `document_keys: list[str] | None` (and optionally `document: str | None`) to `documents: list[str] | None`. Internal logic remains identical—just parameter names change. Tests updated to use new parameter name.

**Tech Stack:** Python 3.11+, pytest with asyncio_mode=auto, MCP FastMCP decorator pattern

---

## Task 1: Update lookup_spell Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/spell_lookup.py:64-227`
- Test: `tests/test_tools/test_spell_lookup.py`

**Step 1: Update test to use `documents` parameter**

```python
# In tests/test_tools/test_spell_lookup.py, find test_lookup_spell_with_document_keys
# Change the function name and parameter usage

@pytest.mark.asyncio
async def test_lookup_spell_with_documents(repository_context):
    """Test lookup_spell with documents filter."""
    # ... existing mock setup ...

    results = await lookup_spell(name="fireball", documents=["srd-5e"])

    # ... existing assertions ...
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_lookup_spell_with_documents -v`
Expected: FAIL with "unexpected keyword argument 'documents'"

**Step 3: Update lookup_spell function signature**

```python
# In src/lorekeeper_mcp/tools/spell_lookup.py, update the function signature
# Remove lines 75-76 (document and document_keys), add documents parameter

async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    level_min: int | None = None,
    level_max: int | None = None,
    school: str | None = None,
    class_key: str | None = None,
    concentration: bool | None = None,
    ritual: bool | None = None,
    casting_time: str | None = None,
    damage_type: str | None = None,
    documents: list[str] | None = None,  # Replaces document and document_keys
    limit: int = 20,
) -> list[dict[str, Any]]:
```

**Step 4: Update docstring examples and Args section**

```python
# Update docstring examples (around line 118-119)
# Change:
#     srd_only = await lookup_spell(document_keys=["srd-5e"])
#     srd_and_tasha = await lookup_spell(document_keys=["srd-5e", "tce"])
# To:
        Filtering by document:
            srd_only = await lookup_spell(documents=["srd-5e"])
            srd_and_tasha = await lookup_spell(documents=["srd-5e", "tce"])

# Update Args section (remove document and document_keys entries, add documents)
        documents: Filter to specific source documents. Provide a list of
            document names/identifiers from list_documents() tool. Examples:
            ["srd-5e"] for SRD only, ["srd-5e", "tce"] for SRD and Tasha's.
            Use list_documents() to see available documents.
```

**Step 5: Update internal parameter handling**

```python
# Replace lines 220-227 with:
    # Document filtering
    if documents is not None:
        params["document"] = documents  # Repository expects "document"
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py::test_lookup_spell_with_documents -v`
Expected: PASS

**Step 7: Run all spell_lookup tests to ensure no regressions**

Run: `uv run pytest tests/test_tools/test_spell_lookup.py -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/spell_lookup.py tests/test_tools/test_spell_lookup.py
git commit -m "refactor(tools): replace document_keys with documents in lookup_spell"
```

---

## Task 2: Update lookup_creature Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/creature_lookup.py:62-200`
- Test: `tests/test_tools/test_creature_lookup.py`

**Step 1: Update test to use `documents` parameter**

```python
# In tests/test_tools/test_creature_lookup.py, find test_lookup_creature_with_document_keys
# Rename to test_lookup_creature_with_documents and update parameter

@pytest.mark.asyncio
async def test_lookup_creature_with_documents(repository_context):
    """Test lookup_creature with documents filter."""
    # ... existing mock setup ...

    results = await lookup_creature(name="fireball", documents=["srd-5e"])

    # ... existing assertions ...
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_creature_lookup.py::test_lookup_creature_with_documents -v`
Expected: FAIL with "unexpected keyword argument 'documents'"

**Step 3: Update lookup_creature function signature**

```python
# In src/lorekeeper_mcp/tools/creature_lookup.py, update function signature
# Remove lines 73-74 (document and document_keys), add documents

async def lookup_creature(
    name: str | None = None,
    cr: float | None = None,
    cr_min: float | None = None,
    cr_max: float | None = None,
    type: str | None = None,  # noqa: A002
    size: str | None = None,
    armor_class_min: int | None = None,
    hit_points_min: int | None = None,
    documents: list[str] | None = None,  # Replaces document and document_keys
    limit: int = 20,
) -> list[dict[str, Any]]:
```

**Step 4: Update docstring examples and Args section**

```python
# Update docstring examples (around lines 109-114)
# Change document_keys to documents in all examples:
            srd_only = await lookup_creature(documents=["srd-5e"])
            srd_and_tasha = await lookup_creature(
                documents=["srd-5e", "tce"]
            )
            filtered_creatures = await lookup_creature(
                documents=["phb", "dmg"], cr_min=5
            )

# Update Args section (remove document and document_keys, add documents)
          documents: Filter to specific source documents. Provide a list of
              document names/identifiers from list_documents() tool. Examples:
              ["srd-5e"] for SRD only, ["srd-5e", "tce"] for SRD and Tasha's.
```

**Step 5: Update internal parameter handling**

```python
# Replace lines 195-200 with:
    # Document filtering
    if documents is not None:
        params["document"] = documents  # Repository expects "document"
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_creature_lookup.py::test_lookup_creature_with_documents -v`
Expected: PASS

**Step 7: Run all creature_lookup tests**

Run: `uv run pytest tests/test_tools/test_creature_lookup.py -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/creature_lookup.py tests/test_tools/test_creature_lookup.py
git commit -m "refactor(tools): replace document_keys with documents in lookup_creature"
```

---

## Task 3: Update lookup_equipment Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/equipment_lookup.py:57-282`
- Test: `tests/test_tools/test_equipment_lookup.py`

**Step 1: Update test to use `documents` parameter**

```python
# In tests/test_tools/test_equipment_lookup.py, find test_lookup_equipment_with_document_keys
# Rename and update parameter

@pytest.mark.asyncio
async def test_lookup_equipment_with_documents() -> None:
    """Test lookup_equipment with documents filter."""
    # ... existing mock setup ...

    results = await lookup_equipment(type="weapon", name="longsword", documents=["srd-5e"])

    # ... existing assertions ...
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_equipment_lookup.py::test_lookup_equipment_with_documents -v`
Expected: FAIL with "unexpected keyword argument 'documents'"

**Step 3: Update lookup_equipment function signature**

```python
# In src/lorekeeper_mcp/tools/equipment_lookup.py, update function signature
# Remove lines 68-69 (document and document_keys), add documents

async def lookup_equipment(
    type: EquipmentType = "all",  # noqa: A002
    name: str | None = None,
    rarity: str | None = None,
    damage_dice: str | None = None,
    is_simple: bool | None = None,
    requires_attunement: str | None = None,
    cost_min: int | float | None = None,
    cost_max: int | float | None = None,
    weight_max: float | None = None,
    is_finesse: bool | None = None,
    is_light: bool | None = None,
    is_magic: bool | None = None,
    documents: list[str] | None = None,  # Replaces document and document_keys
    limit: int = 20,
) -> list[dict[str, Any]]:
```

**Step 4: Update docstring Args section**

```python
# Remove document and document_keys entries, add:
         documents: Filter to specific source documents. Provide a list of
             document names/identifiers from list_documents() tool. Examples:
             ["srd-5e"] for SRD only, ["srd-5e", "tce"] for SRD and Tasha's.
```

**Step 5: Update internal parameter handling (3 places)**

```python
# For weapons (around lines 225-230), replace with:
        # Document filtering
        if documents is not None:
            weapon_filters["document"] = documents

# For armor (around lines 249-254), replace with:
        # Document filtering
        if documents is not None:
            armor_filters["document"] = documents

# For magic items (around lines 277-282), replace with:
        # Document filtering
        if documents is not None:
            magic_item_filters["document"] = documents
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_equipment_lookup.py::test_lookup_equipment_with_documents -v`
Expected: PASS

**Step 7: Run all equipment_lookup tests**

Run: `uv run pytest tests/test_tools/test_equipment_lookup.py -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/equipment_lookup.py tests/test_tools/test_equipment_lookup.py
git commit -m "refactor(tools): replace document_keys with documents in lookup_equipment"
```

---

## Task 4: Update lookup_character_option Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/character_option_lookup.py:64-172`
- Test: `tests/test_tools/test_character_option_lookup.py`

**Step 1: Update test to use `documents` parameter**

```python
# In tests/test_tools/test_character_option_lookup.py, find test_lookup_character_option_with_document_keys
# Rename and update parameter

@pytest.mark.asyncio
async def test_lookup_character_option_with_documents(
    repository_context,
) -> None:
    """Test lookup_character_option with documents filter."""

    result = await lookup_character_option(type="class", documents=["srd-5e"])

    # ... existing assertions ...
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_character_option_lookup.py::test_lookup_character_option_with_documents -v`
Expected: FAIL with "unexpected keyword argument 'documents'"

**Step 3: Update lookup_character_option function signature**

```python
# In src/lorekeeper_mcp/tools/character_option_lookup.py, update function signature
# Replace line 67 (document_keys) with documents

async def lookup_character_option(
    type: OptionType,  # noqa: A002
    name: str | None = None,
    documents: list[str] | None = None,  # Replaces document_keys
    limit: int = 20,
) -> list[dict[str, Any]]:
```

**Step 4: Update docstring Args section**

```python
# Replace document_keys entry (around line 109) with:
        documents: Filter to specific source documents. Provide a list of
            document names/identifiers from list_documents() tool. Examples:
            ["srd-5e"] for SRD only, ["srd-5e", "tce"] for SRD and Tasha's.
```

**Step 5: Update internal parameter handling**

```python
# Replace lines 170-172 with:
    # Document filtering
    if documents is not None:
        params["document"] = documents  # Repository expects "document"
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_character_option_lookup.py::test_lookup_character_option_with_documents -v`
Expected: PASS

**Step 7: Run all character_option_lookup tests**

Run: `uv run pytest tests/test_tools/test_character_option_lookup.py -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/character_option_lookup.py tests/test_tools/test_character_option_lookup.py
git commit -m "refactor(tools): replace document_keys with documents in lookup_character_option"
```

---

## Task 5: Update lookup_rule Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/rule_lookup.py:69-208`
- Test: `tests/test_tools/test_rule_lookup.py`

**Step 1: Update test to use `documents` parameter**

```python
# In tests/test_tools/test_rule_lookup.py, find test_lookup_rule_with_document_keys
# Rename and update parameter

@pytest.mark.asyncio
async def test_lookup_rule_with_documents(repository_context) -> None:
    """Test lookup_rule with documents filter."""
    # ... existing mock setup ...

    result = await lookup_rule(rule_type="rule", name="Combat", documents=["srd-5e"])

    # ... existing assertions ...
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools/test_rule_lookup.py::test_lookup_rule_with_documents -v`
Expected: FAIL with "unexpected keyword argument 'documents'"

**Step 3: Update lookup_rule function signature**

```python
# In src/lorekeeper_mcp/tools/rule_lookup.py, update function signature
# Replace line 72 (document_keys) with documents

async def lookup_rule(
    rule_type: RuleType,
    name: str | None = None,
    section: str | None = None,
    documents: list[str] | None = None,  # Replaces document_keys
    limit: int = 20,
) -> list[dict[str, Any]]:
```

**Step 4: Update docstring examples and Args section**

```python
# Update examples (around lines 91-92)
        - lookup_rule(rule_type="rule", documents=["srd-5e"]) - Find rules from SRD only
        - lookup_rule(rule_type="condition", name="grappled", documents=["srd-5e", "tce"]) - Filter conditions by documents

# Update Args section (around line 119)
        documents: Filter to specific source documents. Provide a list of
            document names/identifiers from list_documents() tool. Examples:
            ["srd-5e"] for SRD only, ["srd-5e", "tce"] for SRD and Tasha's.
```

**Step 5: Update internal parameter handling**

```python
# Replace lines 206-208 with:
    # Document filtering
    if documents is not None:
        params["document"] = documents  # Repository expects "document"
```

**Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_tools/test_rule_lookup.py::test_lookup_rule_with_documents -v`
Expected: PASS

**Step 7: Run all rule_lookup tests**

Run: `uv run pytest tests/test_tools/test_rule_lookup.py -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/rule_lookup.py tests/test_tools/test_rule_lookup.py
git commit -m "refactor(tools): replace document_keys with documents in lookup_rule"
```

---

## Task 6: Update search_dnd_content Tool

**Files:**
- Modify: `src/lorekeeper_mcp/tools/search_dnd_content.py:39-137`
- Test: `tests/test_tools/test_search_dnd_content.py`

**Step 1: Update tests to use `documents` parameter**

```python
# In tests/test_tools/test_search_dnd_content.py, update 3 tests:

# 1. test_search_dnd_content_with_document_keys -> test_search_dnd_content_with_documents
@pytest.mark.asyncio
async def test_search_dnd_content_with_documents(mock_client_factory):
    """Test search_dnd_content with documents post-filtering."""
    # ... existing setup ...
    result = await search_dnd_content(query="fire", documents=["srd-5e"], limit=10)
    # ... existing assertions ...

# 2. test_search_dnd_content_empty_document_keys -> test_search_dnd_content_empty_documents
@pytest.mark.asyncio
async def test_search_dnd_content_empty_documents(mock_client_factory):
    """Test search_dnd_content short-circuits on empty documents list."""
    result = await search_dnd_content(query="fire", documents=[], limit=10)
    # ... existing assertions ...

# 3. test_search_dnd_content_document_keys_with_content_types -> test_search_dnd_content_documents_with_content_types
@pytest.mark.asyncio
async def test_search_dnd_content_documents_with_content_types(mock_client_factory):
    """Test documents post-filtering with content_types specified."""
    # ... existing setup ...
    result = await search_dnd_content(
        query="fire", content_types=["Spell", "Creature"], documents=["srd-5e"], limit=10
    )
    # ... existing assertions ...
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_tools/test_search_dnd_content.py::test_search_dnd_content_with_documents -v`
Expected: FAIL with "unexpected keyword argument 'documents'"

**Step 3: Update search_dnd_content function signature**

```python
# In src/lorekeeper_mcp/tools/search_dnd_content.py, update function signature
# Replace line 42 (document_keys) with documents

async def search_dnd_content(
    query: str,
    content_types: list[str] | None = None,
    documents: list[str] | None = None,  # Replaces document_keys
    enable_fuzzy: bool = True,
    enable_semantic: bool = True,
    limit: int = 20,
) -> list[dict[str, Any]]:
```

**Step 4: Update docstring examples and Args section**

```python
# Update examples (around lines 69-70)
        search_dnd_content(query="fireball", documents=["srd-5e"])
        search_dnd_content(query="spell", documents=["srd-5e", "tce"])

# Update Args section (around line 76)
        documents: Filter results to specific documents. Provide list of
            document names from list_documents() tool. Post-filters search
            results by document field. Examples: ["srd-5e"], ["srd-5e", "tce"].
```

**Step 5: Update internal parameter handling (4 places)**

```python
# Replace all occurrences of document_keys with documents:

# Line 94: Short-circuit check
    if documents is not None and len(documents) == 0:
        return []

# Line 115: Post-filter in content_types branch
        if documents:
            all_results = [
                r for r in all_results
                if r.get("document") in documents or r.get("document__slug") in documents
            ]

# Line 133: Post-filter in main branch
    if documents:
        results = [
            r for r in results
            if r.get("document") in documents or r.get("document__slug") in documents
        ]
```

**Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_tools/test_search_dnd_content.py::test_search_dnd_content_with_documents tests/test_tools/test_search_dnd_content.py::test_search_dnd_content_empty_documents tests/test_tools/test_search_dnd_content.py::test_search_dnd_content_documents_with_content_types -v`
Expected: All 3 tests PASS

**Step 7: Run all search_dnd_content tests**

Run: `uv run pytest tests/test_tools/test_search_dnd_content.py -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add src/lorekeeper_mcp/tools/search_dnd_content.py tests/test_tools/test_search_dnd_content.py
git commit -m "refactor(tools): replace document_keys with documents in search_dnd_content"
```

---

## Task 7: Update Integration Tests

**Files:**
- Modify: `tests/test_tools/test_document_filtering.py`
- Modify: `tests/test_tools/test_live_mcp.py`

**Step 1: Update test_document_filtering.py**

```python
# Update all occurrences of document_keys to documents:

# Around line 155:
        filtered_spells = await lookup_spell(documents=[doc_to_filter], limit=50)

# Around lines 192-193:
                spells = await lookup_spell(documents=[doc_key], limit=5)
                creatures = await lookup_creature(documents=[doc_key], limit=5)
```

**Step 2: Update test_live_mcp.py**

```python
# Around line 624:
            {"documents": [doc_key], "limit": 5},
```

**Step 3: Run integration tests**

Run: `uv run pytest tests/test_tools/test_document_filtering.py -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_tools/test_document_filtering.py tests/test_tools/test_live_mcp.py
git commit -m "test: update integration tests to use documents parameter"
```

---

## Task 8: Update list_documents Docstring

**Files:**
- Modify: `src/lorekeeper_mcp/tools/list_documents.py`

**Step 1: Update docstring references to document_keys**

```python
# In src/lorekeeper_mcp/tools/list_documents.py, update:

# Line 21: Change "document_keys parameter" to "documents parameter"
    then use the documents parameter in other tools to filter content.

# Line 45: Change "use this in document_keys" to "use this in documents"
            - document: Document name/identifier (use this in documents)
```

**Step 2: Run list_documents tests**

Run: `uv run pytest tests/test_tools/test_list_documents.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add src/lorekeeper_mcp/tools/list_documents.py
git commit -m "docs(tools): update list_documents references to documents parameter"
```

---

## Task 9: Update Documentation

**Files:**
- Modify: `docs/document-filtering.md`
- Modify: `docs/tools.md`
- Modify: `README.md`

**Step 1: Update docs/document-filtering.md**

Replace all occurrences of `document_keys` with `documents` throughout the file. Key sections to update:
- Parameter descriptions
- Code examples
- Usage patterns

**Step 2: Update docs/tools.md**

Replace all occurrences of `document_keys` with `documents` in tool parameter documentation.

**Step 3: Update README.md**

Replace any occurrences of `document_keys` with `documents` in usage examples.

**Step 4: Commit**

```bash
git add docs/document-filtering.md docs/tools.md README.md
git commit -m "docs: update all documentation to use documents parameter"
```

---

## Task 10: Run Full Test Suite and Quality Checks

**Step 1: Run all unit tests**

Run: `uv run pytest tests/ -v -m "not live"`
Expected: All tests PASS

**Step 2: Run type checking**

Run: `just type-check`
Expected: No mypy errors

**Step 3: Run linting**

Run: `just lint`
Expected: No ruff errors

**Step 4: Run formatting**

Run: `just format`
Expected: Files formatted (or no changes needed)

**Step 5: Run all quality checks**

Run: `just check`
Expected: All checks PASS

**Step 6: Commit if any formatting was applied**

```bash
git add -u
git commit -m "style: apply formatting fixes"
```

---

## Validation Checklist

Before marking complete, verify:

- [ ] All 6 tools use `documents: list[str] | None = None` parameter
- [ ] No tools have `document` or `document_keys` parameters
- [ ] All tool docstrings updated with new parameter name and examples
- [ ] All tests renamed and updated to use `documents`
- [ ] Integration tests updated
- [ ] list_documents docstring references updated
- [ ] Documentation files updated
- [ ] All unit tests pass
- [ ] Type checking passes
- [ ] Linting passes
- [ ] No regressions in existing functionality

## Estimated Effort

- **Tool updates**: 3-4 hours (Tasks 1-6, ~30-40 min each)
- **Test updates**: 30 minutes (Task 7)
- **Documentation**: 30 minutes (Tasks 8-9)
- **Quality checks**: 15 minutes (Task 10)

**Total**: ~5 hours
