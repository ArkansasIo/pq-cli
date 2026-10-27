"""Encounter templates: open-world packs, dungeon rooms, raid archetypes.

Reusable encounter layouts (section J of the spec) that compose enemies from
the taxonomy tiers. Each template can `spawn()` a concrete enemy list.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum

from .enemies import AIRole, Enemy, EnemyRank, EnemyTier, spawn_enemy


class TemplateKind(StrEnum):
    OPEN_WORLD_PACK = "open_world_pack"
    RARE_SPAWN = "rare_spawn"
    EVENT_WAVES = "event_waves"
    PACK_HAZARD = "pack_hazard"
    PACK_MINIBOSS = "pack_miniboss"
    PUZZLE_ROOM = "puzzle_room"
    GAUNTLET = "gauntlet"
    BOSS_ADD_CYCLE = "boss_add_cycle"
    ARENA_MORPH = "arena_morph"
    SPLIT_ARENA = "split_arena"
    COUNCIL = "council"


@dataclass
class SpawnSpec:
    """One enemy slot in an encounter template."""

    tier: EnemyTier
    rank: EnemyRank = EnemyRank.NORMAL
    role: AIRole = AIRole.BRUTE
    name: str = "Enemy"
    count: int = 1


@dataclass
class EncounterTemplate:
    """A reusable encounter layout."""

    id: str
    name: str
    kind: TemplateKind
    spawns: list[SpawnSpec] = field(default_factory=list)
    waves: int = 1  # for event_waves / gauntlet templates
    hazard: str | None = None
    puzzle_objective: str | None = None
    level: int = 1
    recommended_players: int = 1
    mechanic: str | None = None  # e.g. "tank_swap", "spread", "soak"

    def spawn(self, rng: random.Random | None = None) -> list[Enemy]:
        """Materialize all waves of enemies from the spawn specs."""
        rng = rng or random.Random()
        enemies: list[Enemy] = []
        for _ in range(max(1, self.waves)):
            for spec in self.spawns:
                for _ in range(spec.count):
                    suffix = f" {rng.randint(2, 99)}" if spec.count > 1 else ""
                    enemies.append(spawn_enemy(
                        f"{spec.name}{suffix}", spec.tier, spec.rank,
                        level=self.level, ai_role=spec.role,
                    ))
        return enemies


# --------------------------------------------------------------------------- #
# Built-in templates (section J of the spec)                                   #
# --------------------------------------------------------------------------- #

BUILT_IN_TEMPLATES: dict[str, EncounterTemplate] = {
    # -- Open world ---------------------------------------------------------- #
    "basic_pack": EncounterTemplate(
        id="basic_pack", name="Basic Pack",
        kind=TemplateKind.OPEN_WORLD_PACK, level=1,
        spawns=[
            SpawnSpec(EnemyTier.TRASH, name="Marauder", count=3),
            SpawnSpec(EnemyTier.TRASH, role=AIRole.CASTER, name="Hexer"),
        ],
    ),
    "patrol_pack": EncounterTemplate(
        id="patrol_pack", name="Patrol with Veteran",
        kind=TemplateKind.OPEN_WORLD_PACK, level=10,
        spawns=[
            SpawnSpec(EnemyTier.TRASH, name="Scout", count=2),
            SpawnSpec(EnemyTier.VETERAN, role=AIRole.TANK, name="Sergeant"),
        ],
        mechanic="interrupt",
    ),
    "rare_named": EncounterTemplate(
        id="rare_named", name="Rare Named Spawn",
        kind=TemplateKind.RARE_SPAWN, level=15,
        spawns=[SpawnSpec(EnemyTier.ELITE, EnemyRank.CHAMPION,
                          role=AIRole.TRICKSTER, name="Wraith Lord")],
        mechanic="positioning",
    ),
    "event_waves": EncounterTemplate(
        id="event_waves", name="Invasion Event",
        kind=TemplateKind.EVENT_WAVES, level=20, waves=5,
        spawns=[
            SpawnSpec(EnemyTier.TRASH, name="Invader", count=4),
            SpawnSpec(EnemyTier.VETERAN, role=AIRole.CASTER, name="Warlock"),
        ],
    ),
    # -- Dungeon rooms ------------------------------------------------------- #
    "hazard_room": EncounterTemplate(
        id="hazard_room", name="Hazard Room",
        kind=TemplateKind.PACK_HAZARD, level=30, hazard="lava",
        recommended_players=5,
        spawns=[
            SpawnSpec(EnemyTier.VETERAN, name="Orc Brute", count=2),
            SpawnSpec(EnemyTier.VETERAN, role=AIRole.SNIPER, name="Arsonist", count=2),
        ],
        mechanic="spread",
    ),
    "miniboss_room": EncounterTemplate(
        id="miniboss_room", name="Mini-boss Room",
        kind=TemplateKind.PACK_MINIBOSS, level=35, recommended_players=5,
        spawns=[
            SpawnSpec(EnemyTier.ELITE, EnemyRank.ELITE, AIRole.BRUTE,
                      name="Dungeon Champion"),
            SpawnSpec(EnemyTier.TRASH, name="Lackey", count=2),
        ],
        mechanic="add_priority",
    ),
    "puzzle_room": EncounterTemplate(
        id="puzzle_room", name="Seal Chamber",
        kind=TemplateKind.PUZZLE_ROOM, level=40, recommended_players=5,
        puzzle_objective="destroy 3 crystals to break the barrier",
        spawns=[SpawnSpec(EnemyTier.VETERAN, AIRole.CONTROLLER,
                          name="Seal Warden", count=2)],
    ),
    "gauntlet_corridor": EncounterTemplate(
        id="gauntlet_corridor", name="Timed Gauntlet",
        kind=TemplateKind.GAUNTLET, level=45, waves=8, recommended_players=5,
        spawns=[SpawnSpec(EnemyTier.TRASH, name="Hound", count=3)],
        mechanic="time_pressure",
    ),
    # -- Raid archetypes ----------------------------------------------------- #
    "boss_add_cycle": EncounterTemplate(
        id="boss_add_cycle", name="Boss + Add Cycle",
        kind=TemplateKind.BOSS_ADD_CYCLE, level=60, recommended_players=10,
        spawns=[
            SpawnSpec(EnemyTier.RAID_BOSS, EnemyRank.BOSS, AIRole.BRUTE,
                      name="Raid Boss"),
            SpawnSpec(EnemyTier.VETERAN, role=AIRole.SUMMONER, name="Add Spawner",
                      count=2),
        ],
        mechanic="add_priority",
    ),
    "arena_morph": EncounterTemplate(
        id="arena_morph", name="Arena Morph Fight",
        kind=TemplateKind.ARENA_MORPH, level=60, recommended_players=10,
        hazard="rotating_lasers",
        spawns=[SpawnSpec(EnemyTier.RAID_BOSS, EnemyRank.BOSS,
                          role=AIRole.CASTER, name="Storm Sovereign")],
        mechanic="movement",
    ),
    "split_arena": EncounterTemplate(
        id="split_arena", name="Two Bosses, Shared Arena",
        kind=TemplateKind.SPLIT_ARENA, level=60, recommended_players=20,
        spawns=[
            SpawnSpec(EnemyTier.RAID_BOSS, EnemyRank.BOSS, AIRole.BRUTE,
                      name="Twin Fang"),
            SpawnSpec(EnemyTier.RAID_BOSS, EnemyRank.BOSS, AIRole.CASTER,
                      name="Twin Venom"),
        ],
        mechanic="tank_swap",
    ),
    "council_fight": EncounterTemplate(
        id="council_fight", name="Council Fight",
        kind=TemplateKind.COUNCIL, level=60, recommended_players=20,
        spawns=[
            SpawnSpec(EnemyTier.ELITE, EnemyRank.CHAMPION, AIRole.BRUTE,
                      name="Councilor", count=4),
        ],
        mechanic="multi_target_priority",
    ),
}


def get_template(template_id: str) -> EncounterTemplate:
    return BUILT_IN_TEMPLATES[template_id]
