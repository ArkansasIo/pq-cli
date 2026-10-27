from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CharacterStore(ABC):
    @abstractmethod
    def put(self, character_id: str, payload: dict[str, Any]) -> None: ...

    @abstractmethod
    def get(self, character_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def delete(self, character_id: str) -> None: ...


class InMemoryStore(CharacterStore):
    """Reference store used by tests and local development."""

    def __init__(self) -> None:
        self._characters: dict[str, dict[str, Any]] = {}

    def put(self, character_id: str, payload: dict[str, Any]) -> None:
        self._characters[character_id] = dict(payload)

    def get(self, character_id: str) -> dict[str, Any] | None:
        value = self._characters.get(character_id)
        return dict(value) if value is not None else None

    def delete(self, character_id: str) -> None:
        self._characters.pop(character_id, None)
