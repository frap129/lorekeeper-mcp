"""Tests for repository factory."""

from unittest.mock import MagicMock

import pytest

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.repositories.character_option import CharacterOptionRepository
from lorekeeper_mcp.repositories.equipment import EquipmentRepository
from lorekeeper_mcp.repositories.factory import RepositoryFactory
from lorekeeper_mcp.repositories.monster import MonsterRepository
from lorekeeper_mcp.repositories.rule import RuleRepository
from lorekeeper_mcp.repositories.spell import SpellRepository


@pytest.mark.asyncio
async def test_factory_create_spell_repository():
    """Test creating SpellRepository via factory."""
    repo = RepositoryFactory.create_spell_repository()
    assert isinstance(repo, SpellRepository)
    assert repo.client is not None
    assert repo.cache is not None


@pytest.mark.asyncio
async def test_factory_create_spell_repository_with_overrides():
    """Test creating SpellRepository with client/cache overrides."""
    mock_client = MagicMock()
    mock_cache = MagicMock()

    repo = RepositoryFactory.create_spell_repository(client=mock_client, cache=mock_cache)

    assert isinstance(repo, SpellRepository)
    assert repo.client is mock_client
    assert repo.cache is mock_cache


@pytest.mark.asyncio
async def test_factory_create_monster_repository():
    """Test creating MonsterRepository via factory."""
    repo = RepositoryFactory.create_monster_repository()
    assert isinstance(repo, MonsterRepository)
    assert repo.client is not None
    assert repo.cache is not None


@pytest.mark.asyncio
async def test_factory_create_monster_repository_with_overrides():
    """Test creating MonsterRepository with client/cache overrides."""
    mock_client = MagicMock()
    mock_cache = MagicMock()

    repo = RepositoryFactory.create_monster_repository(client=mock_client, cache=mock_cache)

    assert isinstance(repo, MonsterRepository)
    assert repo.client is mock_client
    assert repo.cache is mock_cache


@pytest.mark.asyncio
async def test_factory_create_equipment_repository():
    """Test creating EquipmentRepository via factory."""
    repo = RepositoryFactory.create_equipment_repository()
    assert isinstance(repo, EquipmentRepository)
    assert repo.client is not None
    assert repo.cache is not None


@pytest.mark.asyncio
async def test_factory_create_equipment_repository_with_overrides():
    """Test creating EquipmentRepository with client/cache overrides."""
    mock_client = MagicMock()
    mock_cache = MagicMock()

    repo = RepositoryFactory.create_equipment_repository(client=mock_client, cache=mock_cache)

    assert isinstance(repo, EquipmentRepository)
    assert repo.client is mock_client
    assert repo.cache is mock_cache


@pytest.mark.asyncio
async def test_factory_create_character_option_repository():
    """Test creating CharacterOptionRepository via factory."""
    repo = RepositoryFactory.create_character_option_repository()
    assert isinstance(repo, CharacterOptionRepository)
    assert repo.client is not None
    assert repo.cache is not None


@pytest.mark.asyncio
async def test_factory_create_character_option_repository_with_overrides():
    """Test creating CharacterOptionRepository with client/cache overrides."""
    mock_client = MagicMock()
    mock_cache = MagicMock()

    repo = RepositoryFactory.create_character_option_repository(
        client=mock_client, cache=mock_cache
    )

    assert isinstance(repo, CharacterOptionRepository)
    assert repo.client is mock_client
    assert repo.cache is mock_cache


@pytest.mark.asyncio
async def test_factory_create_rule_repository():
    """Test creating RuleRepository via factory."""
    repo = RepositoryFactory.create_rule_repository()
    assert isinstance(repo, RuleRepository)
    assert repo.client is not None
    assert repo.cache is not None


@pytest.mark.asyncio
async def test_factory_create_rule_repository_with_overrides():
    """Test creating RuleRepository with client/cache overrides."""
    mock_client = MagicMock()
    mock_cache = MagicMock()

    repo = RepositoryFactory.create_rule_repository(client=mock_client, cache=mock_cache)

    assert isinstance(repo, RuleRepository)
    assert repo.client is mock_client
    assert repo.cache is mock_cache


@pytest.mark.asyncio
async def test_factory_creates_shared_cache_by_default():
    """Test that factory uses shared cache instance by default."""
    # Create multiple repositories
    spell_repo = RepositoryFactory.create_spell_repository()
    monster_repo = RepositoryFactory.create_monster_repository()
    equipment_repo = RepositoryFactory.create_equipment_repository()

    # Cache instances should be the same (singleton pattern)
    assert spell_repo.cache is monster_repo.cache
    assert monster_repo.cache is equipment_repo.cache


@pytest.mark.asyncio
async def test_factory_all_repositories_created_successfully():
    """Test that all repositories can be created successfully."""
    repos = {
        "spell": RepositoryFactory.create_spell_repository(),
        "monster": RepositoryFactory.create_monster_repository(),
        "equipment": RepositoryFactory.create_equipment_repository(),
        "character_option": RepositoryFactory.create_character_option_repository(),
        "rule": RepositoryFactory.create_rule_repository(),
    }

    for name, repo in repos.items():
        assert repo is not None, f"{name} repository is None"
        assert hasattr(repo, "get_all"), f"{name} repository missing get_all"
        assert hasattr(repo, "search"), f"{name} repository missing search"
        assert hasattr(repo, "client"), f"{name} repository missing client"
        assert hasattr(repo, "cache"), f"{name} repository missing cache"


def test_create_monster_repository_default_uses_v2():
    """Test that create_monster_repository uses Open5eV2Client by default."""
    # Clear any cached instance
    RepositoryFactory._cache_instance = None

    repo = RepositoryFactory.create_monster_repository()

    assert isinstance(repo.client, Open5eV2Client)
