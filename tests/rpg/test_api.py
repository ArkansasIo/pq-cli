from pqcli.rpg.api.contracts import ErrorResponse, LoginRequest, LoginResponse


def test_api_contracts_are_serializable() -> None:
    assert LoginRequest("hero", "secret").to_dict()["username"] == "hero"
    assert LoginResponse("token", "account").to_dict()["api_version"] == "v1"
    assert ErrorResponse("bad_request", "invalid").to_dict()["code"] == "bad_request"
