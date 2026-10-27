from pqcli.rpg.mmorpg import PlayerSession
from pqcli.rpg.server.auth import AuthService
from pqcli.rpg.server.world import GameServer, ServerConfig


def test_auth_register_and_login() -> None:
    auth = AuthService()
    account = auth.register("a1", "hero", "correct horse")
    token = auth.login("hero", "correct horse")
    assert auth.account_for(token) == account


def test_world_server_capacity() -> None:
    server = GameServer(ServerConfig("test", capacity=1))
    server.start()
    server.connect(PlayerSession("s1", "a1", "c1"))
    try:
        server.connect(PlayerSession("s2", "a2", "c2"))
    except RuntimeError as exc:
        assert str(exc) == "server is full"
    else:
        raise AssertionError("expected server-full error")
