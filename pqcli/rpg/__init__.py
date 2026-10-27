"""RPG/MMORPG domain framework for pqcli.

The modules in this package are deliberately independent of the legacy
Progress Quest simulation so they can be adopted incrementally.
"""

from .character import Character
from .combat import CombatEngine, CombatResult
from .effects import EffectDef, EffectHost
from .enemies import BossData, Enemy, EnemyRank, EnemyTier, spawn_enemy
from .enums import ClassId, RaceId
from .equipment import EquipmentManager, ItemDef, ItemKind
from .stat_framework import (
    CoreAttribute, ResourceBars, ResourceId, Resistances, StatBlock,
    SubAttributes, SubStatCategory, SubStatId, damage_taken, hit_chance,
    mitigation, power_units,
)
from .stats import Attributes, CombatStats, ResourcePool

__all__ = [
    "Attributes", "BossData", "Character", "ClassId", "CombatEngine",
    "CombatResult", "CombatStats", "CoreAttribute", "EffectDef",
    "EffectHost", "Enemy", "EnemyRank", "EnemyTier", "EquipmentManager",
    "Inventory", "Item", "ItemDef", "ItemKind", "RaceId", "Resistances",
    "ResourceBars", "ResourceId", "ResourcePool", "StatBlock",
    "SubAttributes", "SubStatCategory", "SubStatId", "damage_taken",
    "hit_chance", "mitigation", "power_units", "spawn_enemy",
]
