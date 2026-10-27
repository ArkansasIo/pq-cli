from dataclasses import dataclass, field


@dataclass(frozen=True)
class TalentNode:
    id: str
    name: str
    max_rank: int = 1
    prerequisites: tuple[str, ...] = ()


@dataclass
class TalentTree:
    nodes: dict[str, TalentNode] = field(default_factory=dict)

    def add(self, node: TalentNode) -> None:
        self.nodes[node.id] = node


@dataclass
class Progression:
    talent_points: int = 0
    talents: dict[str, int] = field(default_factory=dict)
    prestige: int = 0

    def spend(self, tree: TalentTree, node_id: str) -> bool:
        node = tree.nodes[node_id]
        current = self.talents.get(node_id, 0)
        if self.talent_points <= 0 or current >= node.max_rank:
            return False
        if any(self.talents.get(req, 0) <= 0 for req in node.prerequisites):
            return False
        self.talents[node_id] = current + 1
        self.talent_points -= 1
        return True
