from dataclasses import dataclass, field
from enum import StrEnum


class ServerStatus(StrEnum):
    OFFLINE = "offline"
    STARTING = "starting"
    ONLINE = "online"
    MAINTENANCE = "maintenance"


@dataclass
class PlayerSession:
    session_id: str
    account_id: str
    character_id: str
    zone_id: str | None = None
    connected: bool = True


@dataclass
class MatchRequest:
    player_id: str
    mode: str
    rating: int = 1000
    role: str | None = None


@dataclass
class Matchmaker:
    queues: dict[str, list[MatchRequest]] = field(default_factory=dict)

    def enqueue(self, request: MatchRequest) -> None:
        self.queues.setdefault(request.mode, []).append(request)

    def pop_match(self, mode: str, size: int) -> list[MatchRequest]:
        queue = self.queues.setdefault(mode, [])
        match = queue[:size]
        del queue[:size]
        return match


@dataclass
class WorldServer:
    server_id: str
    status: ServerStatus = ServerStatus.OFFLINE
    sessions: dict[str, PlayerSession] = field(default_factory=dict)
    capacity: int = 1000

    @property
    def online_count(self) -> int:
        return len(self.sessions)

    def can_accept(self) -> bool:
        return self.status == ServerStatus.ONLINE and self.online_count < self.capacity
