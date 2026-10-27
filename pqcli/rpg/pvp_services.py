from __future__ import annotations

from dataclasses import dataclass
from .mmorpg import MatchRequest, Matchmaker


@dataclass(frozen=True)
class ArenaMatch:
    match_id: str
    mode: str
    players: tuple[str, ...]
    rating: int


class PvPService:
    def __init__(self) -> None:
        self.matchmaker = Matchmaker()
        self.matches: dict[str, ArenaMatch] = {}

    def queue(self, player_id: str, mode: str, rating: int = 1000, role: str | None = None) -> None:
        self.matchmaker.enqueue(MatchRequest(player_id, mode, rating, role))

    def make_match(self, match_id: str, mode: str, size: int = 2) -> ArenaMatch | None:
        requests = self.matchmaker.pop_match(mode, size)
        if len(requests) != size:
            for request in reversed(requests):
                self.matchmaker.queues.setdefault(mode, []).insert(0, request)
            return None
        avg_rating = sum(r.rating for r in requests) // size
        match = ArenaMatch(match_id, mode, tuple(r.player_id for r in requests), avg_rating)
        self.matches[match_id] = match
        return match
