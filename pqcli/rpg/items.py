from dataclasses import dataclass, field

from .enums import DamageType, EquipmentSlot, Rarity


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    rarity: Rarity = Rarity.COMMON
    level: int = 1
    value: int = 0
    stack_size: int = 1
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ItemStats:
    attack: int = 0
    armor: int = 0
    spell_power: int = 0
    hp: int = 0
    mp: int = 0
    strength: int = 0
    dexterity: int = 0
    constitution: int = 0
    intelligence: int = 0
    wisdom: int = 0
    vitality: int = 0
    spirit: int = 0
    crit: float = 0.0
    haste: float = 0.0


@dataclass(frozen=True)
class EquipmentItem(Item):
    slot: EquipmentSlot = EquipmentSlot.CHEST
    stats: ItemStats = field(default_factory=ItemStats)
    damage_type: DamageType = DamageType.PHYSICAL
    min_damage: int = 0
    max_damage: int = 0
    required_level: int = 1
    durability: int = 100


@dataclass
class InventoryStack:
    item_id: str
    quantity: int = 1


@dataclass
class Inventory:
    capacity: int = 30
    stacks: list[InventoryStack] = field(default_factory=list)
    gold: int = 0

    def add(self, item_id: str, quantity: int = 1, stack_size: int = 1) -> int:
        remaining = max(0, quantity)
        for stack in self.stacks:
            if stack.item_id == item_id and stack.quantity < stack_size:
                amount = min(remaining, stack_size - stack.quantity)
                stack.quantity += amount
                remaining -= amount
                if not remaining:
                    return 0
        while remaining and len(self.stacks) < self.capacity:
            amount = min(remaining, stack_size)
            self.stacks.append(InventoryStack(item_id, amount))
            remaining -= amount
        return remaining

    def remove(self, item_id: str, quantity: int = 1) -> bool:
        if quantity <= 0:
            return True
        if sum(s.quantity for s in self.stacks if s.item_id == item_id) < quantity:
            return False
        remaining = quantity
        for stack in list(self.stacks):
            if stack.item_id != item_id:
                continue
            amount = min(remaining, stack.quantity)
            stack.quantity -= amount
            remaining -= amount
            if stack.quantity == 0:
                self.stacks.remove(stack)
            if remaining == 0:
                break
        return True

    def count(self, item_id: str) -> int:
        return sum(s.quantity for s in self.stacks if s.item_id == item_id)
