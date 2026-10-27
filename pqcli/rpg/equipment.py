"""PvE vs PvP equipment: weapons, armor, trinkets, gems/enchants, items.

Core design rule: PvE and PvP never use identical scaling even when items
share names. Each item carries separate PvE and PvP stat tables, and a
`context` selects which table feeds the stat framework.

    WeaponPower_PvE = (BaseDmg*Speed + AttributeScaling + ElementalScaling) * PvEMult
    WeaponPower_PvP = (NormalizedDmg + AttrScale*PvPStatScale) * PvPDampening
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .enums import DamageType, EquipmentSlot, Rarity
from .stat_framework import SubStatId, power_units, proc_value


class ItemKind(StrEnum):
    WEAPON = "weapon"
    ARMOR = "armor"
    TRINKET = "trinket"
    CONSUMABLE = "consumable"
    GEM = "gem"
    ENCHANT = "enchant"
    CURRENCY = "currency"
    MATERIAL = "material"
    COSMETIC = "cosmetic"


class WeaponClass(StrEnum):
    # Melee
    GREATSWORD = "greatsword"
    LONGSWORD = "longsword"
    AXE = "axe"
    MACE = "mace"
    SPEAR = "spear"
    DAGGER = "dagger"
    FIST = "fist"
    SCYTHE = "scythe"
    # Ranged
    BOW = "bow"
    CROSSBOW = "crossbow"
    GUN = "gun"
    THROWING = "throwing"
    # Magic / hybrid
    STAFF = "staff"
    WAND = "wand"
    TOME = "tome"
    CATALYST = "catalyst"
    RELIC = "relic"


class ArmorWeight(StrEnum):
    LIGHT = "light"  # casters, stealth
    MEDIUM = "medium"  # rogues, archers
    HEAVY = "heavy"  # tanks, bruisers


@dataclass
class Proc:
    """Chance-based on-hit effect (PvE only; normalized/disabled in PvP)."""

    id: str
    effect_id: str  # EffectDef id in effects.py
    chance: float  # 0..1
    internal_cooldown: float = 0.0  # seconds between procs
    dps_equivalent: float = 0.0  # for PU valuation


@dataclass
class StatTable:
    """Stats for one context (PvE or PvP)."""

    base_stats: dict[str, float] = field(default_factory=dict)  # sub-stats
    attribute_bonuses: dict[str, int] = field(default_factory=dict)
    armor: float = 0.0
    magic_resist: float = 0.0
    max_hp: float = 0.0
    max_mp: float = 0.0
    base_damage: float = 0.0  # weapons
    weapon_speed: float = 1.0  # attacks per second multiplier
    element: DamageType | None = None  # weapons: infused damage type
    element_damage: float = 0.0
    boss_damage_bonus: float = 0.0  # PvE: +% vs bosses
    pvp_power: float = 0.0  # PvP: PvP-only damage stat
    pvp_penetration: float = 0.0
    anti_heal: float = 0.0  # PvP: enemy healing reduction
    procs: list[Proc] = field(default_factory=list)  # ignored in PvP


@dataclass
class ItemDef:
    """Full item definition with separate PvE and PvP tables."""

    id: str
    name: str
    kind: ItemKind
    slot: EquipmentSlot | None = None
    rarity: Rarity = Rarity.COMMON
    required_level: int = 1
    set_id: str | None = None  # gear set this item belongs to
    weapon_class: WeaponClass | None = None
    armor_weight: ArmorWeight | None = None
    pve: StatTable = field(default_factory=StatTable)
    pvp: StatTable = field(default_factory=StatTable)
    bind_on_pickup: bool = False
    stackable: bool = False
    max_stack: int = 1
    heal_amount: float = 0.0  # consumables
    restore_mp: float = 0.0
    description: str = ""

    def table(self, pvp: bool) -> StatTable:
        return self.pvp if pvp else self.pve

    # -- Valuation ----------------------------------------------------------- #

    def item_power(self, pvp: bool) -> float:
        """ItemPower = sum(StatPU) + ProcValue (+ rarity multiplier)."""
        table = self.table(pvp)
        stats: dict[str, float] = dict(table.base_stats)
        stats["armor"] = stats.get("armor", 0.0) + table.armor
        stats[str(SubStatId.MAGIC_RESIST.value)] = (
            stats.get(str(SubStatId.MAGIC_RESIST.value), 0.0) + table.magic_resist
        )
        stats["max_hp"] = stats.get("max_hp", 0.0) + table.max_hp
        total = power_units(stats)
        if not pvp:  # procs are PvE-only
            total += sum(
                proc_value(p.dps_equivalent, uptime=0.25, impact_weight=1.2)
                for p in table.procs
            )
        rarity_mult = {
            Rarity.COMMON: 1.0, Rarity.UNCOMMON: 1.05, Rarity.RARE: 1.15,
            Rarity.EPIC: 1.3, Rarity.LEGENDARY: 1.5, Rarity.MYTHIC: 1.8,
        }[self.rarity]
        return total * rarity_mult


@dataclass
class SetBonus:
    """Set bonus active at N pieces of a named set."""

    set_id: str
    pieces: int
    stats: dict[str, float] = field(default_factory=dict)
    effect_id: str | None = None  # special set effect (PvE sets often alter skills)


@dataclass
class GearSet:
    """A named gear set with tiered bonuses (2pc / 4pc / 6pc)."""

    set_id: str
    name: str
    bonuses: list[SetBonus] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Gear slot aggregation                                                        #
# --------------------------------------------------------------------------- #

STANDARD_SLOTS: tuple[EquipmentSlot, ...] = (
    EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS,
    EquipmentSlot.FEET, EquipmentSlot.HANDS, EquipmentSlot.MAIN_HAND,
    EquipmentSlot.OFF_HAND, EquipmentSlot.NECK, EquipmentSlot.RING_1,
    EquipmentSlot.RING_2, EquipmentSlot.TRINKET_1, EquipmentSlot.TRINKET_2,
)


class EquipmentManager:
    """Aggregates equipped items into one gear table for the stat framework."""

    def __init__(self) -> None:
        self.equipped: dict[EquipmentSlot, ItemDef] = {}
        self.gems: dict[EquipmentSlot, list[ItemDef]] = {}

    def equip(self, item: ItemDef, slot: EquipmentSlot | None = None) -> ItemDef | None:
        """Equip an item; returns the previously equipped item, if any."""
        target = slot or item.slot
        if target is None:
            raise ValueError(f"Item {item.id} has no slot")
        previous = self.equipped.get(target)
        self.equipped[target] = item
        return previous

    def unequip(self, slot: EquipmentSlot) -> ItemDef | None:
        return self.equipped.pop(slot, None)

    def socket(self, slot: EquipmentSlot, gem: ItemDef) -> bool:
        if gem.kind != ItemKind.GEM:
            return False
        self.gems.setdefault(slot, []).append(gem)
        return True

    def gear_table(self, pvp: bool) -> dict[str, float]:
        """Merge all equipped items + gems into a sub-stat delta table."""
        merged: dict[str, float] = {}
        for item in self.equipped.values():
            table = item.table(pvp)
            for stat, value in table.base_stats.items():
                merged[stat] = merged.get(stat, 0.0) + value
            merged["armor"] = merged.get("armor", 0.0) + table.armor
            merged["magic_resist"] = (
                merged.get("magic_resist", 0.0) + table.magic_resist
            )
            merged["max_hp"] = merged.get("max_hp", 0.0) + table.max_hp
            merged["max_mp"] = merged.get("max_mp", 0.0) + table.max_mp
        # Gems apply only while their host item stays equipped
        for slot, gem_list in self.gems.items():
            if slot not in self.equipped:
                continue
            for gem in gem_list:
                table = gem.table(pvp)
                for stat, value in table.base_stats.items():
                    merged[stat] = merged.get(stat, 0.0) + value
        return merged

    def total_power(self, pvp: bool) -> float:
        return sum(item.item_power(pvp) for item in self.equipped.values())

    def set_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.equipped.values():
            set_id = getattr(item, "set_id", None)
            if set_id:
                counts[set_id] = counts.get(set_id, 0) + 1
        return counts

    def active_set_bonuses(self, sets: dict[str, GearSet]) -> list[SetBonus]:
        """Return set bonuses whose piece thresholds are met."""
        counts = self.set_counts()
        active: list[SetBonus] = []
        for set_id, count in counts.items():
            gear_set = sets.get(set_id)
            if not gear_set:
                continue
            for bonus in gear_set.bonuses:
                if count >= bonus.pieces:
                    active.append(bonus)
        return active
