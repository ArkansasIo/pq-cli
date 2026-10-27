from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TradeOffer:
    item_id: str
    quantity: int


class TradeError(ValueError):
    pass


class TradeSession:
    def __init__(self, trade_id: str, player_a: str, player_b: str) -> None:
        self.trade_id = trade_id
        self.players = (player_a, player_b)
        self.offers: dict[str, list[TradeOffer]] = {player_a: [], player_b: []}
        self.accepted: set[str] = set()

    def offer(self, player_id: str, item_id: str, quantity: int) -> None:
        if player_id not in self.players:
            raise TradeError("player is not part of this trade")
        if quantity <= 0:
            raise TradeError("quantity must be positive")
        self.offers[player_id].append(TradeOffer(item_id, quantity))
        self.accepted.clear()

    def accept(self, player_id: str) -> bool:
        if player_id not in self.players:
            raise TradeError("player is not part of this trade")
        self.accepted.add(player_id)
        return len(self.accepted) == 2

    @property
    def ready(self) -> bool:
        return len(self.accepted) == 2
