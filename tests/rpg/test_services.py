from pqcli.rpg.auction import AuctionHouse, AuctionListing
from pqcli.rpg.backend import GameBackend
from pqcli.rpg.instances import InstanceService
from pqcli.rpg.mail import MailMessage, MailService
from pqcli.rpg.pvp_services import PvPService
from pqcli.rpg.social_services import SocialService
from pqcli.rpg.trading import TradeSession
from pqcli.rpg.world_service import WorldService


def test_party_and_guild() -> None:
    social = SocialService()
    party = social.create_party("p1", "alice")
    assert party.add("bob")
    guild = social.create_guild("g1", "Heroes", "alice")
    assert guild.promote("alice")


def test_trade_requires_both_acceptances() -> None:
    trade = TradeSession("t1", "alice", "bob")
    trade.offer("alice", "sword", 1)
    assert not trade.accept("alice")
    assert trade.accept("bob")
    assert trade.ready


def test_pvp_matchmaking() -> None:
    pvp = PvPService()
    pvp.queue("a", "arena")
    pvp.queue("b", "arena")
    match = pvp.make_match("m1", "arena")
    assert match is not None
    assert match.players == ("a", "b")


def test_world_instance_auction_and_mail() -> None:
    world = WorldService()
    world.enter("a", "greenfields")
    assert world.zones["greenfields"].population == 1

    instances = InstanceService()
    instance = instances.create("greenfields_mines", "normal", ["p1"])
    instance.start()
    assert instance.state == "active"

    auction = AuctionHouse()
    auction.list(AuctionListing("l1", "a", "sword", 1, 100))
    assert auction.search("sword")[0].total_price == 100

    mail = MailService()
    mail.send(MailMessage("m1", "a", "b", "Hello", "Welcome"))
    assert len(mail.inbox("b")) == 1


def test_backend_factory() -> None:
    backend = GameBackend.create()
    assert backend.world is not None
    assert backend.quests is not None
