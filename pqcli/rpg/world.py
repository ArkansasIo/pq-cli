from dataclasses import dataclass, field


@dataclass(frozen=True)
class Biome:
    id: str
    name: str
    level_min: int = 1
    level_max: int = 10
    climate: str = "temperate"


@dataclass
class Zone:
    id: str
    name: str
    biome_id: str
    level_min: int = 1
    level_max: int = 10
    dungeons: list[str] = field(default_factory=list)
    points_of_interest: list[str] = field(default_factory=list)


@dataclass
class World:
    zones: dict[str, Zone] = field(default_factory=dict)
    biomes: dict[str, Biome] = field(default_factory=dict)
    world_version: int = 1

    def add_zone(self, zone: Zone) -> None:
        self.zones[zone.id] = zone

    def zones_for_level(self, level: int) -> list[Zone]:
        return [z for z in self.zones.values() if z.level_min <= level <= z.level_max]
