"""Tests for the repository base protocol."""

from typing import Any

import pytest

from lorekeeper_mcp.models import Spell
from lorekeeper_mcp.repositories.base import Repository


class MockRepository(Repository[Spell]):
    """Mock implementation of Repository protocol for testing."""

    def __init__(self) -> None:
        self.spells: list[Spell] = []

    async def get_all(self) -> list[Spell]:
        """Return all spells."""
        return self.spells

    async def search(self, **filters: Any) -> list[Spell]:
        """Search for spells matching filters."""
        results = self.spells
        for key, value in filters.items():
            if key == "name" and value:
                results = [s for s in results if value.lower() in s.name.lower()]
            elif key == "level" and value is not None:
                results = [s for s in results if s.level == value]
        return results


@pytest.mark.asyncio
async def test_repository_protocol_get_all() -> None:
    """Test that Repository protocol defines get_all method."""
    repo = MockRepository()
    result = await repo.get_all()
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_repository_protocol_search() -> None:
    """Test that Repository protocol defines search method."""
    repo = MockRepository()
    result = await repo.search(name="fireball")
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_repository_is_generic() -> None:
    """Test that Repository supports generic typing."""
    repo: Repository[Spell] = MockRepository()
    result = await repo.get_all()
    assert isinstance(result, list)
