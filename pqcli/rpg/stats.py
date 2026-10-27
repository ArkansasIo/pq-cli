from dataclasses import dataclass, field


@dataclass
class Attributes:
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    vitality: int = 10
    spirit: int = 10
    luck: int = 10
    willpower: int = 10
    charisma: int = 10

    def add(self, other: "Attributes") -> "Attributes":
        return Attributes(**{name: getattr(self, name) + getattr(other, name) for name in self.__dataclass_fields__})

    def as_dict(self) -> dict[str, int]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


@dataclass
class CombatStats:
    max_hp: int = 100
    max_mp: int = 50
    attack: int = 10
    spell_power: int = 10
    armor: int = 0
    magic_resist: int = 0
    crit_chance: float = 0.05
    crit_multiplier: float = 1.5
    dodge_chance: float = 0.05
    block_chance: float = 0.0
    haste: float = 0.0
    move_speed: float = 1.0
    life_steal: float = 0.0
    threat: float = 1.0

    @classmethod
    def from_attributes(cls, a: Attributes) -> "CombatStats":
        return cls(
            max_hp=a.vitality * 15 + a.constitution * 10,
            max_mp=a.spirit * 5 + a.intelligence * 10,
            attack=a.strength * 2 + a.dexterity,
            spell_power=a.intelligence * 2 + a.wisdom,
            armor=a.constitution * 2 + a.vitality,
            magic_resist=a.wisdom + a.spirit,
            crit_chance=min(0.75, 0.02 + a.dexterity / 500),
            dodge_chance=min(0.50, 0.01 + a.dexterity / 400),
        )


@dataclass
class ResourcePool:
    hp: int
    mp: int
    stamina: int = 100
    rage: int = 0

    def clamp(self, stats: CombatStats) -> None:
        self.hp = max(0, min(self.hp, stats.max_hp))
        self.mp = max(0, min(self.mp, stats.max_mp))
        self.stamina = max(0, min(self.stamina, 100))
        self.rage = max(0, min(self.rage, 100))
