from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Party:
    party_id: str
    leader_id: str
    members: list[str] = field(default_factory=list)
    max_size: int = 5

    def add(self, player_id: str) -> bool:
        if player_id in self.members or len(self.members) >= self.max_size:
            return False
        self.members.append(player_id)
        return True

    def remove(self, player_id: str) -> bool:
        if player_id not in self.members:
            return False
        self.members.remove(player_id)
        if self.leader_id == player_id and self.members:
            self.leader_id = self.members[0]
        return True


@dataclass
class Guild:
    guild_id: str
    name: str
    leader_id: str
    members: set[str] = field(default_factory=set)
    officers: set[str] = field(default_factory=set)
    level: int = 1
    experience: int = 0

    def add_member(self, player_id: str) -> None:
        self.members.add(player_id)

    def remove_member(self, player_id: str) -> None:
        self.members.discard(player_id)
        self.officers.discard(player_id)

    def promote(self, player_id: str) -> bool:
        if player_id not in self.members:
            return False
        self.officers.add(player_id)
        return True


@dataclass
class SocialService:
    parties: dict[str, Party] = field(default_factory=dict)
    guilds: dict[str, Guild] = field(default_factory=dict)

    def create_party(self, party_id: str, leader_id: str) -> Party:
        party = Party(party_id, leader_id, [leader_id])
        self.parties[party_id] = party
        return party

    def create_guild(self, guild_id: str, name: str, leader_id: str) -> Guild:
        guild = Guild(guild_id, name, leader_id, {leader_id})
        self.guilds[guild_id] = guild
        return guild
