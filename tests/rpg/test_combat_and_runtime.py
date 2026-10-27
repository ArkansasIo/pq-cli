import random

from pqcli.rpg.character import Character
from pqcli.rpg.combat_service import CombatService
from pqcli.rpg.respawn import RespawnService
from pqcli.rpg.runtime import RuntimeState


def test_combat_service_uses_character_stats() -> None:
    attacker = Character("A")
    defender = Character("B")
    result = CombatService(random.Random(1)).attack(attacker, defender)
    assert result.attacker_id == attacker.id
    assert result.defender_id == defender.id
    assert result.damage >= 0


def test_respawn_restores_runtime() -> None:
    character = Character("A")
    runtime = RuntimeState(character.id, 0, 0, zone_id="danger")
    service = RespawnService()
    service.kill(character, "town")
    assert service.respawn(character, runtime) == "town"
    assert runtime.zone_id == "town"
    assert runtime.current_hp == character.combat_stats.max_hp
