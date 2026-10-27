from __future__ import annotations

from dataclasses import dataclass

from .auction import AuctionHouse
from .mail import MailService
from .pvp_services import PvPService
from .quest_service import QuestService
from .social_services import SocialService
from .trading import TradeSession
from .world_service import WorldService


@dataclass
class GameBackend:
    """In-process authoritative service composition for local and test deployments."""

    social: SocialService
    world: WorldService
    quests: QuestService
    pvp: PvPService
    auction: AuctionHouse
    mail: MailService

    @classmethod
    def create(cls) -> "GameBackend":
        return cls(SocialService(), WorldService(), QuestService(), PvPService(), AuctionHouse(), MailService())

    def trade(self, trade_id: str, player_a: str, player_b: str) -> TradeSession:
        return TradeSession(trade_id, player_a, player_b)
