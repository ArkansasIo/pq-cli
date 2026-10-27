"""Tests for AI, encounter templates and the gear catalog."""

from __future__ import annotations

import random

import pytest

from pqcli.rpg.ai import (
    AIContext, AIBrain, AIState, CombatSubState, ROLE_PREFERRED_RANGE,
)
from pqcli.rpg.catalog import CATALOG, GEAR_SETS, ASHEN_BLADE, WORLDBREAKER
from pqcli.rpg.effects import BUILT_IN_EFFECTS
from pqcli.rpg.encounters import (
    BUILT_IN_TEMPLATES, EncounterTemplate, SpawnSpec, TemplateKind,
)
from pqcli.rpg.enemies import AIRole, EnemyRank, EnemyTier, spawn_enemy
from pqcli.rpg.enums import EquipmentSlot, Rarity
from pqcli.rpg.equipment import EquipmentManager
from pqcli.rpg.stat_framework import SubStatId


# --------------------------------------------------------------------------- #
# AI                                                                           #
# --------------------------------------------------------------------------- #


class TestAIBrain:
    def _brain(self, role: AIRole = AIRole.BRUTE) -> AIBrain:
        enemy = spawn_enemy("Brute", EnemyTier.ELITE, level=30, ai_role=role)
        return AIBrain(enemy=enemy)

    def test_idle_to_alert_to_engage(self) -> None:
        brain = self._brain()
        brain.perceive(AIContext(distance=20, target_visible=True))
        assert brain.state == AIState.ALERT
        brain.perceive(AIContext(distance=10, target_visible=True))
        assert brain.state == AIState.ENGAGE
        brain.perceive(AIContext(distance=3, target_visible=True))
        assert brain.state == AIState.COMBAT

    def test_retreat_on_low_hp(self) -> None:
        brain = self._brain()
        brain.state = AIState.COMBAT
        brain.perceive(AIContext(distance=3, own_hp_fraction=0.05))
        assert brain.state == AIState.RETREAT

    def test_leash_reset(self) -> None:
        brain = self._brain()
        brain.state = AIState.COMBAT
        brain.position = 0.0
        brain.perceive(AIContext(distance=100, own_hp_fraction=1.0))
        assert brain.state == AIState.RESET

    def test_brute_closes_distance(self) -> None:
        brain = self._brain(AIRole.BRUTE)
        sub = brain.resolve_sub_state()
        assert sub == CombatSubState.CLOSE_DISTANCE  # far from preferred 3.0

    def test_sniper_maintains_range(self) -> None:
        brain = self._brain(AIRole.SNIPER)  # preferred 30
        brain.context = AIContext(distance=10.0)
        sub = brain.resolve_sub_state()
        assert sub == CombatSubState.MAINTAIN_RANGE

    def test_summoner_sums_adds(self) -> None:
        brain = self._brain(AIRole.SUMMONER)
        brain.context = AIContext(distance=25.0, adds_remaining=0)
        assert brain.resolve_sub_state() == CombatSubState.SUMMON_ADDS

    def test_burst_on_low_target_hp(self) -> None:
        brain = self._brain(AIRole.BRUTE)
        brain.context = AIContext(distance=3.0, target_hp_fraction=0.1)
        assert brain.resolve_sub_state() == CombatSubState.BURST_WINDOW

    def test_act_releases_after_telegraph(self) -> None:
        from pqcli.rpg.enemies import Ability
        brain = self._brain()
        brain.state = AIState.COMBAT
        brain.enemy.abilities = [Ability("hit", "Hit", power=50,
                                         telegraph=0.0, cast_time=0.0)]
        assert brain.act(0.1) is None  # starts casting
        ability = brain.act(0.1)
        assert ability is not None and ability.id == "hit"
        assert brain.enemy.cooldowns["hit"] > 0

    def test_act_ignores_noncombat_states(self) -> None:
        brain = self._brain()
        assert brain.act(0.1) is None  # IDLE

    def test_role_ranges(self) -> None:
        assert ROLE_PREFERRED_RANGE[AIRole.SNIPER] > ROLE_PREFERRED_RANGE[AIRole.BRUTE]


# --------------------------------------------------------------------------- #
# Encounter templates                                                          #
# --------------------------------------------------------------------------- #


class TestEncounterTemplates:
    def test_basic_pack_composition(self) -> None:
        template = BUILT_IN_TEMPLATES["basic_pack"]
        enemies = template.spawn(random.Random(7))
        assert len(enemies) == 4  # 3 marauders + 1 hexer
        assert all(e.alive for e in enemies)

    def test_event_waves_multiply(self) -> None:
        template = BUILT_IN_TEMPLATES["event_waves"]  # 5 waves of 5
        enemies = template.spawn(random.Random(1))
        assert len(enemies) == 25

    def test_council_multi_target(self) -> None:
        template = BUILT_IN_TEMPLATES["council_fight"]
        enemies = template.spawn()
        assert len(enemies) == 4
        assert enemies[0].rank == EnemyRank.CHAMPION

    def test_raid_templates_recommended_players(self) -> None:
        assert BUILT_IN_TEMPLATES["split_arena"].recommended_players == 20
        assert BUILT_IN_TEMPLATES["boss_add_cycle"].recommended_players == 10

    def test_hazard_and_puzzle_fields(self) -> None:
        assert BUILT_IN_TEMPLATES["hazard_room"].hazard == "lava"
        assert "crystals" in BUILT_IN_TEMPLATES["puzzle_room"].puzzle_objective

    def test_custom_template_spawns(self) -> None:
        template = EncounterTemplate(
            id="x", name="X", kind=TemplateKind.OPEN_WORLD_PACK, level=5,
            spawns=[SpawnSpec(EnemyTier.TRASH, EnemyRank.VETERAN, name="Z",
                              count=2)],
        )
        enemies = template.spawn(random.Random(3))
        assert len(enemies) == 2
        assert enemies[0].rank == EnemyRank.VETERAN
        assert enemies[0].level == 5

    def test_all_templates_have_unique_ids(self) -> None:
        assert len(BUILT_IN_TEMPLATES) == len({
            t.id for t in BUILT_IN_TEMPLATES.values()
        })


# --------------------------------------------------------------------------- #
# Catalog                                                                      #
# --------------------------------------------------------------------------- #


class TestCatalog:
    def test_all_items_have_dual_tables(self) -> None:
        for item in CATALOG.values():
            assert item.pve is not None and item.pvp is not None

    def test_pve_damage_exceeds_pvp(self) -> None:
        for item in CATALOG.values():
            if item.kind.name == "WEAPON" and item.pvp.base_damage > 0:
                assert item.pve.base_damage > item.pvp.base_damage

    def test_mythic_pvp_disabled(self) -> None:
        assert WORLDBREAKER.rarity == Rarity.MYTHIC
        assert WORLDBREAKER.pvp.base_damage == 0.0

    def test_ashen_blade_pve_procs(self) -> None:
        assert len(ASHEN_BLADE.pve.procs) == 1
        assert ASHEN_BLADE.pvp.procs == []  # procs disabled in PvP

    def test_pvp_defensive_stats(self) -> None:
        charm = CATALOG["sentinel_charm"]
        assert charm.pvp.base_stats[SubStatId.DAMAGE_REDUCTION.value] > 0

    def test_trinket_references_valid_effect(self) -> None:
        # every proc effect id must exist in the effect registry
        for item in CATALOG.values():
            for proc in item.pve.procs:
                assert proc.effect_id in BUILT_IN_EFFECTS

    def test_flame_set_pieces(self) -> None:
        flame = GEAR_SETS["flame"]
        assert {b.pieces for b in flame.bonuses} == {2, 4, 6}

    def test_full_set_via_manager(self) -> None:
        mgr = EquipmentManager()
        for item_id in ("flame_helm", "flame_chest", "flame_legs"):
            mgr.equip(CATALOG[item_id])
        bonuses = mgr.active_set_bonuses(GEAR_SETS)
        # 3 pieces meet the 2pc threshold only (4pc/6pc need more items)
        assert [b.pieces for b in bonuses] == [2]
        assert bonuses[0].stats == {SubStatId.ARMOR.value: 200}

    def test_pve_higher_item_power(self) -> None:
        for item in CATALOG.values():
            if item.pve.procs:
                assert item.item_power(False) > item.item_power(True)

    def test_slots_distinct(self) -> None:
        slots = [item.slot for item in CATALOG.values() if item.slot]
        assert EquipmentSlot.MAIN_HAND in slots
        assert EquipmentSlot.TRINKET_2 in slots
