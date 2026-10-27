from dataclasses import dataclass, field


@dataclass
class Party:
    id: str
    leader_id: str
    members: list[str] = field(default_factory=list)
    loot_mode: str = "round_robin"

    def add(self, character_id: str) -> bool:
        if character_id in self.members:
            return False
        self.members.append(character_id)
        return True

    def remove(self, character_id: str) -> None:
        if character_id in self.members:
            self.members.remove(character_id)


@dataclass
class Guild:
    id: str
    name: str
    leader_id: str
    members: dict[str, str] = field(default_factory=dict)
    bank_gold: int = 0
    level: int = 1
    experience: int = 0

    def add_member(self, character_id: str, rank: str = "member") -> None:
        self.members[character_id] = rank

    def remove_member(self, character_id: str) -> None:
        self.members.pop(character_id, None)


@dataclass
class SocialGraph:
    friends: dict[str, set[str]] = field(default_factory=dict)
    blocked: dict[str, set[str]] = field(default_factory=dict)

    def add_friend(self, a: str, b: str) -> None:
        self.friends.setdefault(a, set()).add(b)
        self.friends.setdefault(b, set()).add(a)

    def block(self, a: str, b: str) -> None:
        self.blocked.setdefault(a, set()).add(b)
