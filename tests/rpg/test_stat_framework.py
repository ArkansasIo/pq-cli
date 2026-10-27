"""Tests for the stat framework, effects, enemies and equipment layers."""

from __future__ import annotations

import pytest

from pqcli.rpg.effects import (
    BUILT_IN_EFFECTS, ActiveEffect, CleanseType, EffectCategory, EffectDef,
    EffectHost, EffectKind, ImmunityKind, StackMode,
)
from pqcli.rpg.enemies import (
    AIRole, BossData, DifficultyTier, Enemy, EnemyRank, EnemyTier,
    RANK_MULTIPLIERS, TIER_BASELINES, spawn_enemy,
)
from pqcli.rpg.enums import DamageType, EquipmentSlot, Rarity
from pqcli.rpg.equipment import (
    ArmorWeight, GearSet, ItemDef, ItemKind, Proc, SetBonus, StatTable,
    STANDARD_SLOTS, WeaponClass,
)
from pqcli.rpg.stat_framework import (
    HARD_CAPS, PVP_MULTIPLIERS, Cap, CoreAttribute, ResourceBars,
    ResourceId, Resistances, StatBlock, SubAttributes, SubStatCategory,
    SubStatId, boss_damage, boss_hp, crit_multiplier, damage_taken,
    diminishing_curve, encounter_power_budget, hit_chance, mitigation,
    power_units, proc_value, soft_cap_curve,
)


# --------------------------------------------------------------------------- #
# Stat framework                                                               #
# --------------------------------------------------------------------------- #


class TestSubAttributes:
    def test_derived_from_attributes(self) -> None:
        sub = SubAttributes.from_attributes(
            __import__("pqcli.rpg.stats", fromlist=["Attributes"]).Attributes()
        )
        assert sub.get(SubStatId.PHYSICAL_POWER) == pytest.approx(25.0)  # 10 str * 2.5
        assert sub.get(SubStatId.SPELL_POWER) == pytest.approx(25.0)

    def test_gear_adds_stats(self) -> None:
        attrs = __import__("pqcli.rpg.stats", fromlist=["Attributes"]).Attributes()
        sub = SubAttributes.from_attributes(attrs, gear={"crit_chance": 0.10})
        # base 0.05 + 10*0.0004 dex + 10*0.0002 luck + gear 0.10
        assert sub.get(SubStatId.CRIT_CHANCE) == pytest.approx(0.156)

    def test_pvp_scaling_reduces_damage_stats(self) -> None:
        attrs = __import__("pqcli.rpg.stats", fromlist=["Attributes"]).Attributes()
        pve = SubAttributes.from_attributes(attrs)
        pvp = SubAttributes.from_attributes(attrs, pvp=True)
        assert pvp.get(SubStatId.PHYSICAL_POWER) < pve.get(SubStatId.PHYSICAL_POWER)

    def test_hard_caps_enforced(self) -> None:
        sub = SubAttributes.from_attributes(
            __import__("pqcli.rpg.stats", fromlist=["Attributes"]).Attributes(),
            gear={"crit_chance": 5.0},
        )
        assert sub.get(SubStatId.CRIT_CHANCE) <= HARD_CAPS[SubStatId.CRIT_CHANCE].pve


class TestFormulas:
    def test_hit_chance_bounds(self) -> None:
        assert hit_chance(100, 1) == 0.95
        assert hit_chance(1, 100) == 0.05
        assert hit_chance(50, 50) == pytest.approx(0.5)

    def test_mitigation_increases_with_armor(self) -> None:
        assert mitigation(0, 10) == 0.0
        assert mitigation(1000, 10) > mitigation(100, 10)
        assert mitigation(1e9, 10) <= 0.85

    def test_damage_taken_pipeline(self) -> None:
        raw = damage_taken(100.0, armor=300.0, resist_pct=0.0,
                           attacker_level=10, k=100.0)
        assert 0 < raw < 100
        # Full vulnerability adds damage back
        vuln = damage_taken(100.0, armor=0.0, resist_pct=0.0,
                            attacker_level=10, vulnerability_pct=0.25)
        assert vuln == pytest.approx(125.0)

    def test_curves(self) -> None:
        assert soft_cap_curve(0, 100) == 0.0
        assert soft_cap_curve(100, 100) == pytest.approx(50.0)
        assert diminishing_curve(0, 100, 50) == 0.0
        assert diminishing_curve(1e6, 100, 50) == pytest.approx(100.0, rel=1e-3)

    def test_power_units_weights(self) -> None:
        crit_only = power_units({"crit_chance": 10})
        plain_only = power_units({"accuracy": 10})
        assert crit_only > plain_only  # weighted 2.5 vs 1.0

    def test_proc_value(self) -> None:
        assert proc_value(300, 0.25, 1.2) == pytest.approx(90.0)


class TestStatBlock:
    def test_recompute_resources(self) -> None:
        block = StatBlock()
        block.recompute()
        assert block.resources.get(ResourceId.HP) == (
            block.attributes.vitality * 15 + block.attributes.constitution * 10
        )
        assert block.resources.get(ResourceId.MP) > 0

    def test_take_damage_reduces_hp(self) -> None:
        block = StatBlock()
        block.recompute()
        before = block.resources.get(ResourceId.HP)
        block.take_damage(50, DamageType.PHYSICAL, attacker_level=1)
        assert block.resources.get(ResourceId.HP) < before

    def test_immunity_zeroes_damage(self) -> None:
        block = StatBlock()
        block.recompute()
        block.resistances.immunity.add(DamageType.FIRE)
        before = block.resources.get(ResourceId.HP)
        assert block.take_damage(500, DamageType.FIRE) == 0.0
        assert block.resources.get(ResourceId.HP) == before

    def test_resistance_layers(self) -> None:
        resist = Resistances(
            flat={DamageType.FIRE: 20},
            percent={DamageType.FIRE: 0.5},
            absorption={DamageType.FIRE: 10},
        )
        # 100 raw - 20 flat = 80; *0.5 = 40; -10 absorb = 30
        assert resist.apply(100, DamageType.FIRE) == pytest.approx(30.0)
        assert resist.apply(100, DamageType.FROST) == pytest.approx(100.0)


class TestScaling:
    def test_boss_hp_scales_with_party(self) -> None:
        solo = boss_hp(1000, 0, 1, 1.0)
        raid = boss_hp(1000, 0, 10, 1.0)
        assert raid == pytest.approx(solo * (1 + 9 * 0.65))

    def test_boss_damage_slower_than_hp(self) -> None:
        hp = boss_hp(1000, 10, 1, 1.0) / 1000
        dmg = boss_damage(1000, 10, 1.0) / 1000
        assert dmg < hp  # damage scales slower than HP

    def test_encounter_budget(self) -> None:
        assert encounter_power_budget([100.0, 200.0], 1.5) == pytest.approx(450.0)


# --------------------------------------------------------------------------- #
# Effects (buffs / debuffs)                                                    #
# --------------------------------------------------------------------------- #


class TestEffects:
    def test_buff_stat_modifier(self) -> None:
        host = EffectHost("hero")
        assert host.apply(BUILT_IN_EFFECTS["power_surge"]) is True
        assert host.stat_modifier(SubStatId.PHYSICAL_POWER) == pytest.approx(0.20)

    def test_stacking_additive(self) -> None:
        host = EffectHost("hero")
        burn = BUILT_IN_EFFECTS["burn"]
        host.apply(burn)
        host.apply(burn)
        host.apply(burn)
        host.apply(burn)  # max 3 stacks
        effect = host.active[0]
        assert effect.stacks == 3

    def test_cc_diminishing_returns(self) -> None:
        host = EffectHost("hero")
        stun = BUILT_IN_EFFECTS["stun"]
        assert host.apply(stun, now=0.0) is True
        host.purge()
        assert host.apply(stun, now=1.0) is True  # 50% window still applies
        host.purge()
        assert host.apply(stun, now=2.0) is True  # 25%
        host.purge()
        assert host.apply(stun, now=3.0) is False  # DR'd out

    def test_cc_immune_blocks_cc_only(self) -> None:
        host = EffectHost("hero")
        host.immunity = ImmunityKind.CC_IMMUNE
        assert host.apply(BUILT_IN_EFFECTS["stun"]) is False
        assert host.apply(BUILT_IN_EFFECTS["weaken"]) is True

    def test_cleanse_by_type(self) -> None:
        host = EffectHost("hero")
        host.apply(BUILT_IN_EFFECTS["burn"])  # physical cleanse
        host.apply(BUILT_IN_EFFECTS["curse"])  # curse cleanse
        assert host.cleanse(CleanseType.POISON) == 0
        assert host.cleanse(CleanseType.PHYSICAL) == 1
        assert host.cleanse(CleanseType.CURSE) == 1

    def test_dot_ticks(self) -> None:
        host = EffectHost("hero")
        host.apply(BUILT_IN_EFFECTS["bleed"], now=0.0)
        damage, heal = host.tick(1.0)
        assert damage == pytest.approx(15.0)  # one 1s tick
        assert heal == 0.0

    def test_expiry(self) -> None:
        host = EffectHost("hero")
        short = EffectDef("t", "T", EffectKind.BUFF, EffectCategory.UTILITY,
                          duration=1.0)
        host.apply(short)
        host.tick(2.0)
        assert host.active == []

    def test_multiply_bonuses(self) -> None:
        host = EffectHost("hero")
        haste = BUILT_IN_EFFECTS["haste"]
        host.apply(haste)
        host.apply(BUILT_IN_EFFECTS["berserk"])  # same stat, independent defs
        mod = host.stat_modifier(SubStatId.ATTACK_SPEED)
        assert mod == pytest.approx(1.25 * 1.30 - 1.0)


# --------------------------------------------------------------------------- #
# Enemies                                                                      #
# --------------------------------------------------------------------------- #


class TestEnemies:
    def test_tier_baselines_ordered(self) -> None:
        assert (
            TIER_BASELINES[EnemyTier.TRASH]
            < TIER_BASELINES[EnemyTier.ELITE]
            < TIER_BASELINES[EnemyTier.RAID_BOSS]
        )

    def test_rank_multipliers_ordered(self) -> None:
        assert (
            RANK_MULTIPLIERS[EnemyRank.NORMAL]
            < RANK_MULTIPLIERS[EnemyRank.ELITE]
            < RANK_MULTIPLIERS[EnemyRank.ASCENDED]
        )

    def test_spawn_scales_stats(self) -> None:
        trash = spawn_enemy("Rat", EnemyTier.TRASH, level=1)
        raid = spawn_enemy("Titan", EnemyTier.RAID_BOSS, level=60)
        assert raid.stats.attributes.vitality > trash.stats.attributes.vitality
        assert raid.xp_reward > trash.xp_reward
        assert raid.stats.resistances.immunity  # raid bosses have immunities

    def test_threat_and_taunt(self) -> None:
        enemy = spawn_enemy("Goblin", EnemyTier.TRASH, level=5)
        enemy.add_threat("dps", damage=100)
        enemy.add_threat("tank", flat=10, taunt=True)
        assert enemy.top_threat() == "tank"
        enemy.decay_threat(0.5)
        assert enemy.threat_table["dps"] == pytest.approx(50.0)

    def test_reflective_affix(self) -> None:
        enemy = spawn_enemy("Mirror Fiend", EnemyTier.ELITE, level=10)
        from pqcli.rpg.enemies import AffixId
        enemy.affixes.add(AffixId.REFLECTIVE)
        damage = enemy.take_hit(100, DamageType.PHYSICAL, attacker_level=10)
        assert enemy.reflected == pytest.approx(damage * 0.2)

    def test_death(self) -> None:
        enemy = spawn_enemy("Slime", EnemyTier.TRASH, level=1)
        enemy.take_hit(10**9, DamageType.TRUE if hasattr(DamageType, "TRUE") else DamageType.PHYSICAL)
        assert enemy.alive is False

    def test_ability_phase_gating(self) -> None:
        from pqcli.rpg.enemies import Ability
        enemy = spawn_enemy("Boss", EnemyTier.DUNGEON_BOSS, level=50)
        weak = Ability("a1", "Slash", power=50)
        ultimate = Ability("a2", "Annihilate", power=900, min_phase=2)
        enemy.abilities = [weak, ultimate]
        assert enemy.choose_ability(10.0, 0.5, phase=1) is weak
        assert enemy.choose_ability(10.0, 0.5, phase=2) is ultimate


class TestBossData:
    def test_scaling(self) -> None:
        boss = BossData(name="Dragon", base_hp=100_000, base_damage=500)
        normal = boss.scaled_hp(1, DifficultyTier.NORMAL)
        mythic = boss.scaled_hp(20, DifficultyTier.MYTHIC)
        assert mythic > normal * 10

    def test_phases(self) -> None:
        boss = BossData(name="Titan")
        assert boss.phases == []  # data-driven; defined per boss
        boss.enrage_timer = 600
        assert boss.enrage_timer == 600


# --------------------------------------------------------------------------- #
# Equipment                                                                    #
# --------------------------------------------------------------------------- #


def _sword() -> ItemDef:
    return ItemDef(
        id="ashen_blade", name="Ashen Blade", kind=ItemKind.WEAPON,
        slot=EquipmentSlot.MAIN_HAND, rarity=Rarity.EPIC, required_level=60,
        weapon_class=WeaponClass.LONGSWORD,
        pve=StatTable(
            base_stats={SubStatId.PHYSICAL_POWER.value: 200,
                        SubStatId.CRIT_CHANCE.value: 0.05},
            base_damage=1200, weapon_speed=1.1,
            element=DamageType.FIRE, element_damage=150,
            boss_damage_bonus=0.10,
            procs=[Proc("burn_proc", "burn", chance=0.25, dps_equivalent=300)],
        ),
        pvp=StatTable(
            base_stats={SubStatId.PHYSICAL_POWER.value: 100,
                        SubStatId.TENACITY.value: 50},
            base_damage=650, pvp_power=100, anti_heal=0.20,
        ),
    )


class TestEquipment:
    def test_pvp_pve_tables_differ(self) -> None:
        sword = _sword()
        assert sword.pve.base_damage != sword.pvp.base_damage
        assert sword.table(True) is sword.pvp
        assert sword.table(False) is sword.pve

    def test_pve_power_higher_with_procs(self) -> None:
        sword = _sword()
        assert sword.item_power(False) > sword.item_power(True)

    def test_equip_swap(self) -> None:
        mgr = _Manager()
        first = _sword()
        second = _sword()
        assert mgr.equip(first) is None
        assert mgr.equip(second) is first

    def test_gear_table_merge(self) -> None:
        mgr = _Manager()
        mgr.equip(_sword())
        table = mgr.gear_table(pvp=False)
        assert table[SubStatId.PHYSICAL_POWER.value] == pytest.approx(200)

    def test_gem_requires_equipped_host(self) -> None:
        mgr = _Manager()
        gem = ItemDef("ruby", "Ruby", ItemKind.GEM,
                      pve=StatTable(base_stats={"crit_chance": 0.02}))
        mgr.socket(EquipmentSlot.MAIN_HAND, gem)
        # No item equipped -> gem contributes nothing
        assert mgr.gear_table(False).get("crit_chance", 0.0) == 0.0
        mgr.equip(_sword())
        # sword base 0.05 + gem 0.02
        assert mgr.gear_table(False)["crit_chance"] == pytest.approx(0.07)

    def test_set_bonuses(self) -> None:
        mgr = _Manager()
        helm = ItemDef("s_h", "Set Helm", ItemKind.ARMOR,
                       slot=EquipmentSlot.HEAD, set_id="flame")
        chest = ItemDef("s_c", "Set Chest", ItemKind.ARMOR,
                        slot=EquipmentSlot.CHEST, set_id="flame")
        sets = {"flame": GearSet("flame", "Flame Guard", bonuses=[
            SetBonus("flame", 2, stats={"armor": 100}),
        ])}
        mgr.equip(helm)
        assert mgr.active_set_bonuses(sets) == []
        mgr.equip(chest)
        bonuses = mgr.active_set_bonuses(sets)
        assert len(bonuses) == 1
        assert bonuses[0].stats == {"armor": 100}

    def test_standard_slots_count(self) -> None:
        assert len(STANDARD_SLOTS) == 12


class _Manager:
    """Small shim: EquipmentManager is imported lazily to mirror real usage."""

    def __init__(self) -> None:
        from pqcli.rpg.equipment import EquipmentManager
        self._mgr = EquipmentManager()
        self.equipped = self._mgr.equipped

    def equip(self, item: ItemDef):
        return self._mgr.equip(item)

    def gear_table(self, pvp: bool):
        return self._mgr.gear_table(pvp)

    def socket(self, slot: EquipmentSlot, gem: ItemDef):
        return self._mgr.socket(slot, gem)

    def active_set_bonuses(self, sets):
        return self._mgr.active_set_bonuses(sets)
