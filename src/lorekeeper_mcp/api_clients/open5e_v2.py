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
        name: str | None = None,
        **kwargs: Any,
    ) -> list[Spell]:
        """Get spells from Open5e API v2.

        Args:
            level: Filter by spell level
            school: Filter by spell school (server-side filtering via school__key)
            name: Filter by spell name (server-side filtering via name__icontains)
            **kwargs: Additional API parameters

        Returns:
            List of Spell models
        """
        params: dict[str, Any] = {}

        if level is not None:
            params["level"] = level

        # Use server-side school__key parameter for filtering
        if school:
            params["school__key"] = school.lower()

        # Use server-side name__icontains parameter for partial name matching
        if name:
            params["name__icontains"] = name

        # Add any additional parameters
        params.update(kwargs)

        result = await self.make_request(
            "/spells/",
            params=params,
        )

        spell_dicts: list[dict[str, Any]] = (
            result if isinstance(result, list) else result.get("results", [])
        )

        return [Spell.model_validate(spell) for spell in spell_dicts]

    async def get_weapons(self, name: str | None = None, **kwargs: Any) -> list[Weapon]:
        """Get weapons from Open5e API v2.

        Args:
            name: Filter by weapon name (server-side filtering via name__icontains)
            **kwargs: Additional API parameters

        Returns:
            List of Weapon models
        """
        params: dict[str, Any] = {}

        # Use server-side name__icontains parameter for partial name matching
        if name:
            params["name__icontains"] = name

        # Add any additional parameters
        params.update(kwargs)

        result = await self.make_request(
            "/weapons/",
            params=params,
        )

        weapon_dicts: list[dict[str, Any]] = (
            result if isinstance(result, list) else result.get("results", [])
        )

        return [Weapon.model_validate(weapon) for weapon in weapon_dicts]

    async def get_armor(self, name: str | None = None, **kwargs: Any) -> list[Armor]:
        """Get armor from Open5e API v2.

        Args:
            name: Filter by armor name (server-side filtering via name__icontains)
            **kwargs: Additional API parameters

        Returns:
            List of Armor models
        """
        params: dict[str, Any] = {}

        # Use server-side name__icontains parameter for partial name matching
        if name:
            params["name__icontains"] = name

        # Add any additional parameters
        params.update(kwargs)

        result = await self.make_request(
            "/armor/",
            params=params,
        )

        armor_dicts: list[dict[str, Any]] = (
            result if isinstance(result, list) else result.get("results", [])
        )

        return [Armor.model_validate(armor) for armor in armor_dicts]

    async def get_backgrounds(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character backgrounds."""
        result = await self.make_request(
            "/backgrounds/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_feats(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get character feats."""
        result = await self.make_request(
            "/feats/",
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]

    async def get_conditions(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Get game conditions."""
        result = await self.make_request(
            "/conditions/",
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
            params=kwargs,
        )

        if isinstance(result, list):
            return result

        return result.get("results", [])  # type: ignore[no-any-return]
