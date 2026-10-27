"""End-to-end tests for the RPG API app (in-process, real HTTP)."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from pqcli.rpg.api.app import ApiApp, make_handler


@pytest.fixture()
def base_url() -> str:
    app = ApiApp()
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    thread.join(timeout=2)


def _request(
    base_url: str, method: str, path: str,
    body: dict | None = None, token: str | None = None,
) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        base_url + path, data=data, method=method,
        headers={"Content-Type": "application/json",
                 **({"Authorization": f"Bearer {token}"} if token else {})},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _register_and_login(base_url: str, username: str) -> str:
    status, _ = _request(base_url, "POST", "/v1/auth/register",
                         {"username": username, "password": "hunter2"})
    assert status == 200
    status, body = _request(base_url, "POST", "/v1/auth/login",
                            {"username": username, "password": "hunter2"})
    assert status == 200
    return body["token"]


class TestHealthAndAuth:
    def test_health(self, base_url: str) -> None:
        status, body = _request(base_url, "GET", "/health")
        assert status == 200
        assert body["status"] == "ok"

    def test_register_login_logout(self, base_url: str) -> None:
        token = _register_and_login(base_url, "alice")
        assert token
        status, body = _request(base_url, "POST", "/v1/auth/logout",
                                {"token": token})
        assert status == 200 and body["ok"] is True

    def test_bad_login_rejected(self, base_url: str) -> None:
        _request(base_url, "POST", "/v1/auth/register",
                 {"username": "bob", "password": "pw"})
        status, body = _request(base_url, "POST", "/v1/auth/login",
                                {"username": "bob", "password": "wrong"})
        assert status == 400
        assert body["code"] == "bad_request"


class TestCharacters:
    def test_create_and_get(self, base_url: str) -> None:
        status, body = _request(base_url, "POST", "/v1/characters",
                                {"name": "Grumdrig", "race": "orc",
                                 "class_id": "warrior"})
        assert status == 201
        char_id = body["id"]

        status, body = _request(base_url, "GET", f"/v1/characters/{char_id}")
        assert status == 200
        assert body["name"] == "Grumdrig"
        assert body["race"] == "orc"
        assert body["combat"]["max_hp"] > 0

    def test_unknown_character_404(self, base_url: str) -> None:
        status, body = _request(base_url, "GET", "/v1/characters/nope")
        assert status == 404
        assert body["code"] == "not_found"

    def test_list_requires_token(self, base_url: str) -> None:
        status, body = _request(base_url, "GET", "/v1/characters")
        assert status == 401
        assert body["code"] == "unauthorized"

    def test_list_with_token(self, base_url: str) -> None:
        token = _register_and_login(base_url, "carol")
        _request(base_url, "POST", "/v1/characters", {"name": "A"})
        _request(base_url, "POST", "/v1/characters", {"name": "B"})
        status, body = _request(base_url, "GET", "/v1/characters", token=token)
        assert status == 200
        assert {c["name"] for c in body["characters"]} == {"A", "B"}

    def test_grant_xp_levels_up(self, base_url: str) -> None:
        _, created = _request(base_url, "POST", "/v1/characters",
                              {"name": "Grinder"})
        char_id = created["id"]
        status, body = _request(base_url, "POST",
                                f"/v1/characters/{char_id}/grant-xp",
                                {"amount": 10_000})
        assert status == 200
        assert body["levels_gained"] > 0
        assert body["level"] > 1


class TestCombat:
    def test_combat_vs_trash(self, base_url: str) -> None:
        _, created = _request(base_url, "POST", "/v1/characters",
                              {"name": "Fighter", "race": "orc"})
        char_id = created["id"]
        _request(base_url, "POST", f"/v1/characters/{char_id}/grant-xp",
                 {"amount": 50_000})
        status, body = _request(base_url, "POST",
                                f"/v1/characters/{char_id}/combat",
                                {"enemy_tier": "trash", "enemy_rank": "normal"})
        assert status == 200
        assert body["rounds"] > 0
        assert body["log"]
        assert isinstance(body["victory"], bool)

    def test_combat_bad_tier(self, base_url: str) -> None:
        _, created = _request(base_url, "POST", "/v1/characters",
                              {"name": "V"})
        status, body = _request(base_url, "POST",
                                f"/v1/characters/{created['id']}/combat",
                                {"enemy_tier": "not-a-tier"})
        assert status == 400


class TestReference:
    def test_enemies_reference(self, base_url: str) -> None:
        status, body = _request(base_url, "GET", "/v1/enemies")
        assert status == 200
        assert "trash" in body["tiers"]
        assert body["ranks"]["ascended"] > body["ranks"]["normal"]

    def test_catalog_list_and_item(self, base_url: str) -> None:
        status, body = _request(base_url, "GET", "/v1/catalog")
        assert status == 200
        assert len(body["items"]) >= 12
        ids = {item["id"] for item in body["items"]}
        assert "ashen_blade" in ids

        status, body = _request(base_url, "GET", "/v1/catalog/ashen_blade")
        assert status == 200
        assert body["pve"]["procs"]  # PvE procs present
        assert body["pvp"]["base_damage"] < body["pve"]["base_damage"]

    def test_catalog_unknown_item(self, base_url: str) -> None:
        status, _ = _request(base_url, "GET", "/v1/catalog/nope")
        assert status == 404
