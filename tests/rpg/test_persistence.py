from pathlib import Path

import pytest

from pqcli.rpg.character import Character
from pqcli.rpg.persistence import SCHEMA_VERSION, load_json, save_json


def test_versioned_json_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "save.json"
    save_json(path, [Character("Aris")])
    data = load_json(path)
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["characters"][0]["name"] == "Aris"


def test_unknown_schema_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"schema_version": 999, "characters": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported save schema"):
        load_json(path)
