# RPG/MMORPG Framework

The repository now contains an additive RPG/MMORPG domain layer under `pqcli/rpg/`.
It is independent from the legacy Progress Quest simulation so existing gameplay can continue while systems are integrated incrementally.

## Implemented modules

- `enums.py` — races, classes, damage types, rarity, equipment slots, quests, faction standing.
- `stats.py` — primary attributes, derived combat statistics, resource pools.
- `character.py` — persistent character identity, progression, race bonuses, inventory, equipment, skills, talents, reputation, achievements.
- `items.py` — item definitions, equipment stats, inventory stacks, currencies.
- `combat.py` — hit, dodge, mitigation, critical, block, damage and defeat resolution.
- `quests.py` — objectives, quest state and quest log.
- `crafting.py` — professions, recipes and ingredient validation.
- `world.py` — biomes, zones and level filtering.
- `dungeons.py` — encounters, dungeons, raids and instances.
- `loot.py` — weighted loot tables.
- `economy.py` — wallets, market orders and player marketplace.
- `social.py` — parties, guilds, friends and blocking.
- `pvp.py` — ratings, seasons and leaderboards.
- `progression.py` — talent trees and talent points.
- `skills.py` — skill training and levels.
- `achievements.py` — achievement definitions and points.
- `factions.py` — reputation and faction standings.
- `events.py` — dynamic world events.
- `mounts.py` — mount collection and summoning.
- `mmorpg.py` — sessions, world-server capacity and matchmaking queues.
- `persistence.py` — versioned JSON persistence with schema validation and atomic replacement.

## Integration roadmap

1. Connect the character model to the existing roster.
2. Add explicit CLI commands for RPG character management.
3. Add legacy-save migration into the versioned JSON format.
4. Move item, quest, enemy and world definitions into data files.
5. Add server/API adapters around the pure domain layer.
6. Add database persistence and authentication at the service boundary.
7. Add multiplayer synchronization and authoritative server rules.

The current modules intentionally avoid introducing a database or network dependency into the core package. This keeps unit tests fast and permits the same domain logic to be used by the CLI, an HTTP API, or a future dedicated game server.
