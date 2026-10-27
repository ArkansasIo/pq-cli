from dataclasses import dataclass, field


@dataclass
class Skill:
    id: str
    name: str
    level: int = 1
    experience: int = 0
    max_level: int = 100

    def add_experience(self, amount: int) -> int:
        levels = 0
        self.experience += max(0, amount)
        while self.level < self.max_level and self.experience >= self.level * 100:
            self.experience -= self.level * 100
            self.level += 1
            levels += 1
        return levels


@dataclass
class SkillBook:
    skills: dict[str, Skill] = field(default_factory=dict)

    def learn(self, skill: Skill) -> None:
        self.skills[skill.id] = skill

    def train(self, skill_id: str, experience: int) -> int:
        return self.skills[skill_id].add_experience(experience)
