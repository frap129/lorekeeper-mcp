"""Repository for rules with cache-aside pattern."""

from typing import Any, Protocol

from lorekeeper_mcp.repositories.base import Repository


class RuleClient(Protocol):
    """Protocol for rule API client."""

    async def get_rules(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch rules from API."""
        ...

    async def get_damage_types(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch damage types from API."""
        ...

    async def get_skills(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch skills from API."""
        ...


class RuleCache(Protocol):
    """Protocol for rule cache."""

    async def get_entities(self, entity_type: str, **filters: Any) -> list[dict[str, Any]]:
        """Retrieve entities from cache."""
        ...

    async def store_entities(self, entities: list[dict[str, Any]], entity_type: str) -> int:
        """Store entities in cache."""
        ...


class RuleRepository(Repository[dict[str, Any]]):
    """Repository for D&D 5e rules with cache-aside pattern.

    Handles rules, damage types, and skills.
    """

    def __init__(self, client: RuleClient, cache: RuleCache) -> None:
        """Initialize RuleRepository.

        Args:
            client: API client with rule methods
            cache: Cache implementation
        """
        self.client = client
        self.cache = cache

    async def get_all(self) -> list[dict[str, Any]]:
        """Retrieve all rules (not implemented).

        Returns:
            Empty list
        """
        return []

    async def search(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for rules with type routing.

        Args:
            **filters: Must include 'rule_type' (rule, damage_type, or skill).

        Returns:
            List of matching rules
        """
        rule_type = filters.pop("rule_type", None)

        if rule_type == "rule":
            return await self._search_rules(**filters)
        if rule_type == "damage_type":
            return await self._search_damage_types(**filters)
        if rule_type == "skill":
            return await self._search_skills(**filters)
        return []

    async def _search_rules(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for rules."""
        cached = await self.cache.get_entities("rules", **filters)

        if cached:
            return cached

        rules: list[dict[str, Any]] = await self.client.get_rules(**filters)

        if rules:
            await self.cache.store_entities(rules, "rules")

        return rules

    async def _search_damage_types(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for damage types."""
        cached = await self.cache.get_entities("damage_types", **filters)

        if cached:
            return cached

        damage_types: list[dict[str, Any]] = await self.client.get_damage_types(**filters)

        if damage_types:
            await self.cache.store_entities(damage_types, "damage_types")

        return damage_types

    async def _search_skills(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for skills."""
        cached = await self.cache.get_entities("skills", **filters)

        if cached:
            return cached

        skills: list[dict[str, Any]] = await self.client.get_skills(**filters)

        if skills:
            await self.cache.store_entities(skills, "skills")

        return skills
