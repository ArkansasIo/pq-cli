from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Envelope:
    request_id: str
    action: str
    payload: dict[str, Any]
    version: str = "v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "request_id": self.request_id,
            "action": self.action,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Envelope":
        if value.get("version") != "v1":
            raise ValueError("unsupported protocol version")
        if not isinstance(value.get("request_id"), str) or not isinstance(value.get("action"), str):
            raise ValueError("request_id and action are required")
        payload = value.get("payload", {})
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        return cls(value["request_id"], value["action"], payload)
