"""Safe, versioned JSON serialization for the new RPG domain objects."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

SCHEMA_VERSION = 1


def encode_character(character: Any) -> dict[str, Any]:
    data = asdict(character)
    data["race"] = str(character.race)
    data["class_id"] = str(character.class_id)
    data["equipment"] = {str(k): v for k, v in character.equipment.items()}
    data["achievements"] = sorted(character.achievements)
    return data


def save_json(path: Path, characters: list[Any]) -> None:
    payload = {"schema_version": SCHEMA_VERSION, "characters": [encode_character(c) for c in characters]}
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        json.dump(payload, tmp, indent=2, sort_keys=True)
        tmp.write("\n")
        temp_path = Path(tmp.name)
    temp_path.replace(path)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("save root must be an object")
    version = payload.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ValueError(f"unsupported save schema version: {version!r}")
    if not isinstance(payload.get("characters"), list):
        raise ValueError("characters must be a list")
    return payload
