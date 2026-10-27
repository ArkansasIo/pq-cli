# RPG Stat Framework

Layered MMORPG stat system: attributes → sub-attributes → combat stats →
resources, with buffs/debuffs, enemies/bosses, AI, encounter templates and
PvE/PvP-split equipment. All modules live in `pqcli/rpg/` and are covered by
`tests/rpg/`.

## Modules

| Module           | Layer                                                          |
| ---------------- | -------------------------------------------------------------- |
| `stat_framework` | Core attributes, sub-attributes, formulas, resources, resistances, scaling |
| `effects`        | Buffs/debuffs: stacking, CC diminishing returns, cleanse, immunity |
| `enemies`        | Mob taxonomy, ranks, affixes, threat/aggro, boss data, loot     |
| `ai`             | Enemy state machine (`Idle → Patrol → Alert → Engage → Combat → Retreat → Reset`) and combat sub-states |
| `encounters`     | Reusable open-world / dungeon / raid encounter templates        |
| `equipment`      | Dual-table items (PvE + PvP), gems, gear sets, 12 slots         |
| `catalog`        | Starter catalog: 12 example items with separate PvE/PvP tables  |

## Quick start

```python
from pqcli.rpg import StatBlock, SubStatId, spawn_enemy, EnemyTier, EnemyRank
from pqcli.rpg.enums import DamageType
from pqcli.rpg.effects import BUILT_IN_EFFECTS, EffectHost, CleanseType

hero = StatBlock()
hero.attributes.strength = 50
hero.gear["crit_chance"] = 0.15
hero.recompute()

slime = spawn_enemy("Slime", EnemyTier.TRASH, EnemyRank.VETERAN, level=10)
damage = hero.take_damage(120, DamageType.PHYSICAL, attacker_level=10)

host = EffectHost("hero")
host.apply(BUILT_IN_EFFECTS["burn"])   # DoT, stacks up to 3
host.cleanse(CleanseType.PHYSICAL)
```

## Key formulas

- `Mitigation = Armor / (Armor + K * AttackerLevel)`
- `DamageTaken = Raw * (1 - Mitigation) * (1 - Resist%) * Vulnerability`
- `BossHP = Base * (1 + LevelDiff*0.18) * PartyMult * TierMult` where
  `PartyMult = 1 + (Players-1)*0.65`
- `BossDamage = Base * (1 + LevelDiff*0.12) * TierMult` (damage scales slower
  than HP on purpose)
- `Threat = Damage*Mult + Healing*0.5 + Flat + TauntOverride`
- `CC DR`: 1st application 100%, 2nd 50%, 3rd 25%, then immune (10s window)

## PvE vs PvP

Every item carries two `StatTable`s; procs are PvE-only. PvP applies
`PVP_MULTIPLIERS` (damage ×0.70, crit ×0.50, healing ×0.65, armor ×1.10) and
`HARD_CAPS` (crit 70% PvE / 40% PvP, CDR 60% / 35%). The starter catalog
demonstrates the pattern: the *Ashen Blade* has a PvE burn proc and boss bonus
while its PvP table gets normalized damage, PvP Power and anti-heal instead.

## Extending

- New sub-stat: add it to `SubStatId`, map a category in
  `SUB_STAT_CATEGORIES`, and (optionally) a derived formula in
  `_DERIVED_FORMULAS` plus a weight in `STAT_WEIGHTS`.
- New effect: append an `EffectDef` to `BUILT_IN_EFFECTS` in `effects.py`.
- New encounter: add an `EncounterTemplate` to `BUILT_IN_TEMPLATES` in
  `encounters.py`.
- New boss: fill in a `BossData` (phases, abilities, immunities, affixes,
  loot, enrage rules) — it is plain data, so it can later be loaded from JSON.
