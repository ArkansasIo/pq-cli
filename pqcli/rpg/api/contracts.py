from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

API_VERSION = "v1"


@dataclass(frozen=True)
class LoginRequest:
    username: str
    password: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LoginResponse:
    token: str
    account_id: str
    api_version: str = API_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ErrorResponse:
    code: str
    message: str
    api_version: str = API_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
