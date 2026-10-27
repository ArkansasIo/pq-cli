from dataclasses import dataclass, field

from .enums import QuestStatus


@dataclass(frozen=True)
class Objective:
    id: str
    description: str
    required: int = 1
    progress: int = 0

    @property
    def complete(self) -> bool:
        return self.progress >= self.required


@dataclass
class Quest:
    id: str
    name: str
    description: str
    xp_reward: int = 0
    gold_reward: int = 0
    objectives: list[Objective] = field(default_factory=list)
    status: QuestStatus = QuestStatus.AVAILABLE

    @property
    def complete(self) -> bool:
        return bool(self.objectives) and all(o.complete for o in self.objectives)

    def start(self) -> None:
        if self.status == QuestStatus.AVAILABLE:
            self.status = QuestStatus.ACTIVE

    def update(self, objective_id: str, amount: int = 1) -> bool:
        for i, objective in enumerate(self.objectives):
            if objective.id == objective_id:
                self.objectives[i] = Objective(
                    objective.id, objective.description, objective.required,
                    min(objective.required, objective.progress + amount),
                )
                if self.complete:
                    self.status = QuestStatus.COMPLETE
                return True
        return False


@dataclass
class QuestLog:
    quests: dict[str, Quest] = field(default_factory=dict)

    def accept(self, quest: Quest) -> bool:
        if quest.id in self.quests:
            return False
        quest.start()
        self.quests[quest.id] = quest
        return True

    def active(self) -> list[Quest]:
        return [q for q in self.quests.values() if q.status == QuestStatus.ACTIVE]
