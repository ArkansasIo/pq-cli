from pqcli.rpg.quests import Objective, Quest, QuestLog
from pqcli.rpg.enums import QuestStatus


def test_quest_completion() -> None:
    quest = Quest("q1", "Wolf Hunt", "Defeat wolves", objectives=[Objective("wolves", "Defeat wolves", 3)])
    log = QuestLog()
    assert log.accept(quest)
    assert quest.status == QuestStatus.ACTIVE
    quest.update("wolves", 3)
    assert quest.status == QuestStatus.COMPLETE
