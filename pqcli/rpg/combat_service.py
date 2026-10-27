from __future__ import annotations

from dataclasses import dataclass
import random

from .character import Character


@dataclass(frozen=True)
class CombatResult:
    attacker_id: str
    defender_id: str
    hit: bool
    critical: bool
    damage: int


class CombatService:
    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()

    def attack(self, attacker: Character, defender: Character) -> CombatResult:
        offense = attacker.combat_stats.attack_power
        defense = defender.combat_stats.defense
        hit = self.rng.random() < max(0.05, min(0.95, 0.75 + (offense - defense) / 200.0))
        if not hit:
            return CombatResult(attacker.id, defender.id, False, False, 0)
        critical = self.rng.random() < attacker.combat_stats.crit_chance
        damage = max(1, offense - defense // 2)
        if critical:
            damage *= 2
        return CombatResult(attacker.id, defender.id, True, critical, damage)
