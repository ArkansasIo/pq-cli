from pqcli.rpg.api.router import ApiRouter


def test_auth_router_round_trip() -> None:
    api = ApiRouter()
    registered = api.dispatch("POST", "/v1/auth/register", {"username": "alice", "password": "secret"})
    assert "account_id" in registered

    logged_in = api.dispatch("POST", "/v1/auth/login", {"username": "alice", "password": "secret"})
    assert logged_in["account_id"] == registered["account_id"]
    assert logged_in["token"]

    logged_out = api.dispatch("POST", "/v1/auth/logout", {"token": logged_in["token"]})
    assert logged_out == {"ok": True}


def test_unknown_route_is_structured_error() -> None:
    result = ApiRouter().dispatch("GET", "/v1/nope", {})
    assert result["code"] == "not_found"
