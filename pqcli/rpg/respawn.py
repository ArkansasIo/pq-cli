from __future__ import annotations

from dataclasses import dataclass

from .character import Character
from .runtime import RuntimeState


@dataclass
class DeathState:
    dead: bool = False
    respawn_zone: str | None = None
    penalty_xp: int = 0


class RespawnService:
    def __init__(self) -> None:
        self.states: dict[str, DeathState] = {}

    def kill(self, character: Character, respawn_zone: str, xp_penalty: int = 0) -> DeathState:
        state = DeathState(True, respawn_zone, max(0, xp_penalty))
        self.states[character.id] = state
        return state

    def respawn(self, character: Character, runtime: RuntimeState | None = None) -> str:
        state = self.states.get(character.id)
        if state is None or not state.dead:
            raise ValueError("character is not dead")
        zone = state.respawn_zone or "starter_zone"
        if runtime is not None:
            runtime.zone_id = zone
            runtime.heal_full(character.combat_stats.max_hp, character.combat_stats.max_mp)
        state.dead = False
        return zone
