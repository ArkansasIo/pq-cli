from dataclasses import dataclass, field
import random

from .enums import DamageType
from .stats import CombatStats, ResourcePool


@dataclass(frozen=True)
class Attack:
    source: str
    target: str
    power: int
    damage_type: DamageType = DamageType.PHYSICAL
    can_crit: bool = True


@dataclass
class CombatResult:
    damage: int = 0
    critical: bool = False
    dodged: bool = False
    blocked: bool = False
    defeated: bool = False
    log: list[str] = field(default_factory=list)


class CombatEngine:
    """Deterministic-friendly combat resolver with injectable RNG."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()

    def resolve(
        self,
        attack: Attack,
        attacker: CombatStats,
        defender: CombatStats,
        defender_resources: ResourcePool,
    ) -> CombatResult:
        result = CombatResult()
        if self.rng.random() < defender.dodge_chance:
            result.dodged = True
            result.log.append(f"{attack.source} misses {attack.target}.")
            return result
        raw = max(1, attack.power + attacker.attack // 2)
        if attack.damage_type != DamageType.PHYSICAL:
            raw += attacker.spell_power // 2
        mitigation = defender.armor if attack.damage_type == DamageType.PHYSICAL else defender.magic_resist
        damage = max(1, int(raw * 100 / (100 + max(0, mitigation))))
        if self.rng.random() < attacker.crit_chance and attack.can_crit:
            result.critical = True
            damage = int(damage * attacker.crit_multiplier)
        if self.rng.random() < defender.block_chance:
            result.blocked = True
            damage = max(1, damage // 2)
        defender_resources.hp = max(0, defender_resources.hp - damage)
        result.damage = damage
        result.defeated = defender_resources.hp == 0
        result.log.append(f"{attack.source} hits {attack.target} for {damage} damage.")
        return result
