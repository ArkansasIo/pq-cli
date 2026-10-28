# RPG/MMORPG Framework Roadmap and Menu Specification

This plan extends the existing `pqcli/rpg/` domain layer and the Progress Quest-style browser game. It is a staged implementation plan, not a claim that every listed system is already playable. The legacy CLI and its save format must remain intact while integration proceeds.

## 1. Player-facing menu tree

- **Adventure**
  - Overview, Autobattle, Combat Log, Rest, Battle Speed, Combat Priority
- **Character**
  - Summary, 10 Primary Attributes, Derived Stats, Resistances, Resources
  - Race/Species, Class, Subclass, Background, Alignment/Roleplay Notes
  - Talent Trees, Skill Training, Achievements, Reputation
- **Inventory**
  - All Items, Equipment, Materials, Consumables, Quest Items, Currency
  - Filters by type/rarity/slot; sort; compare; use; equip; unequip; sell
- **Equipment**
  - Weapon, Offhand, Head, Chest, Hands, Legs, Feet, Amulet, Rings
  - Item comparison, stat totals, rarity, durability/repair where implemented
- **Skills & Magic**
  - Active Skills, Passive Skills, Spellbook, Spell Slots/Resources, Skill Bar
  - Cooldowns, upgrades, loadouts, class/subclass unlocks
- **World**
  - World Map, Zones, Biomes, Encounters, Gathering, Dynamic Events
  - Waypoints, Travel, Exploration Progress
- **Activities**
  - Dungeons, Trials, Raids, Bosses, Challenge Tower, Repeatable Expeditions
  - Single-player mode, party mode, multiplayer queue
- **Quests & Story**
  - Main Campaign, Side Quests, Daily/Weekly Objectives, Quest Journal
  - Dialogue, Story Choices, Chapter Progress, Lore, Rewards
- **Crafting & Trade**
  - Professions, Recipes, Gathering, Crafting Queue, Tempering/Masterworking
  - Enchanting, Repair, Player Market, Vendor, Currency Exchange
- **Social**
  - Party, Friends, Guilds/Alliances, Chat, Invitations, Block List
- **PvP**
  - Duel, Arena, Seasonal Rating, Leaderboards, Match History
- **Collections**
  - Mounts, Pets, Cosmetics, Titles, Bestiary, Discovered Lore
- **System**
  - Settings, Accessibility, Save/Load, Export/Import, Account, Connection Status

Menu items for server-only features must show a clear "requires multiplayer server" state until that backend is actually deployed.

## 2. Modes and session rules

### Single-player
- Local autobattle and manual character management.
- Browser save is versioned and stored locally; export/import for backup.
- Dungeons, story, crafting, loot, and quests can run locally.
- No claim of shared market, real-time chat, guild synchronization, or persistent online world.

### Party/co-op multiplayer
- Party creation, invite/accept, roles, formation, ready checks, instance entry.
- Server validates player identity, party membership, rewards, inventory changes, and combat results.
- Reconnect/resume and disconnect handling; do not trust client-sent damage or loot.

### Dungeons and trials
- Instance definitions include recommended level, entry requirements, encounter list, boss, reward table, reset policy, and completion state.
- Trials emphasize timed/skill challenges, phases, modifiers, and score records.
- Solo mode scales encounter numbers and stats; party mode uses server-authoritative scaling.
- Clear failure, revive, retreat, and completion flows.

### Raids
- Multi-boss instance with phases, telegraphs, role mechanics, checkpoints, loot rules, and lockout policy.
- Party size and roles are configurable by encounter definition.
- Raid content remains disabled in multiplayer until authoritative server and group synchronization exist.

## 3. Existing domain modules to wire into UI

| Domain | Existing module | UI surface |
|---|---|---|
| Attributes and derived combat stats | `stats.py` | Character / Stats |
| Character identity and progression | `character.py` | Character / Progression |
| Item and inventory definitions | `items.py` | Inventory / Equipment |
| Combat resolution | `combat.py` | Autobattle / Combat Log |
| Skills and talent trees | `skills.py`, `progression.py` | Skills / Talents |
| Quests and story state | `quests.py`, browser story module | Quest Journal / Campaign |
| Crafting | `crafting.py` | Crafting / Professions |
| Zones, biomes, instances | `world.py`, `dungeons.py` | World / Activities |
| Loot | `loot.py` | Loot / Rewards |
| Currency and marketplace | `economy.py` | Trade / Market |
| Friends, parties, guilds | `social.py` | Social |
| PvP ratings | `pvp.py` | PvP / Leaderboards |
| Achievements, factions, events, mounts | corresponding modules | Collections / World |
| Sessions, matchmaking, persistence | `mmorpg.py`, `persistence.py` | System / Connection |

## 4. Backend and data architecture

1. **Domain layer:** pure game rules, definitions, validation, and deterministic tests.
2. **Application services:** character, combat, inventory, quest, crafting, party, and instance use-cases.
3. **API boundary:** versioned REST endpoints for accounts, characters, inventories, quests, crafting, and matchmaking; WebSocket events for live parties, combat feeds, and chat.
4. **Persistence:** SQLite for development/single-user tests; MySQL or PostgreSQL for a deployed service. Store migrations and backups.
5. **Security:** server-side authorization, rate limits, input validation, transaction-safe rewards, inventory anti-duplication, audit logs, and secret management.
6. **Browser client:** renders menus and sends player intentions; server decides multiplayer state. Static GitHub Pages alone cannot host this server.

## 5. Data contracts to define

- `CharacterState`: schema version, identity, race/class/subclass, attributes, derived stats, resources, XP/level, skills/talents, inventory/equipment.
- `EncounterDefinition`: enemy roster, level range, biome, damage types, AI priorities, loot table, difficulty modifiers.
- `ActivityDefinition`: activity type, requirements, party-size range, phases, checkpoints, rewards, reset rules.
- `QuestDefinition`: prerequisites, objectives, branching choices, completion flags, rewards, repeat policy.
- `ItemDefinition`: slot/type, rarity, level, stats, affixes, stack rules, trade/bind rules.
- `SessionState`: session id, player ids, party, instance, start time, heartbeat, reconnect window.
- `RewardGrant`: unique idempotency key, source activity, XP, currency, items, validation status.

## 6. Milestones and acceptance checks

1. **Framework parity:** browser attributes and combat formulas match Python `stats.py`; test every derived-stat formula and boundaries.
2. **Core UI:** character, inventory, equipment, skills, world, quest, crafting, settings screens operate against one save model.
3. **PvE activities:** encounter definitions, dungeons, boss phases, loot, failure/retry and reward grants work in solo mode.
4. **Story integration:** original branching campaign objectives read/write the same quest state; choices and rewards persist.
5. **Social systems:** local party/guild screens first; server-backed invitations and chat only after API deployment.
6. **Backend:** API, SQL migrations, authentication, authoritative combat, and persistence.
7. **Multiplayer validation:** reconnect, duplicate reward prevention, unauthorized actions, party/instance consistency, and load tests.
8. **Release:** automated tests, accessibility/mobile checks, GitHub Pages smoke test, and separate backend deployment health check.

## 7. Current state and constraints

The repository already documents a broad Python RPG/MMORPG domain layer. The browser companion has additional framework and original story files, but the browser client is not yet fully integrated with every Python module. A menu is not proof that its online feature is implemented. GitHub Pages can host the client and static data; a separate running server is required for real multiplayer, shared MySQL data, accounts, chat, parties, raids, and a persistent world.
