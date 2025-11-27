"""OrcBrew-specific validation models with relaxed constraints.

OrcBrew files often have incomplete data compared to API responses.
These models share structure with canonical models but define all fields independently
to avoid parent validator side effects.
"""

from lorekeeper_mcp.models.orcbrew.creature import OrcBrewCreature
from lorekeeper_mcp.models.orcbrew.equipment import (
    OrcBrewArmor,
    OrcBrewMagicItem,
    OrcBrewWeapon,
)
from lorekeeper_mcp.models.orcbrew.spell import OrcBrewSpell

__all__ = [
    "OrcBrewArmor",
    "OrcBrewCreature",
    "OrcBrewMagicItem",
    "OrcBrewSpell",
    "OrcBrewWeapon",
]
