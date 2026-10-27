"""Starter PvE/PvP gear catalog: example weapons, armor, trinkets and sets.

Demonstrates the dual-table item model: every item defines separate PvE and
PvP stat tables, and `catalog_item(id, context)` returns the right one.
"""

from __future__ import annotations

from .effects import BUILT_IN_EFFECTS
from .enums import DamageType, EquipmentSlot, Rarity
from .equipment import (
    ArmorWeight, GearSet, ItemDef, ItemKind, Proc, SetBonus, StatTable,
    WeaponClass,
)
from .stat_framework import SubStatId


def _weapon(
    item_id: str, name: str, weapon_class: WeaponClass, rarity: Rarity,
    level: int, pve_damage: float, pvp_damage: float, speed: float = 1.0,
    pve_stats: dict[str, float] | None = None,
    pvp_stats: dict[str, float] | None = None,
    element: DamageType | None = None, element_damage: float = 0.0,
    proc: Proc | None = None, boss_bonus: float = 0.0,
    pvp_power: float = 0.0, anti_heal: float = 0.0,
) -> ItemDef:
    pve_table = StatTable(
        base_stats=pve_stats or {}, base_damage=pve_damage,
        weapon_speed=speed, element=element, element_damage=element_damage,
        boss_damage_bonus=boss_bonus, procs=[proc] if proc else [],
    )
    pvp_table = StatTable(
        base_stats=pvp_stats or {}, base_damage=pvp_damage,
        weapon_speed=speed, pvp_power=pvp_power, anti_heal=anti_heal,
    )
    return ItemDef(
        id=item_id, name=name, kind=ItemKind.WEAPON,
        slot=EquipmentSlot.MAIN_HAND, rarity=rarity, required_level=level,
        weapon_class=weapon_class, pve=pve_table, pvp=pvp_table,
    )


def _armor(
    item_id: str, name: str, slot: EquipmentSlot, weight: ArmorWeight,
    rarity: Rarity, level: int, armor: float, magic_resist: float,
    hp: float = 0.0, pve_stats: dict[str, float] | None = None,
    pvp_stats: dict[str, float] | None = None, set_id: str | None = None,
) -> ItemDef:
    return ItemDef(
        id=item_id, name=name, kind=ItemKind.ARMOR, slot=slot,
        rarity=rarity, required_level=level, armor_weight=weight, set_id=set_id,
        pve=StatTable(armor=armor, magic_resist=magic_resist, max_hp=hp,
                      base_stats=pve_stats or {}),
        pvp=StatTable(armor=armor * 0.6, magic_resist=magic_resist * 0.6,
                      max_hp=hp * 0.5, base_stats=pvp_stats or {}),
    )


def _trinket(
    item_id: str, name: str, slot: EquipmentSlot, rarity: Rarity, level: int,
    pve_stats: dict[str, float] | None = None,
    pvp_stats: dict[str, float] | None = None, proc: Proc | None = None,
) -> ItemDef:
    return ItemDef(
        id=item_id, name=name, kind=ItemKind.TRINKET, slot=slot,
        rarity=rarity, required_level=level,
        pve=StatTable(base_stats=pve_stats or {}, procs=[proc] if proc else []),
        pvp=StatTable(base_stats=pvp_stats or {}),
    )


# --------------------------------------------------------------------------- #
# Weapons — same family, different PvE / PvP tables                            #
# --------------------------------------------------------------------------- #

ASHEN_BLADE = _weapon(
    "ashen_blade", "Ashen Blade", WeaponClass.LONGSWORD, Rarity.EPIC, 60,
    pve_damage=1200, pvp_damage=650, speed=1.1,
    pve_stats={SubStatId.PHYSICAL_POWER.value: 200,
               SubStatId.CRIT_CHANCE.value: 0.05},
    pvp_stats={SubStatId.PHYSICAL_POWER.value: 100,
               SubStatId.TENACITY.value: 50},
    element=DamageType.FIRE, element_damage=150,
    proc=Proc("ashen_burn", "burn", chance=0.25, internal_cooldown=10.0,
              dps_equivalent=300),
    boss_bonus=0.10, pvp_power=100, anti_heal=0.20,
)

STORMBRINGER = _weapon(
    "stormbringer", "Stormbringer", WeaponClass.GREATSWORD, Rarity.LEGENDARY, 70,
    pve_damage=1500, pvp_damage=780, speed=0.9,
    pve_stats={SubStatId.PHYSICAL_POWER.value: 260,
               SubStatId.CRIT_DAMAGE.value: 0.30},
    pvp_stats={SubStatId.PHYSICAL_POWER.value: 120,
               SubStatId.ACCURACY.value: 40},
    element=DamageType.NATURE, element_damage=200,
    proc=Proc("chain_shock", "burn", chance=0.15, internal_cooldown=12.0,
              dps_equivalent=450),
    boss_bonus=0.15, pvp_power=130,
)

NIGHTPIERCER = _weapon(
    "nightpiercer", "Nightpiercer", WeaponClass.DAGGER, Rarity.RARE, 50,
    pve_damage=700, pvp_damage=420, speed=1.8,
    pve_stats={SubStatId.CRIT_CHANCE.value: 0.08,
               SubStatId.ATTACK_SPEED.value: 0.10},
    pvp_stats={SubStatId.CRIT_CHANCE.value: 0.03,
               SubStatId.EVASION.value: 0.02},
    proc=Proc("venom", "poison", chance=0.35, internal_cooldown=6.0,
              dps_equivalent=180),
    pvp_power=60,
)

WORLDBREAKER = _weapon(
    "worldbreaker", "Worldbreaker", WeaponClass.SCYTHE, Rarity.MYTHIC, 80,
    pve_damage=2100, pvp_damage=0, speed=0.8,  # mythic: PvP-disabled
    pve_stats={SubStatId.PHYSICAL_POWER.value: 350,
               SubStatId.LIFE_STEAL.value: 0.05,
               SubStatId.CRIT_DAMAGE.value: 0.40},
    pvp_stats={},
    element=DamageType.SHADOW, element_damage=300,
    proc=Proc("soul_drain", "bleed", chance=0.30, internal_cooldown=8.0,
              dps_equivalent=600),
    boss_bonus=0.20,
)

# --------------------------------------------------------------------------- #
# Armor                                                                        #
# --------------------------------------------------------------------------- #

FLAME_HELM = _armor(
    "flame_helm", "Flame Guard Helm", EquipmentSlot.HEAD, ArmorWeight.HEAVY,
    Rarity.EPIC, 60, armor=450, magic_resist=180, hp=800,
    pve_stats={SubStatId.DAMAGE_REDUCTION.value: 0.02},
    pvp_stats={SubStatId.TENACITY.value: 60},
    set_id="flame",
)
FLAME_CHEST = _armor(
    "flame_chest", "Flame Guard Breastplate", EquipmentSlot.CHEST,
    ArmorWeight.HEAVY, Rarity.EPIC, 60, armor=900, magic_resist=350, hp=1500,
    pve_stats={SubStatId.BLOCK_CHANCE.value: 0.05},
    pvp_stats={SubStatId.TENACITY.value: 120,
               SubStatId.DAMAGE_REDUCTION.value: 0.03},
    set_id="flame",
)
FLAME_LEGS = _armor(
    "flame_legs", "Flame Guard Greaves", EquipmentSlot.LEGS,
    ArmorWeight.HEAVY, Rarity.EPIC, 60, armor=700, magic_resist=260, hp=1100,
    pve_stats={SubStatId.POISE.value: 40},
    pvp_stats={SubStatId.TENACITY.value: 90},
    set_id="flame",
)

SHADOW_WEAVE_HOOD = _armor(
    "shadow_hood", "Shadowweave Hood", EquipmentSlot.HEAD,
    ArmorWeight.LIGHT, Rarity.RARE, 50, armor=120, magic_resist=300, hp=400,
    pve_stats={SubStatId.SPELL_POWER.value: 60, SubStatId.CDR.value: 0.03},
    pvp_stats={SubStatId.CAST_SPEED.value: 0.05},
)
SHADOW_WEAVE_ROBE = _armor(
    "shadow_robe", "Shadowweave Robe", EquipmentSlot.CHEST, ArmorWeight.LIGHT,
    Rarity.RARE, 50, armor=200, magic_resist=550, hp=650,
    pve_stats={SubStatId.SPELL_POWER.value: 110, SubStatId.MP_REGEN.value: 8},
    pvp_stats={SubStatId.MAGIC_RESIST.value: 100},
)

# --------------------------------------------------------------------------- #
# Trinkets: PvE procs vs PvP utility                                           #
# --------------------------------------------------------------------------- #

EMBER_HEART = _trinket(
    "ember_heart", "Ember Heart", EquipmentSlot.TRINKET_1, Rarity.EPIC, 60,
    pve_stats={SubStatId.SPELL_POWER.value: 120},
    pvp_stats={SubStatId.TENACITY.value: 40},
    proc=Proc("inferno", "burn", chance=0.20, internal_cooldown=45.0,
              dps_equivalent=800),
)
SENTINEL_CHARM = _trinket(
    "sentinel_charm", "Sentinel's Charm", EquipmentSlot.TRINKET_1,
    Rarity.EPIC, 60,
    pve_stats={SubStatId.SHIELD_POWER.value: 400},
    pvp_stats={SubStatId.DAMAGE_REDUCTION.value: 0.04,
               SubStatId.TENACITY.value: 80},  # mandatory PvP defensive option
)
CC_BREAK_TRINKET = _trinket(
    "liberation_talisman", "Liberation Talisman",
    EquipmentSlot.TRINKET_2, Rarity.RARE, 40,
    pve_stats={},
    pvp_stats={SubStatId.TENACITY.value: 150},  # CC-break trinket slot
)

# --------------------------------------------------------------------------- #
# Gear sets                                                                    #
# --------------------------------------------------------------------------- #

FLAME_GUARD_SET = GearSet(
    "flame", "Flame Guard",
    bonuses=[
        SetBonus("flame", 2, stats={SubStatId.ARMOR.value: 200}),
        SetBonus("flame", 4, stats={SubStatId.DAMAGE_REDUCTION.value: 0.05,
                                    SubStatId.POISE.value: 100}),
        SetBonus("flame", 6, stats={SubStatId.DAMAGE_REDUCTION.value: 0.10},
                 effect_id="fortified"),
    ],
)

# --------------------------------------------------------------------------- #
# Catalog registry                                                             #
# --------------------------------------------------------------------------- #

CATALOG: dict[str, ItemDef] = {
    item.id: item
    for item in (
        ASHEN_BLADE, STORMBRINGER, NIGHTPIERCER, WORLDBREAKER,
        FLAME_HELM, FLAME_CHEST, FLAME_LEGS,
        SHADOW_WEAVE_HOOD, SHADOW_WEAVE_ROBE,
        EMBER_HEART, SENTINEL_CHARM, CC_BREAK_TRINKET,
    )
}

GEAR_SETS: dict[str, GearSet] = {"flame": FLAME_GUARD_SET}


def catalog_item(item_id: str) -> ItemDef:
    return CATALOG[item_id]
