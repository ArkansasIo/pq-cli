from dataclasses import dataclass, field


@dataclass(frozen=True)
class Achievement:
    id: str
    name: str
    description: str
    points: int = 10
    hidden: bool = False


@dataclass
class AchievementBook:
    definitions: dict[str, Achievement] = field(default_factory=dict)
    unlocked: set[str] = field(default_factory=set)

    def unlock(self, achievement_id: str) -> bool:
        if achievement_id not in self.definitions or achievement_id in self.unlocked:
            return False
        self.unlocked.add(achievement_id)
        return True

    @property
    def points(self) -> int:
        return sum(self.definitions[a].points for a in self.unlocked if a in self.definitions)
