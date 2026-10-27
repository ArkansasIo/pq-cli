from dataclasses import dataclass, field
from uuid import uuid4

from .enums import ClassId, EquipmentSlot, RaceId
from .items import Inventory
from .stats import Attributes, CombatStats, ResourcePool


RACE_BONUSES: dict[RaceId, Attributes] = {
    RaceId.HUMAN: Attributes(),
    RaceId.ELF: Attributes(dexterity=2, intelligence=2, constitution=-1),
    RaceId.DWARF: Attributes(constitution=3, vitality=2, dexterity=-1),
    RaceId.ORC: Attributes(strength=3, vitality=2, intelligence=-1),
    RaceId.HALFLING: Attributes(dexterity=3, luck=2, strength=-1),
    RaceId.UNDEAD: Attributes(spirit=3, willpower=2, charisma=-1),
    RaceId.DRACONIC: Attributes(strength=2, charisma=2, wisdom=1),
}


@dataclass
class Character:
    name: str
    race: RaceId = RaceId.HUMAN
    class_id: ClassId = ClassId.WARRIOR
    id: str = field(default_factory=lambda: str(uuid4()))
    level: int = 1
    xp: int = 0
    attributes: Attributes = field(default_factory=Attributes)
    inventory: Inventory = field(default_factory=Inventory)
    equipment: dict[EquipmentSlot, str] = field(default_factory=dict)
    skills: dict[str, int] = field(default_factory=dict)
    talents: dict[str, int] = field(default_factory=dict)
    achievements: set[str] = field(default_factory=set)
    reputation: dict[str, int] = field(default_factory=dict)

    @property
    def combat_stats(self) -> CombatStats:
        return CombatStats.from_attributes(self.attributes.add(RACE_BONUSES[self.race]))

    @property
    def resources(self) -> ResourcePool:
        stats = self.combat_stats
        return ResourcePool(stats.max_hp, stats.max_mp)

    @staticmethod
    def xp_for_level(level: int) -> int:
        return int(level**2.5 * 500)

    def grant_xp(self, amount: int) -> int:
        if amount <= 0:
            return 0
        self.xp += amount
        levels = 0
        while self.level < 100 and self.xp >= self.xp_for_level(self.level + 1):
            self.level += 1
            levels += 1
        return levels
