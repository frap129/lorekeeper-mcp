# Code Quality Guide

This guide covers the code quality tools, standards, and practices used in the LoreKeeper MCP project.

## Table of Contents

- [Overview](#overview)
- [Code Quality Tools](#code-quality-tools)
- [Configuration](#configuration)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Code Standards](#code-standards)
- [Linting Rules](#linting-rules)
- [Type Checking](#type-checking)
- [Code Formatting](#code-formatting)
- [Quality Gates](#quality-gates)
- [Best Practices](#best-practices)

## Overview

The LoreKeeper project uses a comprehensive code quality stack to ensure maintainable, reliable, and consistent code. Our approach emphasizes:

- **Automated Enforcement**: Quality checks run automatically on every commit
- **Developer Experience**: Tools are fast and provide helpful feedback
- **Consistency**: All code follows the same standards
- **Type Safety**: Catch errors at development time
- **Documentation**: Self-documenting code with clear intent

## Code Quality Tools

### Primary Tools

| Tool | Purpose | Version | Configuration |
|------|---------|---------|---------------|
| **Black** | Code formatting | 24.10.0+ | `pyproject.toml` |
| **Ruff** | Linting and import sorting | 0.14.3+ | `pyproject.toml` |
| **MyPy** | Static type checking | 1.18.2+ | `pyproject.toml` |
| **Pre-commit** | Git hooks automation | 4.3.0+ | `.pre-commit-config.yaml` |

### Tool Integration

```bash
# Install all quality tools
uv sync --dev

# Run all quality checks
uv run pre-commit run --all-files

# Individual tool execution
uv run black src/ tests/
uv run ruff check src/ tests/ --fix
uv run mypy src/
```

## Configuration

### pyproject.toml Configuration

```toml
[tool.ruff]
line-length = 100
target-version = "py313"
exclude = [
    ".bzr", ".direnv", ".eggs", ".git", ".git-rewrite", ".hg",
    ".mypy_cache", ".nox", ".pants.d", ".pytype", ".ruff_cache",
    ".svn", ".tox", ".venv", "__pypackages__", "_build",
    "buck-out", "build", "dist", "node_modules", "venv",
]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "A",      # flake8-builtins
    "C4",     # flake8-comprehensions
    "PIE",    # flake8-pie
    "RET",    # flake8-return
    "SIM",    # flake8-simplify
    "RUF",    # Ruff-specific rules
    "PTH",    # flake8-use-pathlib
    "PERF",   # flake8-perf
    "PGH",    # pygrep-hooks
    "PL",     # pylint
]
ignore = [
    "E501",   # line too long, handled by black
    "PLR0913", # too many arguments
    "PLR0915", # too many statements
    "PLR0912", # too many branches
    "PLR0911", # too many return statements
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = [
    "S101",   # use of assert
    "PLR2004", # magic value comparison
    "PLR0913", # too many arguments in tests
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[tool.black]
line-length = 100
target-version = ["py313"]
include = '\.pyi?$'
extend-exclude = '''
/(
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
extra_checks = true

[[tool.mypy.overrides]]
module = [
    "fastmcp.*",
    "aiosqlite.*",
]
ignore_missing_imports = true
```

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        language_version: python3.13

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: uv run mypy src/
        language: system
        pass_filenames: false
        always_run: true
```

## Pre-commit Hooks

### Hook Execution Order

1. **Basic Checks** (pre-commit/pre-commit-hooks)
   - Remove trailing whitespace
   - Fix end-of-file issues
   - Validate YAML syntax
   - Check for large files
   - Detect merge conflicts
   - Find debug statements

2. **Code Formatting** (psf/black)
   - Format Python code to Black standards
   - Ensure consistent style

3. **Linting and Import Sorting** (astral-sh/ruff-pre-commit)
   - Run Ruff linter with auto-fix
   - Sort imports according to isort rules
   - Apply Ruff formatting

4. **Type Checking** (local mypy hook)
   - Run MyPy static type analysis
   - Verify type annotations
   - Check for type errors

### Installing Hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Install hooks for all repositories
uv run pre-commit install --all-types

# Run hooks manually on all files
uv run pre-commit run --all-files

# Run hooks on staged files only
uv run pre-commit run
```

### Hook Configuration Details

#### Trailing Whitespace
```yaml
- id: trailing-whitespace
  args: [--markdown-linebreak-ext=md]
```

#### Large File Detection
```yaml
- id: check-added-large-files
  args: ['--maxkb=1000']  # 1MB limit
```

#### MyPy Configuration
```yaml
- id: mypy
  name: mypy
  entry: uv run mypy src/
  language: system
  pass_filenames: false
  always_run: true
  args: [--show-error-codes]
```

## Code Standards

### Formatting Standards

#### Line Length
- **Maximum**: 100 characters
- **Enforced by**: Black and Ruff
- **Rationale**: Readable on modern screens and side-by-side diffing

#### Indentation
- **Style**: 4 spaces (no tabs)
- **Enforced by**: Black
- **Consistency**: All Python files use same indentation

#### Quotes
- **Strings**: Double quotes by default
- **Docstrings**: Triple double quotes
- **Enforced by**: Black and Ruff

```python
# Good
name = "Fireball"
description = """A brilliant streak of flame..."""

# Bad
name = 'Fireball'
description = '''A brilliant streak of flame...'''
```

#### Imports
- **Order**: Standard library, third-party, local imports
- **Style**: Individual imports on separate lines
- **Enforced by**: Ruff (isort)

```python
# Good
import asyncio
import json
from pathlib import Path

import httpx
import pytest
from pydantic import BaseModel

from lorekeeper_mcp.cache import db
from lorekeeper_mcp.config import settings

# Bad
import asyncio, json, pathlib
import httpx, pytest
from lorekeeper_mcp.cache import db, config
```

### Naming Conventions

#### Variables and Functions
```python
# Good
spell_level = 3
def calculate_damage(dice_count: int, dice_sides: int) -> int:
    return dice_count * dice_sides

# Bad
spellLevel = 3
def CalcDamage(d, s):
    return d * s
```

#### Classes
```python
# Good
class SpellLookup:
    pass

class CacheManager:
    pass

# Bad
class spellLookup:
    pass

class cache_manager:
    pass
```

#### Constants
```python
# Good
MAX_SPELL_LEVEL = 9
DEFAULT_CACHE_TTL = 7 * 24 * 3600

# Bad
max_spell_level = 9
defaultCacheTtl = 7 * 24 * 3600
```

#### Private Members
```python
# Good
class CacheManager:
    def __init__(self):
        self._connection = None  # Private instance variable
        self.__init_database()  # Private method

    def __init_database(self):
        pass

# Bad
class CacheManager:
    def __init__(self):
        self.connection = None  # Should be private

    def init_database(self):  # Should be private
        pass
```

## Linting Rules

### Enabled Rule Categories

#### Error Detection (E, W, F)
- **pycodestyle errors (E)**: Style violations
- **pycodestyle warnings (W)**: Style warnings
- **pyflakes (F)**: Error detection and undefined names

#### Import Management (I)
- **isort (I)**: Import sorting and organization

#### Naming Conventions (N)
- **pep8-naming (N)**: Class, function, and variable naming

#### Modern Python (UP)
- **pyupgrade (UP)**: Python 3.13+ syntax and idioms

#### Bug Prevention (B, A, C4, PIE)
- **flake8-bugbear (B)**: Common pitfalls and design issues
- **flake8-builtins (A)**: Shadowing built-in functions
- **flake8-comprehensions (C4)**: List/set/dict comprehension best practices
- **flake8-pie (PIE)**: Miscellaneous issues

#### Code Quality (RET, SIM, RUF, PTH, PERF)
- **flake8-return (RET)**: Return statement issues
- **flake8-simplify (SIM)**: Code simplification opportunities
- **Ruff-specific (RUF)**: Ruff's own rules
- **flake8-use-pathlib (PTH)**: Prefer pathlib over os.path
- **flake8-perf (PERF)**: Performance anti-patterns

#### Security (PGH)
- **pygrep-hooks (PGH)**: Security and best practice checks

#### Code Quality (PL)
- **pylint (PL)**: Additional quality checks

### Common Issues and Fixes

#### Line Too Long (E501)
```python
# Bad - Line too long
result = await fetch_spell_data(name="fireball", level=3, school="evocation", casting_time="1 action")

# Good - Line breaks
result = await fetch_spell_data(
    name="fireball",
    level=3,
    school="evocation",
    casting_time="1 action",
)
```

#### Unused Import (F401)
```python
# Bad - Unused import
import json
import os  # Unused

def load_data():
    return {"test": "data"}

# Good - Only import what's used
import json

def load_data():
    return {"test": "data"}
```

#### Undefined Name (F821)
```python
# Bad - Undefined variable
def calculate_damage():
    return base_damage * multiplier  # base_damage not defined

# Good - Define variables before use
def calculate_damage(base_damage: int, multiplier: int) -> int:
    return base_damage * multiplier
```

#### Import Sorting (I001)
```python
# Bad - Wrong order
from lorekeeper_mcp.cache import db
import asyncio
import httpx

# Good - Correct order
import asyncio

import httpx

from lorekeeper_mcp.cache import db
```

## Type Checking

### MyPy Configuration

#### Strict Type Checking
```python
# Good - Full type annotations
async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    school: str | None = None,
) -> dict[str, Any]:
    """Look up spell information."""
    # Implementation

# Bad - Missing type annotations
async def lookup_spell(name=None, level=None, school=None):
    """Look up spell information."""
    # Implementation
```

#### Type Hints Best Practices

```python
from typing import Any, Dict, List, Optional, Union

# Use modern syntax (Python 3.9+)
def process_spells(spells: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process a list of spells."""
    return {"count": len(spells)}

# Use Optional for nullable types
def find_spell(name: str) -> Optional[Dict[str, Any]]:
    """Find a spell by name."""
    # Returns None if not found

# Use Union for multiple types
def process_id(id_value: Union[int, str]) -> str:
    """Process ID value."""
    return str(id_value)

# Use | syntax for unions (Python 3.10+)
def process_id_modern(id_value: int | str) -> str:
    """Process ID value."""
    return str(id_value)
```

#### Type Definitions

```python
from typing import TypedDict, NotRequired

class Spell(TypedDict):
    """Type definition for spell data."""
    name: str
    level: int
    school: str
    casting_time: str
    components: List[str]
    duration: str
    description: str
    higher_levels: NotRequired[str]

def process_spell(spell: Spell) -> str:
    """Process spell data."""
    return f"{spell['name']} (Level {spell['level']} {spell['school']})"
```

#### Generic Types

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Cache(Generic[T]):
    """Generic cache implementation."""

    def __init__(self) -> None:
        self._data: Dict[str, T] = {}

    def get(self, key: str) -> T | None:
        return self._data.get(key)

    def set(self, key: str, value: T) -> None:
        self._data[key] = value

# Usage
spell_cache = Cache[Dict[str, Any]]()
monster_cache = Cache[Dict[str, Any]]()
```

## Code Formatting

### Black Configuration

#### Formatting Rules
- **Line Length**: 100 characters
- **String Normalization**: Double quotes
- **Indentation**: 4 spaces
- **Trailing Commas**: Preserved in multi-line structures

#### Before and After Examples

```python
# Before Black
def calculate_spell_dc(spell_level:int,casting_ability:int):
    base_dc=8+spell_level+casting_ability
    if spell_level==0:
        base_dc=casting_ability
    return base_dc

spell_data={'name':'Fireball','level':3,'school':'evocation','damage':'8d6'}

# After Black
def calculate_spell_dc(spell_level: int, casting_ability: int) -> int:
    base_dc = 8 + spell_level + casting_ability
    if spell_level == 0:
        base_dc = casting_ability
    return base_dc


spell_data = {
    "name": "Fireball",
    "level": 3,
    "school": "evocation",
    "damage": "8d6",
}
```

#### Function Formatting

```python
# Good - Black formatted
async def lookup_spell(
    name: str | None = None,
    level: int | None = None,
    school: str | None = None,
    class_key: str | None = None,
    concentration: bool | None = None,
    ritual: bool | None = None,
    casting_time: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Look up spell information from Open5e API."""
    # Implementation
```

#### List and Dictionary Formatting

```python
# Good - Consistent formatting
spell_components = ["V", "S", "M"]
spell_properties = [
    "verbal",
    "somatic",
    "material",
]

spell_data = {
    "name": "Fireball",
    "level": 3,
    "school": "evocation",
    "casting_time": "1 action",
    "components": spell_components,
    "properties": spell_properties,
}
```

## Quality Gates

### Pre-commit Quality Gates

#### Must Pass
1. **Black Formatting**: Code must be properly formatted
2. **Ruff Linting**: No linting errors allowed
3. **MyPy Type Checking**: No type errors allowed
4. **Basic Checks**: No trailing whitespace, proper file endings

#### Warnings
1. **Large Files**: Warning for files >1MB
2. **Debug Statements**: Warning for print statements in production code

### CI/CD Quality Gates

#### Automated Checks
```yaml
# GitHub Actions example
- name: Run quality checks
  run: |
    uv run ruff check src/ tests/
    uv run mypy src/
    uv run black --check src/ tests/

- name: Run tests with coverage
  run: |
    uv run pytest --cov=lorekeeper_mcp --cov-fail-under=90
```

#### Quality Metrics
- **Test Coverage**: Minimum 90%
- **Type Coverage**: 100% for public APIs
- **Linting**: Zero errors
- **Security**: No high-severity issues

## Best Practices

### Code Organization

#### File Structure
```python
# Good file organization
"""Module docstring explaining purpose."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from lorekeeper_mcp.config import settings
from lorekeeper_mcp.cache import db

# Constants
MAX_SPELL_LEVEL = 9
DEFAULT_CACHE_TTL = 7 * 24 * 3600

# Type definitions
SpellData = Dict[str, Any]

# Classes
class SpellLookup:
    """Class for spell lookup operations."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self.client = http_client

    async def lookup(self, name: str) -> Optional[SpellData]:
        """Look up spell by name."""
        # Implementation

# Functions
async def fetch_spell_data(name: str) -> SpellData:
    """Fetch spell data from API."""
    # Implementation

# Main execution
async def main() -> None:
    """Main entry point."""
    # Implementation
```

#### Error Handling
```python
# Good error handling
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SpellLookupError(Exception):
    """Exception raised when spell lookup fails."""
    pass

async def lookup_spell_safe(name: str) -> Optional[Dict[str, Any]]:
    """Look up spell with proper error handling."""
    try:
        return await lookup_spell(name)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error looking up spell {name}: {e}")
        raise SpellLookupError(f"Failed to lookup spell: {e}") from e
    except httpx.RequestError as e:
        logger.error(f"Network error looking up spell {name}: {e}")
        raise SpellLookupError(f"Network error: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error looking up spell {name}: {e}")
        raise SpellLookupError(f"Unexpected error: {e}") from e
```

#### Documentation
```python
# Good documentation
def calculate_spell_save_dc(
    spell_level: int,
    casting_ability_score: int,
    proficiency_bonus: int = 2,
) -> int:
    """Calculate spell save DC.

    The save DC determines the difficulty for creatures to save against
    a spell that requires a saving throw.

    Args:
        spell_level: The level of the spell (0-9).
        casting_ability_score: The character's casting ability score.
        proficiency_bonus: Character's proficiency bonus (default: 2).

    Returns:
        The calculated save DC as an integer.

    Raises:
        ValueError: If spell_level is not between 0 and 9.
        ValueError: If casting_ability_score is not between 1 and 20.

    Example:
        >>> calculate_spell_save_dc(3, 16, 2)
        15
    """
    if not 0 <= spell_level <= 9:
        raise ValueError("Spell level must be between 0 and 9")

    if not 1 <= casting_ability_score <= 20:
        raise ValueError("Ability score must be between 1 and 20")

    base_dc = 8 + spell_level + proficiency_bonus
    ability_modifier = (casting_ability_score - 10) // 2

    return base_dc + ability_modifier
```

### Performance Considerations

#### Efficient Data Structures
```python
# Good - Efficient data structures
from collections import defaultdict
from typing import Dict, List

def group_spells_by_level(spells: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """Group spells by their level using defaultdict."""
    spell_groups = defaultdict(list)

    for spell in spells:
        level = spell.get("level", 0)
        spell_groups[level].append(spell)

    return dict(spell_groups)

# Bad - Inefficient approach
def group_spells_by_level_slow(spells: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """Inefficient spell grouping."""
    spell_groups = {}

    for spell in spells:
        level = spell.get("level", 0)
        if level not in spell_groups:
            spell_groups[level] = []
        spell_groups[level].append(spell)

    return spell_groups
```

#### Async Best Practices
```python
# Good - Proper async patterns
import asyncio
from typing import List, Optional

async def fetch_multiple_spells(spell_names: List[str]) -> List[Optional[Dict[str, Any]]]:
    """Fetch multiple spells concurrently."""
    tasks = [fetch_spell(name) for name in spell_names]
    return await asyncio.gather(*tasks, return_exceptions=False)

# Bad - Sequential async calls
async def fetch_multiple_spells_slow(spell_names: List[str]) -> List[Optional[Dict[str, Any]]]:
    """Fetch spells sequentially (slow)."""
    results = []
    for name in spell_names:
        spell = await fetch_spell(name)
        results.append(spell)
    return results
```

This comprehensive code quality guide ensures that LoreKeeper MCP maintains high standards of code quality, readability, and maintainability.
