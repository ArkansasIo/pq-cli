import random

from pqcli.rpg.combat import Attack, CombatEngine
from pqcli.rpg.enums import DamageType
from pqcli.rpg.stats import CombatStats, ResourcePool


def test_combat_deals_damage() -> None:
    engine = CombatEngine(random.Random(1))
    attacker = CombatStats(attack=20, crit_chance=0, dodge_chance=0)
    defender = CombatStats(armor=0, dodge_chance=0, block_chance=0)
    resources = ResourcePool(100, 0)
    result = engine.resolve(Attack("a", "b", 10, DamageType.PHYSICAL), attacker, defender, resources)
    assert result.damage > 0
    assert resources.hp < 100
