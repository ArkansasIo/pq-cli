def test_rpg_services_import() -> None:
    from pqcli.rpg import auction, backend, combat_service, instances, inventory_service, mail
    from pqcli.rpg import pvp_services, quest_service, respawn, runtime, social_services, trading, world_service
    from pqcli.rpg.api import ApiRouter, Envelope
    from pqcli.rpg.database.postgres import PostgresCharacterStore
    from pqcli.rpg.server.permissions import can
    from pqcli.rpg.server.rate_limit import RateLimiter

    assert auction.AuctionHouse
    assert backend.GameBackend
    assert combat_service.CombatService
    assert instances.InstanceService
    assert inventory_service.InventoryService
    assert mail.MailService
    assert pvp_services.PvPService
    assert quest_service.QuestService
    assert respawn.RespawnService
    assert runtime.RuntimeState
    assert social_services.SocialService
    assert trading.TradeSession
    assert world_service.WorldService
    assert ApiRouter and Envelope and PostgresCharacterStore and can and RateLimiter
