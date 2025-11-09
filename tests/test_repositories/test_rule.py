"""Tests for RuleRepository implementation."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from lorekeeper_mcp.repositories.rule import RuleRepository


@pytest.fixture
def mock_cache() -> MagicMock:
    """Create mock cache for testing."""
    cache = MagicMock()
    cache.get_entities = AsyncMock()
    cache.store_entities = AsyncMock()
    return cache


@pytest.fixture
def mock_client() -> MagicMock:
    """Create mock API client for testing."""
    client = MagicMock()
    client.get_rules = AsyncMock()
    client.get_damage_types = AsyncMock()
    client.get_skills = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_rule_repository_search_rules(mock_cache: MagicMock, mock_client: MagicMock) -> None:
    """Test search filtering by rules."""
    mock_cache.get_entities.return_value = []
    mock_client.get_rules.return_value = [{"name": "Action Economy", "slug": "action-economy"}]
    mock_cache.store_entities.return_value = 1

    repo = RuleRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(rule_type="rule")

    assert len(results) == 1
    mock_client.get_rules.assert_called_once()


@pytest.mark.asyncio
async def test_rule_repository_search_damage_types(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test search filtering by damage types."""
    mock_cache.get_entities.return_value = [{"name": "Fire", "slug": "fire"}]

    repo = RuleRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(rule_type="damage_type")

    assert len(results) == 1
    mock_client.get_damage_types.assert_not_called()


@pytest.mark.asyncio
async def test_rule_repository_search_skills(mock_cache: MagicMock, mock_client: MagicMock) -> None:
    """Test search filtering by skills."""
    mock_cache.get_entities.return_value = []
    mock_client.get_skills.return_value = [{"name": "Acrobatics", "slug": "acrobatics"}]
    mock_cache.store_entities.return_value = 1

    repo = RuleRepository(client=mock_client, cache=mock_cache)
    results = await repo.search(rule_type="skill")

    assert len(results) == 1
    mock_client.get_skills.assert_called_once()
