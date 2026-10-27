"""MMORPG stat framework: attributes, sub-attributes, combat stats, formulas.

Implements the layered stat model used by AAA RPGs and MMOs:

    Core Attributes -> Sub-Attributes -> Combat Stats -> Resources

All values are computed from core attributes + gear + modifiers (PU = Power
Units):

    StatValuePU = RawStat * StatWeight * ScalingCurve
    Mitigation  = Armor / (Armor + K * AttackerLevel)
    DamageTaken = RawDamage * (1 - Mitigation) * (1 - Resist%)
    BossHP      = BaseHP * (1 + LevelDiff * 0.18) * PartyMult * TierMult
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import StrEnum

from .enums import DamageType
from .stats import Attributes

# ============================================================================ #
# 1. Core Attributes (Primary)                                                 #
# ============================================================================ #


class CoreAttribute(StrEnum):
    """Primary stats: permanent character growth; affects everything else."""

    STR = "str"  # physical power, melee damage, carry weight
    DEX = "dex"  # speed, accuracy, crit chance, evasion
    CON = "con"  # health, stamina, resistances
    INT = "int"  # spell power, mana, magic scaling
    WIS = "wis"  # healing, mana regen, status resistance
    VIT = "vit"  # max HP, survivability
    SPI = "spi"  # resource regen, aura strength
    LCK = "lck"  # drop rate, crit variance, proc chance
    WIL = "wil"  # crowd-control resistance, resolve
    CHA = "cha"  # NPC reactions, threat control, leadership


CORE_ATTRIBUTE_IDS: frozenset[str] = frozenset(
    e.value for e in CoreAttribute
)


# ============================================================================ #
# 2. Sub-Attributes (Secondary)                                                #
# ============================================================================ #


class SubStatCategory(StrEnum):
    PHYSICAL = "physical"
    MAGICAL = "magical"
    SURVIVAL = "survival"
    TEMPO = "tempo"
    META = "meta"


class SubStatId(StrEnum):
    """Sub-attributes derived from core attributes + gear + passives."""

    # Physical
    PHYSICAL_POWER = "physical_power"
    ACCURACY = "accuracy"
    ARMOR_PEN = "armor_pen"
    ATTACK_SPEED = "attack_speed"
    CRIT_CHANCE = "crit_chance"
    CRIT_DAMAGE = "crit_damage"
    EVASION = "evasion"
    BLOCK_CHANCE = "block_chance"
    PARRY_CHANCE = "parry_chance"
    STAGGER_DAMAGE = "stagger_damage"
    # Magical
    SPELL_POWER = "spell_power"
    CAST_SPEED = "cast_speed"
    MAGIC_PEN = "magic_pen"
    ELEMENTAL_MASTERY = "elemental_mastery"
    HEALING_POWER = "healing_power"
    CONTROL_POWER = "control_power"
    MANA_EFFICIENCY = "mana_efficiency"
    OVERCHARGE = "overcharge"
    # Survival
    ARMOR = "armor"
    MAGIC_RESIST = "magic_resist"
    DAMAGE_REDUCTION = "damage_reduction"
    SHIELD_POWER = "shield_power"
    HP_REGEN = "hp_regen"
    MP_REGEN = "mp_regen"
    SHIELD_REGEN = "shield_regend"
    TENACITY = "tenacity"
    POISE = "poise"
    # Tempo / flow
    MOVE_SPEED = "move_speed"
    CDR = "cdr"
    GCD = "gcd"
    TURN_PRIORITY = "turn_priority"
    # Meta / economy
    LIFE_STEAL = "life_steal"
    THREAT = "threat"
    GEAR_SCORE = "gear_score"


SUB_STAT_IDS: frozenset[str] = frozenset(e.value for e in SubStatId)

SUB_STAT_CATEGORIES: dict[SubStatId, SubStatCategory] = {
    SubStatId.PHYSICAL_POWER: SubStatCategory.PHYSICAL,
    SubStatId.ACCURACY: SubStatCategory.PHYSICAL,
    SubStatId.ARMOR_PEN: SubStatCategory.PHYSICAL,
    SubStatId.ATTACK_SPEED: SubStatCategory.PHYSICAL,
    SubStatId.CRIT_CHANCE: SubStatCategory.PHYSICAL,
    SubStatId.CRIT_DAMAGE: SubStatCategory.PHYSICAL,
    SubStatId.EVASION: SubStatCategory.PHYSICAL,
    SubStatId.BLOCK_CHANCE: SubStatCategory.PHYSICAL,
    SubStatId.PARRY_CHANCE: SubStatCategory.PHYSICAL,
    SubStatId.STAGGER_DAMAGE: SubStatCategory.PHYSICAL,
    SubStatId.SPELL_POWER: SubStatCategory.MAGICAL,
    SubStatId.CAST_SPEED: SubStatCategory.MAGICAL,
    SubStatId.MAGIC_PEN: SubStatCategory.MAGICAL,
    SubStatId.ELEMENTAL_MASTERY: SubStatCategory.MAGICAL,
    SubStatId.HEALING_POWER: SubStatCategory.MAGICAL,
    SubStatId.CONTROL_POWER: SubStatCategory.MAGICAL,
    SubStatId.MANA_EFFICIENCY: SubStatCategory.MAGICAL,
    SubStatId.OVERCHARGE: SubStatCategory.MAGICAL,
    SubStatId.ARMOR: SubStatCategory.SURVIVAL,
    SubStatId.MAGIC_RESIST: SubStatCategory.SURVIVAL,
    SubStatId.DAMAGE_REDUCTION: SubStatCategory.SURVIVAL,
    SubStatId.SHIELD_POWER: SubStatCategory.SURVIVAL,
    SubStatId.HP_REGEN: SubStatCategory.SURVIVAL,
    SubStatId.MP_REGEN: SubStatCategory.SURVIVAL,
    SubStatId.SHIELD_REGEN: SubStatCategory.SURVIVAL,
    SubStatId.TENACITY: SubStatCategory.SURVIVAL,
    SubStatId.POISE: SubStatCategory.SURVIVAL,
    SubStatId.MOVE_SPEED: SubStatCategory.TEMPO,
    SubStatId.CDR: SubStatCategory.TEMPO,
    SubStatId.GCD: SubStatCategory.TEMPO,
    SubStatId.TURN_PRIORITY: SubStatCategory.TEMPO,
    SubStatId.LIFE_STEAL: SubStatCategory.META,
    SubStatId.THREAT: SubStatCategory.META,
    SubStatId.GEAR_SCORE: SubStatCategory.META,
}

# Stat weights for the Power Unit valuation formula (section 2 of the spec).
STAT_WEIGHTS: dict[str, float] = {
    "strength": 1.00, "dexterity": 1.00, "intelligence": 1.00,
    "vitality": 0.85, "constitution": 0.85, "wisdom": 0.85, "spirit": 0.85,
    "luck": 0.90, "willpower": 0.90, "charisma": 0.70,
    SubStatId.CRIT_CHANCE: 2.50,
    SubStatId.CRIT_DAMAGE: 1.75,
    SubStatId.ATTACK_SPEED: 2.00,
    SubStatId.CDR: 2.25,
    SubStatId.ARMOR: 0.75,
    SubStatId.MAGIC_RESIST: 0.75,
    SubStatId.TENACITY: 3.00,  # PvP Resilience
}


# ============================================================================ #
# 3. Hard caps and safety limits (section 12 of the spec)                      #
# ============================================================================ #


@dataclass(frozen=True)
class Cap:
    """Hard cap with separate PvE / PvP ceilings."""

    pve: float
    pvp: float

    def for_context(self, pvp: bool) -> float:
        return self.pvp if pvp else self.pve


HARD_CAPS: dict[str, Cap] = {
    SubStatId.CRIT_CHANCE: Cap(pve=0.70, pvp=0.40),
    SubStatId.CDR: Cap(pve=0.60, pvp=0.35),
    SubStatId.DAMAGE_REDUCTION: Cap(pve=0.70, pvp=0.70),
    SubStatId.HEALING_POWER: Cap(pve=999.0, pvp=0.50),  # PvP healing bonus cap
    SubStatId.EVASION: Cap(pve=0.60, pvp=0.40),
    SubStatId.BLOCK_CHANCE: Cap(pve=0.75, pvp=0.60),
}

# PvE vs PvP stat conversion multipliers (section 7 of the spec).
PVP_MULTIPLIERS: dict[str, float] = {
    SubStatId.PHYSICAL_POWER: 0.70,
    SubStatId.SPELL_POWER: 0.70,
    SubStatId.CRIT_CHANCE: 0.50,
    SubStatId.CRIT_DAMAGE: 0.60,
    SubStatId.HEALING_POWER: 0.65,
    SubStatId.CDR: 0.50,
    SubStatId.ARMOR: 1.10,
    SubStatId.MAGIC_RESIST: 1.10,
    SubStatId.TENACITY: 1.00,
}


# ============================================================================ #
# 4. Scaling curves (anti-overflow protection)                                 #
# ============================================================================ #


def linear_curve(raw: float) -> float:
    """Early-game linear scaling."""
    return raw


def soft_cap_curve(raw: float, soft_cap: float) -> float:
    """Soft-cap curve: effective = raw / (raw + softcap) * softcap."""
    if raw <= 0:
        return 0.0
    return raw / (raw + soft_cap) * soft_cap


def diminishing_curve(raw: float, cap: float, k: float) -> float:
    """Diminishing returns: cap * (1 - e^(-raw / k))."""
    if raw <= 0:
        return 0.0
    return cap * (1.0 - math.exp(-raw / k))


CURVES: dict[str, Callable[[float], float]] = {
    "linear": linear_curve,
}


# ============================================================================ #
# 5. Derived sub-attribute computation                                         #
# ============================================================================ #

# Derived formulas: base value + per-point contribution from core attributes.
_DERIVED_FORMULAS: dict[SubStatId, tuple[float, dict[str, float]]] = {
    SubStatId.PHYSICAL_POWER: (0.0, {"strength": 2.5}),
    SubStatId.SPELL_POWER: (0.0, {"intelligence": 2.5}),
    SubStatId.HEALING_POWER: (0.0, {"wisdom": 2.0, "spirit": 1.0}),
    SubStatId.ACCURACY: (50.0, {"dexterity": 2.0}),
    SubStatId.EVASION: (0.05, {"dexterity": 0.002}),
    SubStatId.CRIT_CHANCE: (0.05, {"dexterity": 0.0004, "luck": 0.0002}),
    SubStatId.CRIT_DAMAGE: (1.5, {"dexterity": 0.001, "luck": 0.0005}),
    SubStatId.ARMOR: (0.0, {"constitution": 1.5}),
    SubStatId.MAGIC_RESIST: (0.0, {"willpower": 1.2, "spirit": 0.5}),
    SubStatId.HP_REGEN: (0.5, {"constitution": 0.05, "spirit": 0.03}),
    SubStatId.MP_REGEN: (1.0, {"wisdom": 0.08, "spirit": 0.06}),
    SubStatId.TENACITY: (0.0, {"willpower": 1.5, "constitution": 0.5}),
    SubStatId.POISE: (10.0, {"constitution": 2.0, "strength": 1.0}),
    SubStatId.ATTACK_SPEED: (1.0, {"dexterity": 0.003}),
    SubStatId.CAST_SPEED: (1.0, {"intelligence": 0.002, "spirit": 0.002}),
    SubStatId.CDR: (0.0, {"intelligence": 0.0005, "spirit": 0.0003}),
    SubStatId.MOVE_SPEED: (1.0, {"dexterity": 0.002}),
    SubStatId.THREAT: (1.0, {"charisma": 0.01}),
    SubStatId.CONTROL_POWER: (0.0, {"willpower": 1.0, "intelligence": 0.5}),
    SubStatId.LIFE_STEAL: (0.0, {"luck": 0.0005}),
}


@dataclass
class SubAttributes:
    """Full sub-attribute block: base + gear + modifiers, capped per context."""

    values: dict[str, float] = field(default_factory=dict)
    pvp: bool = False

    @classmethod
    def from_attributes(
        cls, attributes: Attributes, gear: dict[str, float] | None = None,
        pvp: bool = False,
    ) -> SubAttributes:
        raw = {e.value: 0.0 for e in SubStatId}
        attr_dict = attributes.as_dict()
        for stat_id, (base, coefs) in _DERIVED_FORMULAS.items():
            value = base + sum(
                attr_dict.get(attr, 0) * coef for attr, coef in coefs.items()
            )
            raw[stat_id.value] = value
        if gear:
            for stat_id, amount in gear.items():
                if stat_id in raw:
                    raw[stat_id] += amount
        self = cls(values=raw, pvp=pvp)
        self.apply_pvp_scaling()
        self.clamp()
        return self

    def apply_pvp_scaling(self) -> None:
        if not self.pvp:
            return
        for stat_id, mult in PVP_MULTIPLIERS.items():
            key = stat_id.value
            if key in self.values:
                self.values[key] *= mult

    def clamp(self) -> None:
        for stat_id, cap in HARD_CAPS.items():
            key = stat_id.value
            if key in self.values:
                self.values[key] = min(self.values[key], cap.for_context(self.pvp))

    def get(self, stat_id: SubStatId | str) -> float:
        return self.values.get(str(getattr(stat_id, "value", stat_id)), 0.0)

    def add(self, stat_id: SubStatId | str, amount: float) -> None:
        key = str(getattr(stat_id, "value", stat_id))
        self.values[key] = self.values.get(key, 0.0) + amount
        self.clamp()


# ============================================================================ #
# 6. Combat formulas (section 13 of the spec)                                  #
# ============================================================================ #


def hit_chance(accuracy: float, evasion: float) -> float:
    """HitChance = clamp(A / (A + E), 0.05, 0.95)."""
    if accuracy + evasion <= 0:
        return 0.5
    return min(0.95, max(0.05, accuracy / (accuracy + evasion)))


def mitigation(armor: float, attacker_level: float, k: float = 75.0) -> float:
    """Mitigation = Armor / (Armor + K * AttackerLevel)."""
    denom = armor + k * max(1.0, attacker_level)
    return min(0.85, max(0.0, armor / denom)) if denom > 0 else 0.0


def damage_taken(
    raw_damage: float,
    armor: float,
    resist_pct: float,
    attacker_level: float,
    vulnerability_pct: float = 0.0,
    k: float = 75.0,
) -> float:
    """DamageTaken = Raw * (1 - Mitigation) * (1 - Resist%) * Vulnerability."""
    after_armor = raw_damage * (1.0 - mitigation(armor, attacker_level, k))
    after_resist = after_armor * (1.0 - min(1.0, max(0.0, resist_pct)))
    return max(0.0, after_resist * (1.0 + vulnerability_pct))


def crit_multiplier(crit_damage_bonus: float) -> float:
    """CritMultiplier = 1 + CritDamage%."""
    return 1.0 + max(0.0, crit_damage_bonus)


def power_units(stats: dict[str, float]) -> float:
    """Item/Gear Power = sum(StatValuePU) = sum(raw * weight * curve)."""
    total = 0.0
    for stat_id, raw in stats.items():
        weight = STAT_WEIGHTS.get(stat_id, 1.0)
        curve = CURVES.get(stat_id, linear_curve)
        total += raw * weight * curve(raw)
    return total


def proc_value(dps: float, uptime: float, impact_weight: float = 1.0) -> float:
    """ProcValue = EffectMagnitude * Uptime * ImpactWeight."""
    return dps * uptime * impact_weight


# ============================================================================ #
# 7. Resources (multi-bar, MMO-ready)                                          #
# ============================================================================ #


class ResourceId(StrEnum):
    HP = "hp"
    MP = "mp"
    STAMINA = "stamina"
    ENERGY = "energy"
    RAGE = "rage"
    FOCUS = "focus"
    FAITH = "faith"
    AETHER = "aether"
    HEAT = "heat"
    SANITY = "sanity"


@dataclass
class ResourceBars:
    """Multi-resource pools with per-resource maxima."""

    maxima: dict[str, float] = field(default_factory=dict)
    current: dict[str, float] = field(default_factory=dict)

    def set_max(self, resource: ResourceId | str, maximum: float) -> None:
        key = str(getattr(resource, "value", resource))
        self.maxima[key] = max(0.0, maximum)
        self.current[key] = min(self.current.get(key, maximum), maximum)

    def spend(self, resource: ResourceId | str, amount: float) -> bool:
        key = str(getattr(resource, "value", resource))
        if self.current.get(key, 0.0) < amount:
            return False
        self.current[key] -= amount
        return True

    def drain(self, resource: ResourceId | str, amount: float) -> float:
        """Remove up to `amount` (damage); never blocks. Returns amount removed."""
        key = str(getattr(resource, "value", resource))
        removed = min(self.current.get(key, 0.0), max(0.0, amount))
        self.current[key] = self.current.get(key, 0.0) - removed
        return removed

    def restore(self, resource: ResourceId | str, amount: float) -> None:
        key = str(getattr(resource, "value", resource))
        self.current[key] = min(
            self.current.get(key, 0.0) + amount, self.maxima.get(key, amount)
        )

    def get(self, resource: ResourceId | str) -> float:
        return self.current.get(str(getattr(resource, "value", resource)), 0.0)

    # -- Legacy compatibility (ResourcePool-style attribute access) ---------- #

    @property
    def hp(self) -> float:
        return self.current.get(ResourceId.HP.value, 0.0)

    @hp.setter
    def hp(self, value: float) -> None:
        self.current[ResourceId.HP.value] = max(0.0, value)

    @property
    def mp(self) -> float:
        return self.current.get(ResourceId.MP.value, 0.0)

    @mp.setter
    def mp(self, value: float) -> None:
        self.current[ResourceId.MP.value] = max(0.0, value)


# ============================================================================ #
# 8. Resistances (4-layer model)                                               #
# ============================================================================ #


@dataclass
class Resistances:
    """Flat resist, % resist, absorption, immunity/vulnerability flags."""

    flat: dict[DamageType, float] = field(default_factory=dict)
    percent: dict[DamageType, float] = field(default_factory=dict)
    absorption: dict[DamageType, float] = field(default_factory=dict)
    immunity: set[DamageType] = field(default_factory=set)
    vulnerability: dict[DamageType, float] = field(default_factory=dict)

    def apply(
        self, raw_damage: float, damage_type: DamageType
    ) -> float:
        """Run raw damage through all four resistance layers."""
        if damage_type in self.immunity:
            return 0.0
        value = max(0.0, raw_damage - self.flat.get(damage_type, 0.0))
        value *= 1.0 - min(1.0, max(0.0, self.percent.get(damage_type, 0.0)))
        absorbed = self.absorption.get(damage_type, 0.0)
        value = max(0.0, value - absorbed)
        value *= 1.0 + self.vulnerability.get(damage_type, 0.0)
        return value


# ============================================================================ #
# 9. Full stat block (players, mobs, bosses)                                   #
# ============================================================================ #


@dataclass
class StatBlock:
    """Unified stat block for a player, mob, elite, or boss.

    Combines core attributes, derived sub-attributes, resistances and
    multi-resource bars into one engine-friendly object.
    """

    attributes: Attributes = field(default_factory=Attributes)
    gear: dict[str, float] = field(default_factory=dict)
    pvp: bool = False
    level: int = 1
    sub: SubAttributes = field(default_factory=SubAttributes)
    resistances: Resistances = field(default_factory=Resistances)
    resources: ResourceBars = field(default_factory=ResourceBars)
    tags: set[str] = field(default_factory=set)

    def combat_proxy(self):
        """Bridge to the legacy CombatStats for the legacy CombatEngine."""
        from .stats import CombatStats
        s = self.sub
        return CombatStats(
            max_hp=int(self.resources.maxima.get(ResourceId.HP.value, 100)),
            attack=int(s.get(SubStatId.PHYSICAL_POWER)),
            spell_power=int(s.get(SubStatId.SPELL_POWER)),
            armor=int(s.get(SubStatId.ARMOR)),
            magic_resist=int(s.get(SubStatId.MAGIC_RESIST)),
            crit_chance=min(0.75, s.get(SubStatId.CRIT_CHANCE)),
            dodge_chance=min(0.50, s.get(SubStatId.EVASION)),
            block_chance=min(0.75, s.get(SubStatId.BLOCK_CHANCE)),
        )

    def recompute(self) -> None:
        """Recompute derived stats from attributes + gear."""
        self.sub = SubAttributes.from_attributes(self.attributes, self.gear, self.pvp)
        max_hp = (
            self.attributes.vitality * 15
            + self.attributes.constitution * 10
            + self.gear.get("max_hp", 0.0)
        )
        max_mp = (
            self.attributes.intelligence * 10
            + self.attributes.spirit * 5
            + self.gear.get("max_mp", 0.0)
        )
        max_stamina = 100 + self.attributes.constitution * 2
        self.resources.set_max(ResourceId.HP, max_hp)
        self.resources.set_max(ResourceId.MP, max_mp)
        self.resources.set_max(ResourceId.STAMINA, max_stamina)
        for resource in (ResourceId.HP, ResourceId.MP, ResourceId.STAMINA):
            if self.resources.get(resource) == 0.0:
                self.resources.restore(resource, self.resources.maxima[resource.value])

    @property
    def gear_score(self) -> float:
        return power_units(self.gear)

    def take_damage(
        self, raw: float, damage_type: DamageType, attacker_level: int = 1
    ) -> float:
        """Apply the full damage pipeline: resistances, then armor mitigation."""
        after_resist = self.resistances.apply(raw, damage_type)
        if damage_type == DamageType.PHYSICAL:
            armor = self.sub.get(SubStatId.ARMOR)
        else:
            armor = self.sub.get(SubStatId.MAGIC_RESIST)
        damage = damage_taken(
            after_resist, armor,
            resist_pct=0.0,  # already applied by resistances
            attacker_level=attacker_level,
            vulnerability_pct=self.resistances.vulnerability.get(damage_type, 0.0),
        )
        if damage_type in self.resistances.immunity:
            damage = 0.0
        self.resources.drain(ResourceId.HP, damage)
        return damage


# ============================================================================ #
# 10. Enemy scaling formulas (section 9 of the spec)                           #
# ============================================================================ #


def boss_hp(
    base_hp: float, level_diff: int, party_size: int, tier_mult: float
) -> float:
    """BossHP = Base * (1 + LevelDiff*0.18) * PartyMult * TierMult."""
    party_mult = 1.0 + (party_size - 1) * 0.65
    return base_hp * (1.0 + level_diff * 0.18) * party_mult * tier_mult


def boss_damage(
    base_damage: float, level_diff: int, tier_mult: float
) -> float:
    """BossDamage = Base * (1 + LevelDiff*0.12) * TierMult.

    Damage scales slower than HP on purpose (anti-one-shot rule).
    """
    return base_damage * (1.0 + level_diff * 0.12) * tier_mult


def encounter_power_budget(
    player_powers: Iterable[float], difficulty_factor: float
) -> float:
    """EncounterPB = sum(PlayerEffectivePower) * DifficultyFactor."""
    return sum(player_powers) * difficulty_factor
