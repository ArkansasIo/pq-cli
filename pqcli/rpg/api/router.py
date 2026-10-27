from __future__ import annotations

from dataclasses import asdict
from typing import Callable

from .contracts import ErrorResponse, LoginRequest, LoginResponse
from ..server.auth import AuthService


class ApiRouter:
    """Framework-neutral request router suitable for HTTP or WebSocket adapters."""

    def __init__(self, auth: AuthService | None = None) -> None:
        self.auth = auth or AuthService()
        self.routes: dict[tuple[str, str], Callable[[dict], dict]] = {
            ("POST", "/v1/auth/register"): self.register,
            ("POST", "/v1/auth/login"): self.login,
            ("POST", "/v1/auth/logout"): self.logout,
        }

    def dispatch(self, method: str, path: str, body: dict) -> dict:
        handler = self.routes.get((method.upper(), path))
        if handler is None:
            return ErrorResponse("not_found", "route not found").to_dict()
        try:
            return handler(body)
        except (ValueError, KeyError) as exc:
            return ErrorResponse("bad_request", str(exc)).to_dict()

    def register(self, body: dict) -> dict:
        account = self.auth.register(str(body["username"]), str(body["password"]))
        return {"account_id": account.account_id}

    def login(self, body: dict) -> dict:
        request = LoginRequest(str(body["username"]), str(body["password"]))
        account, token = self.auth.login(request.username, request.password)
        return LoginResponse(token, account.account_id).to_dict()

    def logout(self, body: dict) -> dict:
        self.auth.logout(str(body["token"]))
        return {"ok": True}
