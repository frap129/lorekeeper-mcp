"""Client for Open5e API v2 (spells, weapons, armor, etc.)."""

from typing import Any

from lorekeeper_mcp.api_clients.base import BaseHttpClient
from lorekeeper_mcp.api_clients.models import Armor, Monster, Spell, Weapon


class Open5eV2Client(BaseHttpClient):
    """Client for Open5e API v2 endpoints."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Open5e v2 client.

        Args:
            **kwargs: Additional arguments for BaseHttpClient
        """
        super().__init__(base_url="https://api.open5e.com/v2", **kwargs)

    async def get_spells(
        self,
        level: int | None = None,
        school: str | None = None,
        **kwargs: Any,
    ) -> list[Spell]:
        """Get spells from Open5e API v2.

        Args:
            level: Filter by spell level
            school: Filter by spell school (client-side filtering)
            **kwargs: Additional API parameters

        Returns:
            List of Spell models
        """
        cache_filters: dict[str, Any] = {}
        params: dict[str, Any] = {}

        if level is not None:
            cache_filters["level"] = level
            params["level"] = level

        # Note: school parameter is not supported server-side by Open5e v2 API,
        # so we filter client-side below
        if school:
            cache_filters["school"] = school

        # Add any additional parameters
        params.update(kwargs)

        result = await self.make_request(
            "/spells/",
            use_entity_cache=True,
            entity_type="spells",
            cache_filters=cache_filters,
            params=params,
        )

        spell_dicts: list[dict[str, Any]] = (
            result if isinstance(result, list) else result.get("results", [])
        )

        spells = [Spell.model_validate(spell) for spell in spell_dicts]

        # Client-side filtering for school (not supported server-side)
        if school:
            spells = [spell for spell in spells if spell.school.lower() == school.lower()]

        return spells

    async def get_weapons(self, **kwargs: Any) -> list[Weapon]:
        """Get weapons from Open5e API v2."""
        result = await self.make_request(
            "/weapons/",
            use_entity_cache=True,
            entity_type="weapons",
            params=kwargs,
        )

        weapon_dicts: list[dict[str, Any]] = (
            result if isinstance(result, list) else result.get("results", [])
        )

        return [Weapon.model_validate(weapon) for weapon in weapon_dicts]

    async def get_armor(self, **kwargs: Any) -> list[Armor]:
        """Get armor from Open5e API v2."""
        result = await self.make_request(
            "/armor/",
            use_entity_cache=True,
            entity_type="armor",
            params=kwargs,
        )

        armor_dicts: list[dict[str, Any]] = (
            result if isinstance(result, list) else result.get("results", [])
        )

        return [Armor.model_validate(armor) for armor in armor_dicts]

    async def get_backgrounds(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character backgrounds."""
        result = await self.make_request(
            "/backgrounds/",
            use_entity_cache=True,
            entity_type="backgrounds",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_feats(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character feats."""
        result = await self.make_request(
            "/feats/",
            use_entity_cache=True,
            entity_type="feats",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_conditions(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get game conditions."""
        result = await self.make_request(
            "/conditions/",
            use_entity_cache=True,
            entity_type="conditions",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.6: Item-related methods
    async def get_items(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get items from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of item dictionaries
        """
        result = await self.make_request(
            "/items/",
            use_entity_cache=True,
            entity_type="items",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_item_sets(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get item sets from Open5e API v2.

        Item sets are collections of items (e.g., core rulebook items).
        Uses 30-day cache TTL for reference data.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of item set dictionaries
        """
        result = await self.make_request(
            "/itemsets/",
            use_entity_cache=True,
            entity_type="itemsets",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_item_categories(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get item categories from Open5e API v2.

        Item categories describe types of items (e.g., Wondrous Item, Potion).
        Uses 30-day cache TTL for reference data.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of item category dictionaries
        """
        result = await self.make_request(
            "/itemcategories/",
            use_entity_cache=True,
            entity_type="itemcategories",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.7: Creature methods
    async def get_creatures(self, **kwargs: Any) -> list[Monster]:
        """Get creatures from Open5e API v2.

        Creatures are returned as Monster models compatible with v1.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of Monster models
        """
        result = await self.make_request(
            "/creatures/",
            use_entity_cache=True,
            entity_type="creatures",
            params=kwargs,
        )

        creature_dicts: list[dict[str, Any]] = (
            result if isinstance(result, list) else result.get("results", [])
        )

        return [Monster.model_validate(creature) for creature in creature_dicts]

    async def get_creature_types(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get creature type definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of creature type dictionaries
        """
        result = await self.make_request(
            "/creaturetypes/",
            use_entity_cache=True,
            entity_type="creaturetypes",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_creature_sets(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get creature sets from Open5e API v2.

        Creature sets are collections of creatures (e.g., SRD, Monster Manual).

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of creature set dictionaries
        """
        result = await self.make_request(
            "/creaturesets/",
            use_entity_cache=True,
            entity_type="creaturesets",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.8: Reference data methods (30-day TTL for all)
    async def get_damage_types_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get damage type definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of damage type dictionaries
        """
        result = await self.make_request(
            "/damagetypes/",
            use_entity_cache=True,
            entity_type="damagetypes",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_languages_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get language definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of language dictionaries
        """
        result = await self.make_request(
            "/languages/",
            use_entity_cache=True,
            entity_type="languages",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_alignments_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get alignment definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of alignment dictionaries
        """
        result = await self.make_request(
            "/alignments/",
            use_entity_cache=True,
            entity_type="alignments",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_spell_schools_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get spell school definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of spell school dictionaries
        """
        result = await self.make_request(
            "/spellschools/",
            use_entity_cache=True,
            entity_type="spellschools",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_sizes(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get creature size definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of size dictionaries
        """
        result = await self.make_request(
            "/sizes/",
            use_entity_cache=True,
            entity_type="sizes",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_item_rarities(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get item rarity level definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of rarity dictionaries
        """
        result = await self.make_request(
            "/itemrarities/",
            use_entity_cache=True,
            entity_type="itemrarities",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_environments(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get encounter environment definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of environment dictionaries
        """
        result = await self.make_request(
            "/environments/",
            use_entity_cache=True,
            entity_type="environments",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_abilities(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get ability score definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of ability dictionaries
        """
        result = await self.make_request(
            "/abilities/",
            use_entity_cache=True,
            entity_type="abilities",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_skills_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get skill definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of skill dictionaries
        """
        result = await self.make_request(
            "/skills/",
            use_entity_cache=True,
            entity_type="skills",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.9: Character option methods (7-day TTL)
    async def get_species(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character species/races from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of species dictionaries
        """
        result = await self.make_request(
            "/species/",
            use_entity_cache=True,
            entity_type="species",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_classes_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character classes from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of class dictionaries
        """
        result = await self.make_request(
            "/classes/",
            use_entity_cache=True,
            entity_type="classes",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.10: Rules and metadata methods
    async def get_rules_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get game rules from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of rule dictionaries
        """
        result = await self.make_request(
            "/rules/",
            use_entity_cache=True,
            entity_type="rules",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_rulesets(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get ruleset definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of ruleset dictionaries
        """
        result = await self.make_request(
            "/rulesets/",
            use_entity_cache=True,
            entity_type="rulesets",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_documents(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get game document definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of document dictionaries
        """
        result = await self.make_request(
            "/documents/",
            use_entity_cache=True,
            entity_type="documents",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_licenses(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get license information from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of license dictionaries
        """
        result = await self.make_request(
            "/licenses/",
            use_entity_cache=True,
            entity_type="licenses",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_publishers(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get publisher information from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of publisher dictionaries
        """
        result = await self.make_request(
            "/publishers/",
            use_entity_cache=True,
            entity_type="publishers",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_game_systems(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get game system information from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of game system dictionaries
        """
        result = await self.make_request(
            "/gamesystems/",
            use_entity_cache=True,
            entity_type="gamesystems",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    # Task 1.11: Additional content methods
    async def get_images(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get image resources from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of image dictionaries
        """
        result = await self.make_request(
            "/images/",
            use_entity_cache=True,
            entity_type="images",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_weapon_properties_v2(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get weapon property definitions from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of weapon property dictionaries
        """
        result = await self.make_request(
            "/weaponproperties/",
            use_entity_cache=True,
            entity_type="weaponproperties",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_services(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get service information from Open5e API v2.

        Args:
            **kwargs: Additional API parameters

        Returns:
            List of service dictionaries
        """
        result = await self.make_request(
            "/services/",
            use_entity_cache=True,
            entity_type="services",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]
