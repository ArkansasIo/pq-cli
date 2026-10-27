from dataclasses import dataclass, field

from .enums import FactionStanding


@dataclass
class Faction:
    id: str
    name: str
    thresholds: tuple[int, ...] = (-42000, -6000, 0, 6000, 12000, 21000, 42000)

    def standing(self, reputation: int) -> FactionStanding:
        if reputation <= self.thresholds[0]: return FactionStanding.HOSTILE
        if reputation <= self.thresholds[1]: return FactionStanding.UNFRIENDLY
        if reputation < self.thresholds[2]: return FactionStanding.NEUTRAL
        if reputation < self.thresholds[3]: return FactionStanding.FRIENDLY
        if reputation < self.thresholds[4]: return FactionStanding.HONORED
        if reputation < self.thresholds[5]: return FactionStanding.REVERED
        return FactionStanding.EXALTED


@dataclass
class ReputationBook:
    values: dict[str, int] = field(default_factory=dict)

    def add(self, faction_id: str, amount: int) -> int:
        self.values[faction_id] = self.values.get(faction_id, 0) + amount
        return self.values[faction_id]
