from __future__ import annotations

from dataclasses import dataclass, field

from ..mmorpg import PlayerSession, ServerStatus


@dataclass(frozen=True)
class ServerConfig:
    server_id: str = "world-1"
    capacity: int = 1000


@dataclass
class GameServer:
    config: ServerConfig
    status: ServerStatus = ServerStatus.OFFLINE
    sessions: dict[str, PlayerSession] = field(default_factory=dict)

    def start(self) -> None:
        self.status = ServerStatus.ONLINE

    def stop(self) -> None:
        self.status = ServerStatus.OFFLINE
        self.sessions.clear()

    def connect(self, session: PlayerSession) -> None:
        if self.status != ServerStatus.ONLINE:
            raise RuntimeError("server is not online")
        if len(self.sessions) >= self.config.capacity:
            raise RuntimeError("server is full")
        self.sessions[session.session_id] = session

    def disconnect(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def tick(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("seconds cannot be negative")
        for session in self.sessions.values():
            session.connected = True
