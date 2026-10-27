from dataclasses import dataclass, field


@dataclass(frozen=True)
class Encounter:
    id: str
    name: str
    enemy_ids: tuple[str, ...]
    reward_xp: int = 0
    reward_gold: int = 0


@dataclass
class Dungeon:
    id: str
    name: str
    level_min: int
    level_max: int
    encounters: list[Encounter] = field(default_factory=list)
    raid: bool = False
    max_players: int = 5

    def add_encounter(self, encounter: Encounter) -> None:
        self.encounters.append(encounter)


@dataclass
class DungeonInstance:
    dungeon_id: str
    instance_id: str
    players: list[str] = field(default_factory=list)
    encounter_index: int = 0
    completed: bool = False

    def advance(self) -> Encounter | None:
        return None
