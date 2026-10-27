from dataclasses import dataclass, field
import random


@dataclass(frozen=True)
class LootEntry:
    item_id: str
    weight: int
    min_quantity: int = 1
    max_quantity: int = 1


@dataclass
class LootTable:
    id: str
    entries: list[LootEntry] = field(default_factory=list)

    def roll(self, rng: random.Random | None = None) -> list[tuple[str, int]]:
        rng = rng or random.Random()
        if not self.entries:
            return []
        total = sum(max(0, e.weight) for e in self.entries)
        if total <= 0:
            return []
        pick = rng.randint(1, total)
        for entry in self.entries:
            pick -= max(0, entry.weight)
            if pick <= 0:
                return [(entry.item_id, rng.randint(entry.min_quantity, entry.max_quantity))]
        return []
