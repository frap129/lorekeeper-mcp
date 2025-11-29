"""Factory for creating repository instances with dependency injection."""

from typing import Any, Protocol

from lorekeeper_mcp.api_clients.open5e_v2 import Open5eV2Client
from lorekeeper_mcp.cache.factory import get_cache_from_config
from lorekeeper_mcp.repositories.character_option import CharacterOptionRepository
from lorekeeper_mcp.repositories.creature import CreatureRepository
from lorekeeper_mcp.repositories.equipment import EquipmentRepository
from lorekeeper_mcp.repositories.rule import RuleRepository
from lorekeeper_mcp.repositories.spell import SpellRepository


class _CacheProtocol(Protocol):
    """Protocol for cache implementations used by factory."""

    async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        """Retrieve entities from cache."""
        ...

    async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
        """Store entities in cache."""
        ...

    async def semantic_search(
        self,
        entity_type: str,
        query: str,
        limit: int = 20,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Perform semantic search (optional - may raise NotImplementedError)."""
        ...


class RepositoryFactory:
    """Factory for creating repository instances with dependency injection.

    Provides static factory methods for creating properly configured repository
    instances. Supports optional client and cache overrides for testing.

    Uses the cache factory to create cache instances based on environment
    configuration (LOREKEEPER_CACHE_BACKEND).
    """

    _cache_instance: _CacheProtocol | None = None

    @staticmethod
    def _get_cache() -> _CacheProtocol:
        """Get or create the shared cache instance.

        Creates cache based on environment configuration:
        - LOREKEEPER_CACHE_BACKEND=milvus (default): MilvusCache with semantic search
        - LOREKEEPER_CACHE_BACKEND=sqlite: SQLiteCache (legacy, no semantic search)

        Returns:
            A cache instance implementing the CacheProtocol.
        """
        if RepositoryFactory._cache_instance is None:
            RepositoryFactory._cache_instance = get_cache_from_config()
        assert RepositoryFactory._cache_instance is not None
        return RepositoryFactory._cache_instance

    @staticmethod
    def reset_cache() -> None:
        """Reset the cached cache instance.

        Useful for testing or when configuration changes require a new cache.
        """
        RepositoryFactory._cache_instance = None

    @staticmethod
    def create_spell_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> SpellRepository:
        """Create a SpellRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to cache from config.

        Returns:
            A configured SpellRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return SpellRepository(client=client, cache=cache)

    @staticmethod
    def create_creature_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> CreatureRepository:
        """Create a CreatureRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to cache from config.

        Returns:
            A configured CreatureRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return CreatureRepository(client=client, cache=cache)

    @staticmethod
    def create_equipment_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> EquipmentRepository:
        """Create an EquipmentRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to cache from config.

        Returns:
            A configured EquipmentRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return EquipmentRepository(client=client, cache=cache)  # type: ignore[arg-type]

    @staticmethod
    def create_character_option_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> CharacterOptionRepository:
        """Create a CharacterOptionRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to cache from config.

        Returns:
            A configured CharacterOptionRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return CharacterOptionRepository(client=client, cache=cache)

    @staticmethod
    def create_rule_repository(
        client: Any | None = None, cache: _CacheProtocol | None = None
    ) -> RuleRepository:
        """Create a RuleRepository instance.

        Args:
            client: Optional custom client instance. Defaults to Open5eV2Client.
            cache: Optional custom cache instance. Defaults to cache from config.

        Returns:
            A configured RuleRepository instance.
        """
        if client is None:
            client = Open5eV2Client()
        if cache is None:
            cache = RepositoryFactory._get_cache()
        return RuleRepository(client=client, cache=cache)
