from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ZoneState:
    zone_id: str
    population: int = 0
    players: set[str] = field(default_factory=set)
    weather: str = "clear"
    event_id: str | None = None


class WorldService:
    def __init__(self) -> None:
        self.zones: dict[str, ZoneState] = {}

    def register_zone(self, zone_id: str) -> ZoneState:
        zone = self.zones.setdefault(zone_id, ZoneState(zone_id))
        return zone

    def enter(self, player_id: str, zone_id: str) -> None:
        zone = self.register_zone(zone_id)
        zone.players.add(player_id)
        zone.population = len(zone.players)

    def leave(self, player_id: str, zone_id: str) -> None:
        zone = self.zones.get(zone_id)
        if zone is None:
            return
        zone.players.discard(player_id)
        zone.population = len(zone.players)

    def set_weather(self, zone_id: str, weather: str) -> None:
        self.register_zone(zone_id).weather = weather

    def start_event(self, zone_id: str, event_id: str) -> None:
        self.register_zone(zone_id).event_id = event_id

    def end_event(self, zone_id: str) -> None:
        self.register_zone(zone_id).event_id = None
