"""Repository for rules with cache-aside pattern."""

from typing import Any, Protocol

from lorekeeper_mcp.repositories.base import Repository


class RuleClient(Protocol):
    """Protocol for rule API client."""

    async def get_rules_v2(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch rules from API."""
        ...

    async def get_damage_types_v2(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch damage types from API."""
        ...

    async def get_weapon_properties_v2(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch weapon properties from API."""
        ...

    async def get_skills_v2(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch skills from API."""
        ...

    async def get_abilities(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch ability scores from API."""
        ...

    async def get_spell_schools_v2(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch magic schools from API."""
        ...

    async def get_languages_v2(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch languages from API."""
        ...

    async def get_alignments_v2(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch alignments from API."""
        ...

    async def get_conditions(self, **filters: Any) -> list[dict[str, Any]]:
        """Fetch conditions from API."""
        ...


class RuleCache(Protocol):
    """Protocol for rule cache.

    Supports both structured filtering via get_entities() and
    semantic search via semantic_search() for Milvus backend.
    """

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

        Supports both structured filtering and semantic search.

        Args:
            **filters: Must include 'rule_type' (rule, condition, damage-type,
                weapon-property, skill, ability-score, magic-school, language,
                proficiency, or alignment).
                - semantic_query: Natural language search query (uses vector search)

        Returns:
            List of matching rules
        """
        rule_type = filters.pop("rule_type", None)
        semantic_query = filters.pop("semantic_query", None)

        if semantic_query:
            return await self._semantic_search(semantic_query, rule_type=rule_type, **filters)

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

    async def _semantic_search(
        self,
        query: str,
        rule_type: str | None = None,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Perform semantic search for rules.

        Args:
            query: Natural language search query
            rule_type: Optional type filter
            **filters: Additional scalar filters

        Returns:
            List of rules ranked by semantic similarity
        """
        limit = filters.pop("limit", None)
        search_limit = limit or 20

        # Map rule types to collection names
        type_to_collection = {
            "rule": "rules",
            "condition": "conditions",
            "damage-type": "damagetypes",
            "weapon-property": "weapon_properties",
            "skill": "skills",
            "ability-score": "ability_scores",
            "magic-school": "magic_schools",
            "language": "languages",
            "proficiency": "proficiencies",
            "alignment": "alignments",
        }

        if rule_type and rule_type in type_to_collection:
            collections = [type_to_collection[rule_type]]
        else:
            # Search all rule types
            collections = list(type_to_collection.values())

        all_results: list[dict[str, Any]] = []

        for collection_name in collections:
            try:
                results = await self.cache.semantic_search(
                    collection_name, query, limit=search_limit, **filters
                )
                all_results.extend(results)
            except NotImplementedError:
                # Fall back to structured search
                cached = await self.cache.get_entities(collection_name, name=query, **filters)
                all_results.extend(cached)

        return all_results[:limit] if limit else all_results

    async def _search_rules(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for rules."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        # Note: document filter is kept in filters for cache (cache-only filter)
        cached = await self.cache.get_entities("rules", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Cache miss - fetch from API with filters and limit
        # Remove document from API filters (cache-only filter)
        api_filters = dict(filters)
        api_filters.pop("document", None)
        rules: list[dict[str, Any]] = await self.client.get_rules_v2(limit=limit, **api_filters)

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
            damage_types: list[dict[str, Any]] = await self.client.get_damage_types_v2(
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
            skills: list[dict[str, Any]] = await self.client.get_skills_v2(limit=limit, **filters)

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
            conditions: list[dict[str, Any]] = await self.client.get_conditions(
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
        properties: list[dict[str, Any]] = await self.client.get_weapon_properties_v2(
            limit=limit, **filters
        )

        if properties:
            await self.cache.store_entities(properties, "weapon_properties")

        return properties

    async def _search_ability_scores(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for ability scores."""
        # Extract limit and name parameters (not cache filter fields)
        limit = filters.pop("limit", None)
        name = filters.pop("name", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("ability_scores", **filters)

        if cached:
            results = cached
        else:
            # Fetch from API with filters and limit
            ability_scores: list[dict[str, Any]] = await self.client.get_abilities(
                limit=limit, **filters
            )

            if ability_scores:
                await self.cache.store_entities(ability_scores, "ability_scores")

            results = ability_scores

        # Client-side filtering by name if requested
        if name:
            name_lower = name.lower()
            results = [r for r in results if name_lower in r.get("name", "").lower()]

        return results[:limit] if limit else results

    async def _search_magic_schools(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for magic schools."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("magic_schools", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Fetch from API with filters and limit
        schools: list[dict[str, Any]] = await self.client.get_spell_schools_v2(
            limit=limit, **filters
        )

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
        languages: list[dict[str, Any]] = await self.client.get_languages_v2(limit=limit, **filters)

        if languages:
            await self.cache.store_entities(languages, "languages")

        return languages

    async def _search_proficiencies(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for proficiencies.

        Note: Proficiencies are not available in Open5e v2 API.
        This method returns cached data if available, otherwise empty list.
        """
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("proficiencies", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Proficiencies not available in Open5e v2 API
        return []

    async def _search_alignments(self, **filters: Any) -> list[dict[str, Any]]:
        """Search for alignments."""
        # Extract limit parameter (not a cache filter field)
        limit = filters.pop("limit", None)

        # Try cache first with valid filter fields only
        cached = await self.cache.get_entities("alignments", **filters)

        if cached:
            return cached[:limit] if limit else cached

        # Fetch from API with filters and limit
        alignments: list[dict[str, Any]] = await self.client.get_alignments_v2(
            limit=limit, **filters
        )

        if alignments:
            await self.cache.store_entities(alignments, "alignments")

        return alignments
