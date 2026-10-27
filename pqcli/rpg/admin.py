from __future__ import annotations

from dataclasses import dataclass

from .server.world import GameServer


@dataclass(frozen=True)
class AdminAction:
    actor_id: str
    action: str
    target_id: str | None = None
    reason: str = ""


class AdminService:
    def __init__(self, server: GameServer) -> None:
        self.server = server
        self.audit_log: list[AdminAction] = []

    def record(self, action: AdminAction) -> None:
        self.audit_log.append(action)

    def kick(self, actor_id: str, session_id: str, reason: str = "") -> bool:
        existed = session_id in self.server.sessions
        self.server.disconnect(session_id)
        self.record(AdminAction(actor_id, "kick", session_id, reason))
        return existed

    def maintenance(self, actor_id: str, enabled: bool) -> None:
        self.server.status = self.server.status.__class__.MAINTENANCE if enabled else self.server.status.__class__.ONLINE
        self.record(AdminAction(actor_id, "maintenance_on" if enabled else "maintenance_off"))
