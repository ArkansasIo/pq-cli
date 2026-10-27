"""RPG API application: character, combat, enemy and catalog endpoints.

A dependency-free HTTP JSON API built on the stdlib ``http.server``, wrapping
the RPG domain (``pqcli.rpg``). The existing framework-neutral ``ApiRouter``
keeps auth routes; this module adds game routes and serves the whole thing.

Run it:

    uv run python -m pqcli.rpg.api.app --port 8420

Endpoints:

    GET  /health
    POST /v1/auth/register        {username, password}
    POST /v1/auth/login           {username, password}
    POST /v1/auth/logout          {token}
    GET  /v1/characters           (Authorization: Bearer <token>)
    POST /v1/characters           {name, race, class_id}
    GET  /v1/characters/{id}
    POST /v1/characters/{id}/grant-xp   {amount}
    POST /v1/characters/{id}/combat     {enemy_tier, enemy_rank}
    GET  /v1/enemies
    GET  /v1/catalog
    GET  /v1/catalog/{item_id}
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from ..character import Character
from ..combat import Attack, CombatEngine
from ..enemies import (
    RANK_MULTIPLIERS,
    TIER_BASELINES,
    AIRole,
    EnemyRank,
    EnemyTier,
    spawn_enemy,
)
from ..enums import ClassId, RaceId
from ..server.auth import AuthService
from .contracts import API_VERSION, ErrorResponse
from .router import ApiRouter

AUTH_BEARER_PREFIX = "Bearer "


class ApiApp:
    """Application state + route handlers over the RPG domain."""

    def __init__(self) -> None:
        self.auth = AuthService()
        self.characters: dict[str, Character] = {}
        self.combat = CombatEngine()
        # Auth routes reuse the framework-neutral router.
        self._auth_router = ApiRouter(auth=self.auth)

    # -- helpers ------------------------------------------------------------- #

    def account_for_request(self, headers: dict[str, str]) -> str | None:
        header = headers.get("Authorization", "")
        if not header.startswith(AUTH_BEARER_PREFIX):
            return None
        token = header[len(AUTH_BEARER_PREFIX):]
        account = self.auth.account_for(token)
        return account.account_id if account else None

    # -- game routes --------------------------------------------------------- #

    def list_characters(self, headers: dict[str, str]) -> tuple[dict, int]:
        account_id = self.account_for_request(headers)
        if account_id is None:
            return ErrorResponse("unauthorized", "missing or invalid token").to_dict(), 401
        chars = [
            {"id": c.id, "name": c.name, "level": c.level, "race": c.race.value,
             "class": c.class_id.value}
            for c in self.characters.values()
        ]
        return {"characters": chars}, 200

    def create_character(self, body: dict) -> tuple[dict, int]:
        try:
            name = str(body["name"])
            race = RaceId(body.get("race", RaceId.HUMAN.value))
            class_id = ClassId(body.get("class_id", ClassId.WARRIOR.value))
        except (KeyError, ValueError) as exc:
            return ErrorResponse("bad_request", str(exc)).to_dict(), 400
        character = Character(name=name, race=race, class_id=class_id)
        self.characters[character.id] = character
        return {"id": character.id, "name": character.name,
                "level": character.level}, 201

    def get_character(self, character_id: str) -> tuple[dict, int]:
        character = self.characters.get(character_id)
        if character is None:
            return ErrorResponse("not_found", "character not found").to_dict(), 404
        stats = character.combat_stats
        return {
            "id": character.id, "name": character.name, "level": character.level,
            "xp": character.xp, "race": character.race.value,
            "class": character.class_id.value,
            "stats": asdict(character.attributes),
            "combat": {"max_hp": stats.max_hp, "max_mp": stats.max_mp,
                       "attack": stats.attack, "armor": stats.armor,
                       "crit_chance": stats.crit_chance},
        }, 200

    def grant_xp(self, character_id: str, body: dict) -> tuple[dict, int]:
        character = self.characters.get(character_id)
        if character is None:
            return ErrorResponse("not_found", "character not found").to_dict(), 404
        amount = int(body.get("amount", 0))
        levels = character.grant_xp(amount)
        return {"id": character.id, "xp": character.xp,
                "level": character.level, "levels_gained": levels}, 200

    def run_combat(self, character_id: str, body: dict) -> tuple[dict, int]:
        character = self.characters.get(character_id)
        if character is None:
            return ErrorResponse("not_found", "character not found").to_dict(), 404
        try:
            tier = EnemyTier(body.get("enemy_tier", EnemyTier.TRASH.value))
            rank = EnemyRank(body.get("enemy_rank", EnemyRank.NORMAL.value))
        except ValueError as exc:
            return ErrorResponse("bad_request", str(exc)).to_dict(), 400
        enemy = spawn_enemy(
            body.get("enemy_name", "Opponent"), tier, rank,
            level=max(1, character.level), ai_role=AIRole.BRUTE,
        )
        player_stats = character.combat_stats
        player_resources = character.resources
        log: list[str] = []
        rounds = 0
        while player_resources.hp > 0 and enemy.alive and rounds < 100:
            rounds += 1
            result = self.combat.resolve(
                Attack(character.name, enemy.name, power=10),
                player_stats, enemy.stats.combat_proxy(),
                enemy.stats.resources,
            )
            log.extend(result.log)
            if enemy.alive and player_resources.hp > 0:
                counter = self.combat.resolve(
                    Attack(enemy.name, character.name,
                           power=int(TIER_BASELINES[tier] * 5)),
                    enemy.stats.combat_proxy(), player_stats, player_resources,
                )
                log.extend(counter.log)
        return {
            "victory": player_resources.hp > 0 and not enemy.alive,
            "rounds": rounds,
            "player_hp": player_resources.hp,
            "enemy_alive": enemy.alive,
            "log": log,
        }, 200

    def list_enemies(self) -> tuple[dict, int]:
        return {
            "tiers": {t.value: TIER_BASELINES[t] for t in EnemyTier},
            "ranks": {r.value: RANK_MULTIPLIERS[r] for r in EnemyRank},
        }, 200

    def list_catalog(self) -> tuple[dict, int]:
        from ..catalog import CATALOG
        items = []
        for item in CATALOG.values():
            items.append({
                "id": item.id, "name": item.name, "kind": item.kind.value,
                "rarity": item.rarity.value, "level": item.required_level,
                "pve_power": round(item.item_power(False), 1),
                "pvp_power": round(item.item_power(True), 1),
            })
        return {"items": items}, 200

    def get_catalog_item(self, item_id: str) -> tuple[dict, int]:
        from ..catalog import CATALOG
        item = CATALOG.get(item_id)
        if item is None:
            return ErrorResponse("not_found", "item not found").to_dict(), 404
        return {
            "id": item.id, "name": item.name, "kind": item.kind.value,
            "rarity": item.rarity.value, "slot": item.slot.value if item.slot else None,
            "pve": {"base_damage": item.pve.base_damage,
                    "stats": item.pve.base_stats,
                    "procs": [p.id for p in item.pve.procs]},
            "pvp": {"base_damage": item.pvp.base_damage,
                    "stats": item.pvp.base_stats,
                    "pvp_power": item.pvp.pvp_power},
            "pve_power": round(item.item_power(False), 1),
            "pvp_power": round(item.item_power(True), 1),
        }, 200


def make_handler(app: ApiApp) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, payload: dict, status: int = 200) -> None:
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_body(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                return {}
            try:
                return json.loads(self.rfile.read(length))
            except json.JSONDecodeError:
                return {}

        def _dispatch(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            method = self.command

            if path == "/health":
                self._send({"status": "ok", "api_version": API_VERSION})
                return

            # Auth routes via the framework-neutral router.
            if (method, path) in app._auth_router.routes:
                result = app._auth_router.dispatch(method, path, self._read_body())
                status = 400 if result.get("code") == "bad_request" else 200
                self._send(result, status)
                return

            # Game routes.
            try:
                if method == "GET" and path == "/v1/characters":
                    payload, status = app.list_characters(dict(self.headers))
                elif method == "POST" and path == "/v1/characters":
                    payload, status = app.create_character(self._read_body())
                elif path.startswith("/v1/characters/"):
                    remainder = path[len("/v1/characters/"):]
                    parts = remainder.split("/")
                    if len(parts) == 1:
                        payload, status = app.get_character(parts[0])
                    elif len(parts) == 2 and parts[1] == "grant-xp":
                        payload, status = app.grant_xp(parts[0], self._read_body())
                    elif len(parts) == 2 and parts[1] == "combat":
                        payload, status = app.run_combat(parts[0], self._read_body())
                    else:
                        payload, status = ErrorResponse(
                            "not_found", "route not found").to_dict(), 404
                elif method == "GET" and path == "/v1/enemies":
                    payload, status = app.list_enemies()
                elif method == "GET" and path == "/v1/catalog":
                    payload, status = app.list_catalog()
                elif method == "GET" and path.startswith("/v1/catalog/"):
                    payload, status = app.get_catalog_item(
                        path[len("/v1/catalog/"):])
                else:
                    payload, status = ErrorResponse(
                        "not_found", "route not found").to_dict(), 404
            except (ValueError, KeyError) as exc:
                payload, status = ErrorResponse("bad_request", str(exc)).to_dict(), 400
            self._send(payload, status)

        do_GET = do_POST = _dispatch

        def log_message(self, fmt: str, *args: Any) -> None:  # quiet
            pass

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="pqcli RPG API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8420)
    args = parser.parse_args()

    app = ApiApp()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(app))
    print(f"pqcli RPG API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
