# RPG Content Catalog

The RPG layer now has a data-driven content boundary for:

- races and class archetypes
- level-scaled zones and biomes
- equipment rarity and slots
- quest objectives and rewards
- dungeons and raid group sizes
- future monsters, loot tables, recipes, factions, achievements, and world events

JSON content under `pqcli/data/` is intentionally separate from Python rules. Content can therefore be expanded without changing combat or progression algorithms.

## Planned content families

`races`, `classes`, `zones`, `biomes`, `monsters`, `bosses`, `items`, `affixes`, `recipes`, `professions`, `quests`, `factions`, `achievements`, `dungeons`, `raids`, `events`, `loot_tables`, and `localization`.
