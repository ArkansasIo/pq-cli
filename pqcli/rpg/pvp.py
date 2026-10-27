from dataclasses import dataclass, field


@dataclass
class PvPRating:
    rating: int = 1000
    wins: int = 0
    losses: int = 0

    def win(self, opponent_rating: int) -> None:
        expected = 1 / (1 + 10 ** ((opponent_rating - self.rating) / 400))
        self.rating += round(32 * (1 - expected))
        self.wins += 1

    def loss(self, opponent_rating: int) -> None:
        expected = 1 / (1 + 10 ** ((opponent_rating - self.rating) / 400))
        self.rating += round(32 * (0 - expected))
        self.rating = max(0, self.rating)
        self.losses += 1


@dataclass
class PvPSeason:
    season_id: str
    name: str
    ratings: dict[str, PvPRating] = field(default_factory=dict)

    def leaderboard(self, limit: int = 100) -> list[tuple[str, PvPRating]]:
        return sorted(self.ratings.items(), key=lambda pair: pair[1].rating, reverse=True)[:limit]
