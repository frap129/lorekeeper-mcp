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

    async def get_weapon_properties(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch weapon properties from API."""
        ...

    async def get_skills(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch skills from API."""
        ...

    async def get_ability_scores(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch ability scores from API."""
        ...

    async def get_magic_schools(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch magic schools from API."""
        ...

    async def get_languages(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch languages from API."""
        ...

    async def get_proficiencies(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch proficiencies from API."""
        ...

    async def get_alignments(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch alignments from API."""
        ...

    async def get_conditions_dnd5e(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch conditions from API."""
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
            **filters: Must include 'rule_type' (rule, condition, damage-type,
                weapon-property, skill, ability-score, magic-school, language,
                proficiency, or alignment).

        Returns:
            List of matching rules
        """
        rule_type = filters.pop("rule_type", None)

        if rule_type == "rule":
            return await self._search_rules(**filters)
        if rule_type == "condition":
            return await self._search_conditions(**filters)
        if rule_type == "damage-type":
            return await self._search_damage_types(**filters)
        if rule_type == "weapon-property":
            return await self._search_weapon_properties(**filters)
        if rule_type == "skill":
            return await self._search_skills(**filters)
        if rule_type == "ability-score":
            return await self._search_ability_scores(**filters)
        if rule_type == "magic-school":
            return await self._search_magic_schools(**filters)
        if rule_type == "language":
            return await self._search_languages(**filters)
        if rule_type == "proficiency":
            return await self._search_proficiencies(**filters)
        if rule_type == "alignment":
            return await self._search_alignments(**filters)
        return []

    async def _search_rules(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for rules."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("rules", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Fetch from API with filters and limit
        rules: list[dict[str, Any]] = await self.client.get_rules(limit=limit, **filters)

        if rules:
            await self.cache.store_entities(rules, "rules")

        return rules

    async def _search_damage_types(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for damage types."""
        # Extract limit and name parameters (not cache filter fields)
        limit = filters.pop("limit", None)
        name = filters.pop("name", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("damagetypes", **filters)

        if cached:
            results = cached
        else:
            # Fetch from API with filters and limit
            damage_types: list[dict[str, Any]] = await self.client.get_damage_types(
                limit=limit, **filters
            )

            if damage_types:
                await self.cache.store_entities(damage_types, "damagetypes")

            results = damage_types

        # Client-side filtering by name if requested
        if name:
            name_lower = name.lower()
            results = [r for r in results if name_lower in r.get("name", "").lower()]

        return results[:limit] if limit else results

    async def _search_skills(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for skills."""
        # Extract limit and name parameters (not cache filter fields)
        limit = filters.pop("limit", None)
        name = filters.pop("name", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("skills", **filters)

        if cached:
            results = cached
        else:
            # Fetch from API with filters and limit
            skills: list[dict[str, Any]] = await self.client.get_skills(limit=limit, **filters)

            if skills:
                await self.cache.store_entities(skills, "skills")

            results = skills

        # Client-side filtering by name if requested
        if name:
            name_lower = name.lower()
            results = [r for r in results if name_lower in r.get("name", "").lower()]

        return results[:limit] if limit else results

    async def _search_conditions(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for conditions."""
        # Extract limit and name parameters (not cache filter fields)
        limit = filters.pop("limit", None)
        name = filters.pop("name", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("conditions", **filters)

        if cached:
            results = cached
        else:
            # Fetch from API with filters and limit
            conditions: list[dict[str, Any]] = await self.client.get_conditions_dnd5e(
                limit=limit, **filters
            )

            if conditions:
                await self.cache.store_entities(conditions, "conditions")

            results = conditions

        # Client-side filtering by name if requested
        if name:
            name_lower = name.lower()
            results = [r for r in results if name_lower in r.get("name", "").lower()]

        return results[:limit] if limit else results

    async def _search_weapon_properties(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for weapon properties."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("weapon_properties", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Fetch from API with filters and limit
        properties: list[dict[str, Any]] = await self.client.get_weapon_properties(
            limit=limit, **filters
        )

        if properties:
            await self.cache.store_entities(properties, "weapon_properties")

        return properties

    async def _search_ability_scores(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for ability scores."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("ability_scores", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Fetch from API with filters and limit
        ability_scores: list[dict[str, Any]] = await self.client.get_ability_scores(
            limit=limit, **filters
        )

        if ability_scores:
            await self.cache.store_entities(ability_scores, "ability_scores")

        return ability_scores

    async def _search_magic_schools(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for magic schools."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("magic_schools", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Fetch from API with filters and limit
        schools: list[dict[str, Any]] = await self.client.get_magic_schools(limit=limit, **filters)

        if schools:
            await self.cache.store_entities(schools, "magic_schools")

        return schools

    async def _search_languages(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for languages."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("languages", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Fetch from API with filters and limit
        languages: list[dict[str, Any]] = await self.client.get_languages(limit=limit, **filters)

        if languages:
            await self.cache.store_entities(languages, "languages")

        return languages

    async def _search_proficiencies(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for proficiencies."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("proficiencies", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Fetch from API with filters and limit
        proficiencies: list[dict[str, Any]] = await self.client.get_proficiencies(
            limit=limit, **filters
        )

        if proficiencies:
            await self.cache.store_entities(proficiencies, "proficiencies")

        return proficiencies

    async def _search_alignments(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for alignments."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("alignments", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Fetch from API with filters and limit
        alignments: list[dict[str, Any]] = await self.client.get_alignments(limit=limit, **filters)

        if alignments:
            await self.cache.store_entities(alignments, "alignments")

        return alignments
