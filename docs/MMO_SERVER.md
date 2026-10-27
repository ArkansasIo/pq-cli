# MMORPG Server Architecture

## Layers

- **Client/UI:** existing CLI interfaces and future web/mobile clients.
- **Domain:** `pqcli.rpg` contains deterministic game rules and state models.
- **World server:** `pqcli.rpg.server.world.GameServer` is the authoritative session boundary.
- **Authentication:** `AuthService` owns account registration, password verification, and session tokens.
- **Persistence:** `pqcli.rpg.database` provides storage interfaces; `schema/mmorpg.sql` defines a PostgreSQL-compatible persistence model.
- **API contracts:** `pqcli.rpg.api` provides versioned transport-independent request/response objects.

## Authoritative rules

The server must validate character mutations, inventory changes, rewards, currency transfers, quest completion, and PvP results. Clients should send intents rather than authoritative state changes.

## Scaling path

1. Run one world server with the in-memory store.
2. Add PostgreSQL-backed `CharacterStore`.
3. Add a network adapter around the API contracts.
4. Add a message broker for cross-server events.
5. Partition zones across world-server processes.
6. Add instance servers and matchmaking workers.
7. Add observability, rate limiting, moderation, and backups.

The current implementation deliberately stops before introducing a third-party networking dependency, keeping the core package usable offline and from the CLI.
