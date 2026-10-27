"""Buff / debuff (status effect) system with stacking, DR, cleanse and immunity.

Implements the effect layer of the stat framework:

    Stack modes : none | refresh | stack | replace_stronger | independent
    Diminishing returns (DR) for CC, especially PvP and bosses
    Cleanse types: physical, magic, curse, poison, bleed, all
    Immunities  : full CC-immune, unstoppable, damage-immune windows
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum

from .stat_framework import SubStatId


class EffectKind(StrEnum):
    BUFF = "buff"
    DEBUFF = "debuff"


class EffectCategory(StrEnum):
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"
    UTILITY = "utility"
    CROWD_CONTROL = "crowd_control"
    DOT = "dot"  # damage over time / debuff ticks
    STAT_BREAK = "stat_break"  # attribute reduction


class StackMode(StrEnum):
    NONE = "none"  # re-application does nothing while active
    REFRESH = "refresh"  # restart duration
    STACK = "stack"  # additive stacks up to max
    REPLACE_STRONGER = "replace_stronger"  # keep stronger magnitude
    INDEPENDENT = "independent"  # parallel instances allowed


class CleanseType(StrEnum):
    PHYSICAL = "physical"
    MAGIC = "magic"
    CURSE = "curse"
    POISON = "poison"
    BLEED = "bleed"
    ALL = "all"


class ImmunityKind(StrEnum):
    NONE = "none"
    CC_IMMUNE = "cc_immune"
    UNSTOPPABLE = "unstoppable"  # CC immune + cannot be interrupted
    DAMAGE_IMMUNE = "damage_immune"


# CC diminishing returns: 1st -> 100%, 2nd -> 50%, 3rd -> 25%, then immune.
CC_DR_STEPS: tuple[float, ...] = (1.0, 0.5, 0.25, 0.0)


@dataclass(frozen=True)
class EffectDef:
    """Static definition of a buff or debuff."""

    id: str
    name: str
    kind: EffectKind
    category: EffectCategory
    duration: float  # seconds
    magnitude: float = 0.0  # flat or fraction, depending on stat
    stat: SubStatId | None = None  # stat modified (buffs/debuffs)
    stat_multiplier: bool = False  # magnitude is a % multiplier when True
    stack_mode: StackMode = StackMode.REFRESH
    max_stacks: int = 1
    tick_interval: float = 0.0  # >0 => periodic (DoT/HoT/regen)
    tick_damage: float = 0.0  # per tick damage (DoT)
    tick_heal: float = 0.0  # per tick heal (HoT/regen)
    dr_category: str | None = None  # CC DR group (e.g. "stun", "root")
    cleanse: CleanseType | None = None  # how it can be removed
    immunity: ImmunityKind = ImmunityKind.NONE


# --------------------------------------------------------------------------- #
# Built-in effect definitions                                                  #
# --------------------------------------------------------------------------- #

BUILT_IN_EFFECTS: dict[str, EffectDef] = {
    # -- Offensive buffs ----------------------------------------------------- #
    "power_surge": EffectDef(
        "power_surge", "Power Surge", EffectKind.BUFF, EffectCategory.OFFENSIVE,
        duration=10.0, magnitude=0.20, stat=SubStatId.PHYSICAL_POWER,
        stat_multiplier=True,
    ),
    "arcane_amplify": EffectDef(
        "arcane_amplify", "Arcane Amplify", EffectKind.BUFF,
        EffectCategory.OFFENSIVE, duration=12.0, magnitude=0.25,
        stat=SubStatId.SPELL_POWER, stat_multiplier=True,
    ),
    "precision": EffectDef(
        "precision", "Precision", EffectKind.BUFF, EffectCategory.OFFENSIVE,
        duration=10.0, magnitude=0.10, stat=SubStatId.CRIT_CHANCE,
    ),
    "berserk": EffectDef(
        "berserk", "Berserk", EffectKind.BUFF, EffectCategory.OFFENSIVE,
        duration=8.0, magnitude=0.30, stat=SubStatId.ATTACK_SPEED,
        stat_multiplier=True,
    ),
    # -- Defensive buffs ----------------------------------------------------- #
    "shielded": EffectDef(
        "shielded", "Shielded", EffectKind.BUFF, EffectCategory.DEFENSIVE,
        duration=12.0, magnitude=100.0, stat=SubStatId.SHIELD_POWER,
    ),
    "fortified": EffectDef(
        "fortified", "Fortified", EffectKind.BUFF, EffectCategory.DEFENSIVE,
        duration=10.0, magnitude=0.15, stat=SubStatId.DAMAGE_REDUCTION,
    ),
    "regeneration": EffectDef(
        "regeneration", "Regeneration", EffectKind.BUFF, EffectCategory.DEFENSIVE,
        duration=10.0, tick_interval=2.0, tick_heal=25.0,
    ),
    "haste": EffectDef(
        "haste", "Haste", EffectKind.BUFF, EffectCategory.UTILITY,
        duration=8.0, magnitude=0.25, stat=SubStatId.ATTACK_SPEED,
        stat_multiplier=True,
    ),
    "stealth": EffectDef(
        "stealth", "Stealth", EffectKind.BUFF, EffectCategory.UTILITY,
        duration=6.0,
    ),
    "unstoppable": EffectDef(
        "unstoppable", "Unstoppable", EffectKind.BUFF, EffectCategory.UTILITY,
        duration=5.0, immunity=ImmunityKind.UNSTOPPABLE,
    ),
    # -- Crowd control debuffs ---------------------------------------------- #
    "stun": EffectDef(
        "stun", "Stun", EffectKind.DEBUFF, EffectCategory.CROWD_CONTROL,
        duration=2.0, dr_category="stun", cleanse=CleanseType.MAGIC,
    ),
    "root": EffectDef(
        "root", "Root", EffectKind.DEBUFF, EffectCategory.CROWD_CONTROL,
        duration=3.0, dr_category="root", cleanse=CleanseType.MAGIC,
    ),
    "silence": EffectDef(
        "silence", "Silence", EffectKind.DEBUFF, EffectCategory.CROWD_CONTROL,
        duration=4.0, dr_category="silence", cleanse=CleanseType.MAGIC,
    ),
    "fear": EffectDef(
        "fear", "Fear", EffectKind.DEBUFF, EffectCategory.CROWD_CONTROL,
        duration=3.0, dr_category="fear", cleanse=CleanseType.CURSE,
    ),
    "freeze": EffectDef(
        "freeze", "Freeze", EffectKind.DEBUFF, EffectCategory.CROWD_CONTROL,
        duration=2.5, dr_category="freeze", cleanse=CleanseType.MAGIC,
    ),
    # -- DoT debuffs --------------------------------------------------------- #
    "burn": EffectDef(
        "burn", "Burn", EffectKind.DEBUFF, EffectCategory.DOT,
        duration=6.0, tick_interval=2.0, tick_damage=30.0, max_stacks=3,
        stack_mode=StackMode.STACK, cleanse=CleanseType.PHYSICAL,
    ),
    "poison": EffectDef(
        "poison", "Poison", EffectKind.DEBUFF, EffectCategory.DOT,
        duration=12.0, tick_interval=3.0, tick_damage=20.0, max_stacks=5,
        stack_mode=StackMode.STACK, cleanse=CleanseType.POISON,
    ),
    "bleed": EffectDef(
        "bleed", "Bleed", EffectKind.DEBUFF, EffectCategory.DOT,
        duration=8.0, tick_interval=1.0, tick_damage=15.0, max_stacks=5,
        stack_mode=StackMode.STACK, cleanse=CleanseType.BLEED,
    ),
    # -- Stat-break debuffs -------------------------------------------------- #
    "weaken": EffectDef(
        "weaken", "Weaken", EffectKind.DEBUFF, EffectCategory.STAT_BREAK,
        duration=10.0, magnitude=-0.25, stat=SubStatId.PHYSICAL_POWER,
        stat_multiplier=True, cleanse=CleanseType.MAGIC,
    ),
    "shatter": EffectDef(
        "shatter", "Shatter", EffectKind.DEBUFF, EffectCategory.STAT_BREAK,
        duration=10.0, magnitude=-0.30, stat=SubStatId.ARMOR,
        stat_multiplier=True, cleanse=CleanseType.MAGIC,
    ),
    "curse": EffectDef(
        "curse", "Curse", EffectKind.DEBUFF, EffectCategory.STAT_BREAK,
        duration=8.0, magnitude=-0.10, stat=SubStatId.DAMAGE_REDUCTION,
        cleanse=CleanseType.CURSE,
    ),
    "slow": EffectDef(
        "slow", "Slow", EffectKind.DEBUFF, EffectCategory.STAT_BREAK,
        duration=6.0, magnitude=-0.40, stat=SubStatId.MOVE_SPEED,
        stat_multiplier=True, cleanse=CleanseType.MAGIC,
    ),
}


# --------------------------------------------------------------------------- #
# Active effect instances                                                      #
# --------------------------------------------------------------------------- #


@dataclass
class ActiveEffect:
    """One live application of an EffectDef on a target."""

    definition: EffectDef
    remaining: float  # seconds left
    stacks: int = 1
    magnitude: float = 0.0  # effective magnitude (after stacking/DR)
    tick_timer: float = 0.0
    source: str = ""

    @property
    def id(self) -> str:
        return self.definition.id


class EffectHost:
    """Tracks active effects on one entity and resolves their interactions.

    Handles stacking rules, CC diminishing returns, immunities and cleansing.
    """

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.active: list[ActiveEffect] = []
        self._dr_history: dict[str, list[float]] = {}  # dr_category -> timestamps
        self.immunity: ImmunityKind = ImmunityKind.NONE
        self.pending_dot: float = 0.0  # accumulated damage for caller to apply
        self.pending_heal: float = 0.0

    # -- Application --------------------------------------------------------- #

    def apply(
        self, definition: EffectDef, source: str = "", now: float | None = None,
    ) -> bool:
        """Apply an effect; returns False if blocked by immunity/DR."""
        t = time.monotonic() if now is None else now
        if definition.kind == EffectKind.DEBUFF:
            if not self._check_immunity(definition):
                return False
            if definition.dr_category:
                factor = self._dr_factor(definition.dr_category, t)
                if factor <= 0.0:
                    return False
            else:
                factor = 1.0
        else:
            factor = 1.0

        existing = [e for e in self.active if e.id == definition.id]
        magnitude = definition.magnitude * factor

        if existing and definition.stack_mode != StackMode.INDEPENDENT:
            effect = existing[0]
            if definition.stack_mode == StackMode.NONE:
                return True  # already active, no change
            if definition.stack_mode == StackMode.REFRESH:
                effect.remaining = definition.duration
                effect.magnitude = max(effect.magnitude, magnitude)
            elif definition.stack_mode == StackMode.STACK:
                effect.stacks = min(
                    effect.stacks + 1, max(1, definition.max_stacks)
                )
                effect.remaining = definition.duration
                effect.magnitude = magnitude
            elif definition.stack_mode == StackMode.REPLACE_STRONGER:
                if abs(magnitude) > abs(effect.magnitude):
                    effect.magnitude = magnitude
                effect.remaining = definition.duration
        else:
            self.active.append(
                ActiveEffect(
                    definition=definition, remaining=definition.duration,
                    magnitude=magnitude, source=source,
                )
            )
        return True

    def _check_immunity(self, definition: EffectDef) -> bool:
        if self.immunity == ImmunityKind.UNSTOPPABLE:
            return False
        if self.immunity == ImmunityKind.CC_IMMUNE:
            return definition.category != EffectCategory.CROWD_CONTROL
        return True

    def _dr_factor(self, category: str, now: float) -> float:
        """Diminishing returns per CC category within a 10s window."""
        window = [t for t in self._dr_history.get(category, []) if now - t <= 10.0]
        self._dr_history[category] = window
        index = min(len(window), len(CC_DR_STEPS) - 1)
        factor = CC_DR_STEPS[index]
        window.append(now)
        return factor

    # -- Stat aggregation ---------------------------------------------------- #

    def stat_modifier(self, stat: SubStatId | str) -> float:
        """Total modifier for a stat from all active effects.

        Flat effects (stat_multiplier=False) sum; multiplier effects combine
        multiplicatively, e.g. two +20% effects give 1.2 * 1.2 = 1.44.
        """
        key = str(getattr(stat, "value", stat))
        flat = 0.0
        multiplicative = 1.0
        for effect in self.active:
            d = effect.definition
            if d.stat is None or str(d.stat.value) != key:
                continue
            total_magnitude = effect.magnitude * effect.stacks
            if d.stat_multiplier:
                multiplicative *= 1.0 + total_magnitude
            else:
                flat += total_magnitude
        return flat if multiplicative == 1.0 else flat + multiplicative - 1.0

    def is_controlled(self, category: EffectCategory = EffectCategory.CROWD_CONTROL) -> bool:
        return any(
            e.definition.category == category for e in self.active
        )

    # -- Ticking / expiry ---------------------------------------------------- #

    def tick(self, dt: float) -> tuple[float, float]:
        """Advance all effects; returns (damage_dealt, healing_done) this tick."""
        self.pending_dot = 0.0
        self.pending_heal = 0.0
        for effect in list(self.active):
            effect.remaining -= dt
            d = effect.definition
            if d.tick_interval > 0:
                effect.tick_timer += dt
                while effect.tick_timer >= d.tick_interval:
                    effect.tick_timer -= d.tick_interval
                    self.pending_dot += d.tick_damage * effect.stacks
                    self.pending_heal += d.tick_heal * effect.stacks
            if effect.remaining <= 0:
                self.active.remove(effect)
        return self.pending_dot, self.pending_heal

    # -- Cleansing ----------------------------------------------------------- #

    def cleanse(self, cleanse_type: CleanseType, debuffs_only: bool = True) -> int:
        """Remove effects cleansable by the given type; returns count removed."""
        removed = 0
        for effect in list(self.active):
            d = effect.definition
            if debuffs_only and d.kind != EffectKind.DEBUFF:
                continue
            if d.cleanse in (cleanse_type, CleanseType.ALL):
                self.active.remove(effect)
                removed += 1
        return removed

    def purge(self) -> None:
        self.active.clear()
