"""Enemy ecosystem: mob taxonomy, ranks, AI archetypes, bosses, threat, loot.

Implements the PvE encounter layer on top of the stat framework:

    Trash -> Veteran -> Elite -> Champion -> Dungeon/World/Raid Boss -> Mythic
    Threat = Damage*Mult + Healing*Weight + Flat + TauntOverride
    BossHP = Base * (1 + LevelDiff*0.18) * PartyMult * TierMult
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum

from .effects import EffectDef, EffectHost
from .enums import DamageType
from .stat_framework import StatBlock, boss_damage, boss_hp


class EnemyTier(StrEnum):
    TRASH = "trash"  # 60-80% player baseline, 1-2 skills
    VETERAN = "veteran"  # 120-150% baseline, partial resistances
    ELITE = "elite"  # 200-300% baseline, CC resist, mini-boss
    CHAMPION = "champion"  # 250-400% + affix + aura
    DUNGEON_BOSS = "dungeon_boss"  # small-group mechanics
    WORLD_BOSS = "world_boss"  # open world, massive HP
    RAID_BOSS = "raid_boss"  # 8-40 players, full phase library
    MYTHIC = "mythic"  # endgame modifiers + layered immunities


class EnemyRank(StrEnum):
    """Color-coded rank system with baseline stat modifiers."""

    NORMAL = "normal"  # x1.0, white
    VETERAN = "veteran"  # x1.2, blue
    ELITE = "elite"  # x1.5, yellow
    CHAMPION = "champion"  # x2.0, orange
    BOSS = "boss"  # x3.0, red
    MYTHIC = "mythic"  # x8.0, purple
    ASCENDED = "ascended"  # x15.0, black


RANK_MULTIPLIERS: dict[EnemyRank, float] = {
    EnemyRank.NORMAL: 1.0,
    EnemyRank.VETERAN: 1.2,
    EnemyRank.ELITE: 1.5,
    EnemyRank.CHAMPION: 2.0,
    EnemyRank.BOSS: 3.0,
    EnemyRank.MYTHIC: 8.0,
    EnemyRank.ASCENDED: 15.0,
}


class AIRole(StrEnum):
    BRUTE = "brute"  # slow, high damage
    TANK = "tank"  # holds threat, shields allies
    ASSASSIN = "assassin"  # burst + target swap
    SNIPER = "sniper"  # long range, line checks
    CASTER = "caster"  # AoE, nukes, debuffs
    CONTROLLER = "controller"  # CC, zones
    SUMMONER = "summoner"  # adds, totems
    SUPPORT = "support"  # buffs, cleanses
    TRICKSTER = "trickster"  # teleports, clones


class BossType(StrEnum):
    DUNGEON = "dungeon"
    WORLD = "world"
    RAID = "raid"
    EVENT = "event"
    STORY = "story"
    MYTHIC = "mythic"
    SECRET = "secret"


class DifficultyTier(StrEnum):
    NORMAL = "normal"
    HARD = "hard"
    NIGHTMARE = "nightmare"
    MYTHIC = "mythic"
    ASCENDED = "ascended"
    APOCALYPSE = "apocalypse"


TIER_MULTIPLIERS: dict[DifficultyTier, float] = {
    DifficultyTier.NORMAL: 1.0,
    DifficultyTier.HARD: 1.4,
    DifficultyTier.NIGHTMARE: 2.0,
    DifficultyTier.MYTHIC: 3.0,
    DifficultyTier.ASCENDED: 5.0,
    DifficultyTier.APOCALYPSE: 8.0,
}


class AffixId(StrEnum):
    """Enemy modifiers for elites and mythic dungeons."""

    BERSERK = "berserk"  # damage ramps over time
    VAMPIRIC = "vampiric"  # life steal
    ARCANE_SHIELD = "arcane_shield"
    REFLECTIVE = "reflective"
    TOXIC = "toxic"
    FRENZIED = "frenzied"
    REGENERATING = "regenerating"
    PHASE_SHIFT = "phase_shift"
    TELEPORTING = "teleporting"
    SUMMONER = "summoner"


@dataclass
class Ability:
    """One enemy ability with a cooldown and a utility score for AI."""

    id: str
    name: str
    power: float
    damage_type: DamageType = DamageType.PHYSICAL
    cooldown: float = 6.0
    telegraph: float = 1.0  # seconds of warning; >=1.5 for big hits
    cast_time: float = 0.5
    effect: EffectDef | None = None  # debuff applied on hit
    min_phase: int = 1  # phase gate
    aoe: bool = False


@dataclass
class BossPhase:
    """One phase of a boss encounter, entered via a trigger."""

    index: int
    hp_threshold: float | None = None  # enter when HP <= this fraction
    time_trigger: float | None = None  # enter after N seconds
    event_trigger: str | None = None  # e.g. "3 crystals destroyed"
    abilities: list[Ability] = field(default_factory=list)
    spawns_adds: int = 0
    arena_change: str | None = None
    damage_type_shift: DamageType | None = None
    enrage: bool = False


@dataclass
class LootEntry:
    item_id: str
    chance: float  # 0..1
    min_count: int = 1
    max_count: int = 1
    unique_per_week: bool = False


@dataclass
class LootTable:
    entries: list[LootEntry] = field(default_factory=list)
    currency_min: int = 0
    currency_max: int = 0

    def roll(self, rng: random.Random, luck: float = 0.0) -> list[str]:
        """Roll drops; luck (bounded 0..0.5) boosts each chance."""
        drops: list[str] = []
        luck_bonus = min(0.5, max(0.0, luck))
        for entry in self.entries:
            if rng.random() < min(1.0, entry.chance + luck_bonus):
                count = rng.randint(entry.min_count, entry.max_count)
                drops.extend([entry.item_id] * count)
        return drops


@dataclass
class BossData:
    """Data-driven boss metadata (engine-agnostic)."""

    name: str
    rank: EnemyRank = EnemyRank.BOSS
    boss_type: BossType = BossType.DUNGEON
    level: int = 60
    base_hp: float = 100_000.0
    base_damage: float = 500.0
    phases: list[BossPhase] = field(default_factory=list)
    abilities: list[Ability] = field(default_factory=list)
    immunities: set[DamageType] = field(default_factory=set)
    affixes: set[AffixId] = field(default_factory=set)
    loot: LootTable = field(default_factory=LootTable)
    enrage_timer: float | None = None  # hard enrage at T seconds
    enrage_ramp: float = 0.0  # soft enrage: +% damage per 15s
    ai_role: AIRole = AIRole.BRUTE
    arena_hazards: list[str] = field(default_factory=list)
    cc_resistance: float = 0.5  # CC duration multiplier
    tags: set[str] = field(default_factory=set)  # Undead, Dragon, Titan...

    def scaled_hp(self, party_size: int, tier: DifficultyTier) -> float:
        return boss_hp(
            self.base_hp, level_diff=0, party_size=max(1, party_size),
            tier_mult=TIER_MULTIPLIERS[tier],
        )

    def scaled_damage(self, tier: DifficultyTier) -> float:
        return boss_damage(self.base_damage, level_diff=0, tier_mult=TIER_MULTIPLIERS[tier])


@dataclass
class Enemy:
    """A concrete spawned enemy: taxonomy tier + stats + effects + threat."""

    name: str
    tier: EnemyTier = EnemyTier.TRASH
    rank: EnemyRank = EnemyRank.NORMAL
    level: int = 1
    ai_role: AIRole = AIRole.BRUTE
    stats: StatBlock = field(default_factory=StatBlock)
    effects: EffectHost = field(default_factory=EffectHost)
    abilities: list[Ability] = field(default_factory=list)
    affixes: set[AffixId] = field(default_factory=set)
    loot: LootTable = field(default_factory=LootTable)
    xp_reward: int = 0
    cc_resistance: float = 0.0  # CC duration multiplier (bosses > 0)
    alive: bool = True
    threat_table: dict[str, float] = field(default_factory=dict)
    cooldowns: dict[str, float] = field(default_factory=dict)
    reflected: float = 0.0  # damage returned to attacker (Reflective affix)

    def __post_init__(self) -> None:
        self.stats.recompute()

    @classmethod
    def spawn(
        cls, name: str, tier: EnemyTier, rank: EnemyRank, level: int,
        ai_role: AIRole = AIRole.BRUTE, baseline: float = 1.0,
    ) -> "Enemy":
        """Build an enemy scaled off the player baseline for its tier."""
        rank_mult = RANK_MULTIPLIERS[rank]
        stats = StatBlock(level=level)
        stats.attributes.strength = int(10 * baseline * rank_mult)
        stats.attributes.vitality = int(10 * baseline * rank_mult)
        stats.recompute()
        xp = int(20 * level * rank_mult)
        return cls(
            name=name, tier=tier, rank=rank, level=level, ai_role=ai_role,
            stats=stats, xp_reward=xp,
            cc_resistance=0.5 if tier in (
                EnemyTier.ELITE, EnemyTier.CHAMPION,
            ) else (0.5 if tier.value.endswith("boss") or tier == EnemyTier.MYTHIC else 0.0),
        )

    # -- Threat (MMO aggro core) -------------------------------------------- #

    def add_threat(self, actor: str, damage: float = 0.0, healing: float = 0.0,
                   flat: float = 0.0, taunt: bool = False,
                   threat_mult: float = 1.0) -> None:
        """Threat = Damage*Mult + Healing*Weight + Flat + TauntOverride."""
        threat = damage * threat_mult + healing * 0.5 + flat
        current = self.threat_table.get(actor, 0.0)
        if taunt:
            # Taunt sets the actor to top-of-threat + 1.
            top = max(self.threat_table.values(), default=0.0)
            self.threat_table[actor] = top + 1.0 + threat
        else:
            self.threat_table[actor] = current + threat

    def top_threat(self) -> str | None:
        if not self.threat_table:
            return None
        return max(self.threat_table, key=self.threat_table.get)  # type: ignore[arg-type]

    def decay_threat(self, factor: float = 0.95) -> None:
        """Threat decay over time."""
        self.threat_table = {
            actor: value * factor for actor, value in self.threat_table.items()
        }

    # -- Damage intake ------------------------------------------------------- #

    def take_hit(self, raw: float, damage_type: DamageType,
                 attacker_level: int = 1) -> float:
        """Apply resistances, mitigation, and reflect (Reflective affix)."""
        if damage_type in self.stats.resistances.immunity:
            return 0.0
        damage = self.stats.take_damage(raw, damage_type, attacker_level)
        if AffixId.REFLECTIVE in self.affixes and damage > 0:
            self.reflected = damage * 0.2
        if self.stats.resources.get("hp") <= 0:
            self.alive = False
        return damage

    # -- AI ability selection (utility scoring) ------------------------------ #

    def choose_ability(
        self, distance: float, target_hp_fraction: float, phase: int = 1,
        rng: random.Random | None = None,
    ) -> Ability | None:
        """Pick the highest-scoring ready ability; respects phase gates."""
        rng = rng or random.Random()
        best: Ability | None = None
        best_score = -1.0
        for ability in self.abilities:
            if ability.min_phase > phase:
                continue
            if self.cooldowns.get(ability.id, 0.0) > 0.0:
                continue
            score = 1.0
            score += (1.0 - min(1.0, abs(distance - 10.0) / 40.0))  # range fit
            score += (1.0 - target_hp_fraction)  # prefer execute on low HP
            score += ability.power / 1000.0  # prefer stronger abilities
            score += rng.random() * 0.1  # tie-break jitter
            if score > best_score:
                best, best_score = ability, score
        return best

    def start_cooldown(self, ability: Ability, duration: float | None = None) -> None:
        self.cooldowns[ability.id] = duration if duration is not None else ability.cooldown

    def tick_cooldowns(self, dt: float) -> None:
        self.cooldowns = {
            ability_id: remaining - dt
            for ability_id, remaining in self.cooldowns.items()
            if remaining - dt > 0.0
        }
        self.effects.tick(dt)


# --------------------------------------------------------------------------- #
# Enemy templates per taxonomy tier (section 11 of the spec)                   #
# --------------------------------------------------------------------------- #

TIER_BASELINES: dict[EnemyTier, float] = {
    EnemyTier.TRASH: 0.7,
    EnemyTier.VETERAN: 1.35,
    EnemyTier.ELITE: 2.5,
    EnemyTier.CHAMPION: 3.25,
    EnemyTier.DUNGEON_BOSS: 10.0,
    EnemyTier.WORLD_BOSS: 40.0,
    EnemyTier.RAID_BOSS: 100.0,
    EnemyTier.MYTHIC: 200.0,
}

TIER_SKILL_COUNTS: dict[EnemyTier, tuple[int, int]] = {
    EnemyTier.TRASH: (1, 2),
    EnemyTier.VETERAN: (3, 5),
    EnemyTier.ELITE: (4, 6),
    EnemyTier.CHAMPION: (5, 7),
    EnemyTier.DUNGEON_BOSS: (5, 8),
    EnemyTier.WORLD_BOSS: (6, 10),
    EnemyTier.RAID_BOSS: (8, 12),
    EnemyTier.MYTHIC: (10, 15),
}

TIER_IMMUNITIES: dict[EnemyTier, set[DamageType]] = {
    EnemyTier.TRASH: set(),
    EnemyTier.VETERAN: set(),
    EnemyTier.ELITE: set(),
    EnemyTier.CHAMPION: set(),
    EnemyTier.DUNGEON_BOSS: set(),
    EnemyTier.WORLD_BOSS: {DamageType.SHADOW},
    EnemyTier.RAID_BOSS: {DamageType.SHADOW, DamageType.POISON},
    EnemyTier.MYTHIC: {DamageType.SHADOW, DamageType.POISON, DamageType.FROST},
}


def spawn_enemy(
    name: str, tier: EnemyTier, rank: EnemyRank = EnemyRank.NORMAL,
    level: int = 1, ai_role: AIRole = AIRole.BRUTE,
) -> Enemy:
    """Spawn an enemy from a taxonomy tier with the right baseline/immunities."""
    enemy = Enemy.spawn(
        name, tier, rank, level, ai_role, baseline=TIER_BASELINES[tier]
    )
    enemy.stats.resistances.immunity = set(TIER_IMMUNITIES[tier])
    return enemy
