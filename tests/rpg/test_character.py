from pqcli.rpg.character import Character
from pqcli.rpg.enums import ClassId, RaceId


def test_character_progression_and_racial_stats() -> None:
    character = Character("Aris", RaceId.ELF, ClassId.MAGE)
    assert character.combat_stats.attack > 0
    assert character.grant_xp(character.xp_for_level(2)) == 1
    assert character.level == 2


def test_inventory_round_trip_operations() -> None:
    character = Character("Tank")
    assert character.inventory.add("iron", 10, stack_size=20) == 0
    assert character.inventory.count("iron") == 10
    assert character.inventory.remove("iron", 4)
    assert character.inventory.count("iron") == 6
