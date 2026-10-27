from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QuestProgress:
    quest_id: str
    objectives: dict[str, int] = field(default_factory=dict)
    completed: bool = False
    rewarded: bool = False

    def advance(self, objective: str, amount: int = 1) -> None:
        if amount <= 0:
            return
        self.objectives[objective] = self.objectives.get(objective, 0) + amount


class QuestService:
    def __init__(self) -> None:
        self.active: dict[str, dict[str, QuestProgress]] = {}

    def accept(self, player_id: str, quest_id: str) -> QuestProgress:
        progress = QuestProgress(quest_id)
        self.active.setdefault(player_id, {})[quest_id] = progress
        return progress

    def progress(self, player_id: str, quest_id: str, objective: str, amount: int = 1) -> QuestProgress:
        quest = self.active[player_id][quest_id]
        quest.advance(objective, amount)
        return quest

    def abandon(self, player_id: str, quest_id: str) -> bool:
        return self.active.get(player_id, {}).pop(quest_id, None) is not None
