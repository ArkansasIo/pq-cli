from __future__ import annotations

from .character import Character
from .items import Item


class InventoryService:
    def add_item(self, character: Character, item: Item, quantity: int = 1) -> int:
        return character.inventory.add(item.id, quantity, item.stack_size)

    def remove_item(self, character: Character, item_id: str, quantity: int = 1) -> bool:
        return character.inventory.remove(item_id, quantity)

    def has_item(self, character: Character, item_id: str, quantity: int = 1) -> bool:
        return character.inventory.count(item_id) >= quantity

    def grant_gold(self, character: Character, amount: int) -> None:
        if amount < 0:
            raise ValueError("amount cannot be negative")
        character.inventory.gold += amount

    def spend_gold(self, character: Character, amount: int) -> bool:
        if amount < 0 or character.inventory.gold < amount:
            return False
        character.inventory.gold -= amount
        return True
