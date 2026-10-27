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
    encounters: list[Encounter] = field(default_factory=list)
    players: list[str] = field(default_factory=list)
    encounter_index: int = 0
    completed: bool = False

    def advance(self) -> Encounter | None:
        if self.completed or self.encounter_index >= len(self.encounters):
            self.completed = True
            return None
        encounter = self.encounters[self.encounter_index]
        self.encounter_index += 1
        if self.encounter_index >= len(self.encounters):
            self.completed = True
        return encounter
