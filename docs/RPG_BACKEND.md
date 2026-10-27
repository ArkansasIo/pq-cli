# RPG/MMORPG Backend

The RPG layer is organized as an authoritative service model rather than a client-authoritative simulation.

## Services

- `server.auth` — account registration, PBKDF2 password hashing, login sessions.
- `server.world` / `world_service` — world-server sessions, zones, weather and events.
- `server.permissions` — role-based authorization.
- `server.rate_limit` — per-key request throttling.
- `server.metrics` — counters and gauges for operational telemetry.
- `social_services` — parties and guilds.
- `trading` — two-party trade negotiation.
- `auction` — player auction listings.
- `mail` — player mail and item attachments.
- `pvp_services` — queueing and arena matchmaking.
- `instances` — dungeon/raid instance lifecycle.
- `quest_service` — persistent quest progression state.
- `inventory_service` — item and currency operations.
- `combat_service` — server-side combat resolution.
- `respawn` / `runtime` — mutable session state and death/respawn lifecycle.

## Transport

`pqcli.rpg.api` defines versioned contracts, envelopes, and a framework-neutral router. An HTTP framework or WebSocket server can adapt these objects without moving game rules into the transport layer.

## Persistence

`database.store.InMemoryStore` is intended for tests and local development. `database.postgres.PostgresCharacterStore` provides a small DB-API implementation for PostgreSQL. The SQL schema lives in `schema/mmorpg.sql`.

The RPG save format is versioned JSON. Legacy pickle saves remain a compatibility boundary and must only be opened when trusted.

## Scaling path

1. Keep game rules deterministic and authoritative.
2. Put sessions behind a gateway/load balancer.
3. Partition world state by zone or shard.
4. Persist durable character/economy transactions in PostgreSQL.
5. Add a durable event bus for cross-shard events.
6. Add observability, backups, rate limits, and administrative audit trails before public deployment.
