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
    results = await repo.search(rule_type="damage-type")

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


@pytest.mark.asyncio
async def test_rule_repository_search_with_document_filter(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test RuleRepository.search with document filter."""
    # Return filtered results from cache when document is specified
    mock_cache.get_entities.return_value = [
        {"name": "Action Economy", "slug": "action-economy", "document": "srd-5e"}
    ]

    repo = RuleRepository(client=mock_client, cache=mock_cache)

    # Search with document filter
    rules = await repo.search(rule_type="rule", document=["srd-5e"])

    assert len(rules) == 1
    assert rules[0]["document"] == "srd-5e"
    # Verify document was passed to cache query
    mock_cache.get_entities.assert_called_with("rules", document=["srd-5e"])


@pytest.mark.asyncio
async def test_rule_repository_search_document_filter_cache_miss(
    mock_cache: MagicMock, mock_client: MagicMock
) -> None:
    """Test document filter removed from API call on cache miss."""
    # Cache miss - return empty, API returns results
    mock_cache.get_entities.return_value = []
    mock_client.get_rules.return_value = [
        {"name": "Action Economy", "slug": "action-economy", "document": "srd-5e"}
    ]
    mock_cache.store_entities.return_value = 1

    repo = RuleRepository(client=mock_client, cache=mock_cache)

    # Search with document filter
    rules = await repo.search(rule_type="rule", document=["srd-5e"])

    assert len(rules) == 1
    # Verify cache was queried with document filter
    mock_cache.get_entities.assert_called_with("rules", document=["srd-5e"])
    # Verify API was called WITHOUT document filter
    mock_client.get_rules.assert_called_once()
    # Get the actual call args to verify document was not passed
    call_kwargs = mock_client.get_rules.call_args[1]
    assert "document" not in call_kwargs
