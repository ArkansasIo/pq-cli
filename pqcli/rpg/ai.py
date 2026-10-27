"""Enemy AI: universal state machine + combat sub-states.

Implements the AI layer of the stat framework (section K):

    Idle -> Patrol -> Alert -> Engage -> Combat -> Retreat -> Reset

Combat sub-states decide whether the enemy maintains range, bursts, plays
defensive, summons, or casts its ultimate. Ability selection is delegated to
``Enemy.choose_ability`` (utility scoring with phase gates).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum

from .enemies import AIRole, Ability, Enemy


class AIState(StrEnum):
    IDLE = "idle"
    PATROL = "patrol"
    ALERT = "alert"
    ENGAGE = "engage"
    COMBAT = "combat"
    RETREAT = "retreat"
    RESET = "reset"


class CombatSubState(StrEnum):
    MAINTAIN_RANGE = "maintain_range"
    CLOSE_DISTANCE = "close_distance"
    BURST_WINDOW = "burst_window"
    DEFENSIVE_WINDOW = "defensive_window"
    SUMMON_ADDS = "summon_adds"
    CAST_ULTIMATE = "cast_ultimate"
    PHASE_TRANSITION = "phase_transition"


# Preferred engagement distance per AI archetype.
ROLE_PREFERRED_RANGE: dict[AIRole, float] = {
    AIRole.BRUTE: 3.0,
    AIRole.TANK: 3.0,
    AIRole.ASSASSIN: 2.0,
    AIRole.SNIPER: 30.0,
    AIRole.CASTER: 20.0,
    AIRole.CONTROLLER: 15.0,
    AIRole.SUMMONER: 25.0,
    AIRole.SUPPORT: 20.0,
    AIRole.TRICKSTER: 10.0,
}


@dataclass
class AIContext:
    """Perception inputs the AI reasons about each tick."""

    distance: float = 10.0
    own_hp_fraction: float = 1.0
    target_hp_fraction: float = 1.0
    phase: int = 1
    adds_remaining: int = 0
    target_visible: bool = True
    allies_threatened: bool = False


@dataclass
class AIBrain:
    """State machine + sub-state resolver driving one enemy."""

    enemy: Enemy
    state: AIState = AIState.IDLE
    sub_state: CombatSubState = CombatSubState.CLOSE_DISTANCE
    home_position: float = 0.0
    leash_range: float = 60.0  # distance before Reset kicks in
    aggro_range: float = 25.0
    retreat_threshold: float = 0.15  # HP fraction to flee
    context: AIContext = field(default_factory=AIContext)
    pending_ability: Ability | None = None
    cast_timer: float = 0.0
    position: float = 0.0

    def perceive(self, context: AIContext) -> None:
        """Update perception, then transition the top-level state."""
        self.context = context
        self._transition()

    def _transition(self) -> None:
        ctx = self.context
        if self.state == AIState.IDLE:
            if ctx.target_visible and ctx.distance <= self.aggro_range:
                self.state = AIState.ALERT
        elif self.state == AIState.ALERT:
            if ctx.distance <= self.aggro_range * 0.6:
                self.state = AIState.ENGAGE
            elif not ctx.target_visible:
                self.state = AIState.PATROL
        elif self.state == AIState.PATROL:
            if ctx.target_visible and ctx.distance <= self.aggro_range:
                self.state = AIState.ALERT
        elif self.state == AIState.ENGAGE:
            if ctx.distance <= self._preferred_range() * 1.5:
                self.state = AIState.COMBAT
        elif self.state == AIState.COMBAT:
            if ctx.own_hp_fraction <= self.retreat_threshold:
                self.state = AIState.RETREAT
            elif ctx.distance > self.leash_range:
                self.state = AIState.RESET
        elif self.state == AIState.RETREAT:
            if ctx.own_hp_fraction > self.retreat_threshold + 0.15:
                self.state = AIState.COMBAT
        elif self.state == AIState.RESET:
            if abs(self.position - self.home_position) < 1.0:
                self.state = AIState.IDLE
                self.enemy.threat_table.clear()

    def _preferred_range(self) -> float:
        return ROLE_PREFERRED_RANGE.get(self.enemy.ai_role, 10.0)

    # -- Sub-state resolution ------------------------------------------------ #

    def resolve_sub_state(self) -> CombatSubState:
        """Pick the combat sub-state from perception + role."""
        ctx = self.context
        preferred = self._preferred_range()
        if self.enemy.ai_role in (AIRole.SUMMONER, AIRole.CONTROLLER) and ctx.adds_remaining == 0:
            self.sub_state = CombatSubState.SUMMON_ADDS
        elif ctx.own_hp_fraction <= 0.25 and self.enemy.ai_role != AIRole.TANK:
            self.sub_state = CombatSubState.DEFENSIVE_WINDOW
        elif ctx.target_hp_fraction <= 0.25:
            self.sub_state = CombatSubState.BURST_WINDOW
        elif ctx.distance > preferred * 1.3:
            self.sub_state = CombatSubState.CLOSE_DISTANCE
        elif ctx.distance < preferred * 0.6 and self.enemy.ai_role in (
            AIRole.SNIPER, AIRole.CASTER, AIRole.SUMMONER, AIRole.SUPPORT,
        ):
            self.sub_state = CombatSubState.MAINTAIN_RANGE
        elif ctx.phase > 1 and any(
            a.min_phase == ctx.phase for a in self.enemy.abilities
        ):
            self.sub_state = CombatSubState.PHASE_TRANSITION
        else:
            self.sub_state = CombatSubState.BURST_WINDOW
        return self.sub_state

    # -- Act ----------------------------------------------------------------- #

    def act(self, dt: float, rng: random.Random | None = None) -> Ability | None:
        """Run one AI tick; may start casting or release an ability."""
        self.enemy.tick_cooldowns(dt)
        if self.state not in (AIState.ENGAGE, AIState.COMBAT):
            return None
        self.resolve_sub_state()
        ctx = self.context

        if self.pending_ability is not None:
            self.cast_timer -= dt
            if self.cast_timer <= 0:
                ability, self.pending_ability = self.pending_ability, None
                self.enemy.start_cooldown(ability)
                return ability
            return None  # still casting / telegraphing

        if self.sub_state in (
            CombatSubState.DEFENSIVE_WINDOW, CombatSubState.SUMMON_ADDS,
            CombatSubState.PHASE_TRANSITION,
        ):
            return None

        ability = self.enemy.choose_ability(
            distance=ctx.distance,
            target_hp_fraction=ctx.target_hp_fraction,
            phase=ctx.phase,
            rng=rng or random.Random(),
        )
        if ability is None:
            return None
        self.pending_ability = ability
        self.cast_timer = ability.telegraph + ability.cast_time
        return None
