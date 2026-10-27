from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AuctionListing:
    listing_id: str
    seller_id: str
    item_id: str
    quantity: int
    unit_price: int
    active: bool = True

    @property
    def total_price(self) -> int:
        return self.quantity * self.unit_price


class AuctionHouse:
    def __init__(self) -> None:
        self.listings: dict[str, AuctionListing] = {}

    def list(self, listing: AuctionListing) -> None:
        if listing.quantity <= 0 or listing.unit_price < 0:
            raise ValueError("invalid auction quantity or price")
        self.listings[listing.listing_id] = listing

    def search(self, item_id: str) -> list[AuctionListing]:
        return [x for x in self.listings.values() if x.active and x.item_id == item_id]

    def close(self, listing_id: str) -> AuctionListing:
        listing = self.listings[listing_id]
        listing.active = False
        return listing
