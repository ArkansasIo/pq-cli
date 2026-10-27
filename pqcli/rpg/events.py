from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorldEvent:
    id: str
    name: str
    zone_id: str
    duration_seconds: int
    objectives: tuple[str, ...] = ()
    reward_xp: int = 0
    reward_gold: int = 0


@dataclass
class EventManager:
    active: dict[str, WorldEvent] = field(default_factory=dict)

    def start(self, event: WorldEvent) -> None:
        self.active[event.id] = event

    def stop(self, event_id: str) -> None:
        self.active.pop(event_id, None)

    def in_zone(self, zone_id: str) -> list[WorldEvent]:
        return [e for e in self.active.values() if e.zone_id == zone_id]
