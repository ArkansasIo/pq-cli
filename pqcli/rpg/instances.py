from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Instance:
    instance_id: str
    content_id: str
    difficulty: str
    party_ids: list[str] = field(default_factory=list)
    state: str = "created"
    boss_defeated: bool = False

    def start(self) -> None:
        self.state = "active"

    def complete(self) -> None:
        self.state = "completed"

    def fail(self) -> None:
        self.state = "failed"


class InstanceService:
    def __init__(self) -> None:
        self.instances: dict[str, Instance] = {}

    def create(self, content_id: str, difficulty: str, party_ids: list[str]) -> Instance:
        instance = Instance(str(uuid4()), content_id, difficulty, list(party_ids))
        self.instances[instance.instance_id] = instance
        return instance

    def get(self, instance_id: str) -> Instance | None:
        return self.instances.get(instance_id)
