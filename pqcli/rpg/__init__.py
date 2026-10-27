"""RPG/MMORPG domain framework for pqcli.

The modules in this package are deliberately independent of the legacy
Progress Quest simulation so they can be adopted incrementally.
"""

from .character import Character
from .combat import CombatEngine, CombatResult
from .enums import ClassId, RaceId
from .items import Inventory, Item
from .stats import Attributes, CombatStats, ResourcePool

__all__ = [
    "Attributes", "Character", "ClassId", "CombatEngine", "CombatResult",
    "CombatStats", "Inventory", "Item", "RaceId", "ResourcePool",
]
