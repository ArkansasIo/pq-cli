from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuntimeState:
    character_id: str
    current_hp: int
    current_mp: int
    zone_id: str | None = None
    instance_id: str | None = None
    in_combat: bool = False
    dead: bool = False

    def heal_full(self, max_hp: int, max_mp: int) -> None:
        self.current_hp = max_hp
        self.current_mp = max_mp
        self.dead = False
