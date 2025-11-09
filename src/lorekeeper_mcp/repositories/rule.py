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

    async def _search_conditions(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for conditions."""
        cached = await self.cache.get_entities("conditions", **filters)

        if cached:
            return cached

        conditions: list[dict[str, Any]] = await self.client.get_conditions_dnd5e(**filters)

        if conditions:
            await self.cache.store_entities(conditions, "conditions")

        return conditions

    async def _search_weapon_properties(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for weapon properties."""
        cached = await self.cache.get_entities("weapon_properties", **filters)

        if cached:
            return cached

        properties: list[dict[str, Any]] = await self.client.get_weapon_properties(**filters)

        if properties:
            await self.cache.store_entities(properties, "weapon_properties")

        return properties

    async def _search_ability_scores(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for ability scores."""
        cached = await self.cache.get_entities("ability_scores", **filters)

        if cached:
            return cached

        ability_scores: list[dict[str, Any]] = await self.client.get_ability_scores(**filters)

        if ability_scores:
            await self.cache.store_entities(ability_scores, "ability_scores")

        return ability_scores

    async def _search_magic_schools(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for magic schools."""
        cached = await self.cache.get_entities("magic_schools", **filters)

        if cached:
            return cached

        schools: list[dict[str, Any]] = await self.client.get_magic_schools(**filters)

        if schools:
            await self.cache.store_entities(schools, "magic_schools")

        return schools

    async def _search_languages(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for languages."""
        cached = await self.cache.get_entities("languages", **filters)

        if cached:
            return cached

        languages: list[dict[str, Any]] = await self.client.get_languages(**filters)

        if languages:
            await self.cache.store_entities(languages, "languages")

        return languages

    async def _search_proficiencies(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for proficiencies."""
        cached = await self.cache.get_entities("proficiencies", **filters)

        if cached:
            return cached

        proficiencies: list[dict[str, Any]] = await self.client.get_proficiencies(**filters)

        if proficiencies:
            await self.cache.store_entities(proficiencies, "proficiencies")

        return proficiencies

    async def _search_alignments(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for alignments."""
        cached = await self.cache.get_entities("alignments", **filters)

        if cached:
            return cached

        alignments: list[dict[str, Any]] = await self.client.get_alignments(**filters)

        if alignments:
            await self.cache.store_entities(alignments, "alignments")

        return alignments
