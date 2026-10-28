# Fifth-Edition-Compatible Rules and Story Mode

This project uses the published System Reference Document (SRD) as the reference point for rules that can be reused in a browser game. It does not scan, reproduce, or bundle entire commercial rulebooks or adventure guides.

## Official rules sources

- **SRD 5.2.1** is the current 2024-rules-based SRD shown on the official D&D Beyond SRD page. It is released under Creative Commons Attribution 4.0 (CC BY 4.0).
- **SRD 5.1** remains available for the original 2014 fifth-edition rules. Choose one rules profile for a campaign instead of silently mixing versions.
- The SRD is not the complete Player's Handbook, Dungeon Master's Guide, Monster Manual, or published adventure catalogue. Content excluded from the SRD must not be assumed to be open-licensed.

References:
- https://www.dndbeyond.com/srd
- https://www.dndbeyond.com/creator-faq
- https://creativecommons.org/licenses/by/4.0/

## Required SRD 5.2 attribution

If this build incorporates SRD 5.2 material, include this attribution in the distribution:

> This work includes material from the System Reference Document 5.2 (“SRD 5.2”) by Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2 is licensed under the Creative Commons Attribution 4.0 International License, available at https://creativecommons.org/licenses/by/4.0/legalcode.

Do not imply that Wizards of the Coast endorses this project.

## Rules framework scope

The browser rules layer is intended to provide data-driven building blocks for:

- Character creation, species/race profiles, class and subclass profiles, backgrounds, ability scores, proficiency, and saving throws.
- D20 checks, attack rolls, advantage/disadvantage, critical results, armor class, hit points, temporary hit points, death and recovery.
- Spellcasting resources, spell definitions, spell slots, prepared/known spells, conditions, damage types, resistance, vulnerability, and saving throws.
- Feats, equipment slots, rarity, item properties, consumables, loot tables, crafting recipes, professions, and currency.
- Experience, levels, proficiency progression, talent trees, skills, quests, achievements, faction reputation, zones, encounters, dungeons, raids, and event schedules.
- Party roles, formation, guild/social records, marketplace concepts, PvP rating, mounts, and versioned save data.

The existing `pqcli/rpg/` Python package remains the primary domain implementation. The `docs/rpg-framework.js` file is a browser-side companion model, not yet a remote API client or a complete one-to-one port of every Python module. Keep shared rule definitions versioned and add parity tests before claiming exact equivalence.

## Story-mode policy and architecture

The browser campaign **The Shattered Accord** is original content. It has four chapters, objective tracking, branching choices, rewards, and reputation flags. It is designed to use fifth-edition-compatible check concepts while avoiding copied text, maps, encounters, characters, or storylines from paid adventure books.

A future campaign-import tool may index user-provided, legally obtained reference material for private lookup, but should not redistribute book text or assets. For a publishable game, use SRD content where licensed and write original settings, dialogue, quests, maps, and encounters. Do not scrape or package entire commercial books.

## Integration stages

1. Keep the browser game playable without a server.
2. Adopt the shared stat and combat formulas for character sheets and autobattle.
3. Add SRD-versioned rules data and automated formula tests.
4. Connect quests, inventory, crafting, zones, dungeons, and story progress to one versioned save model.
5. Add a server API and authoritative persistence only when multiplayer or cross-device saves are implemented.
