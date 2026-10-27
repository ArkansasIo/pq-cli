from dataclasses import dataclass, field


@dataclass
class MarketOrder:
    order_id: str
    seller_id: str
    item_id: str
    quantity: int
    unit_price: int


@dataclass
class Market:
    orders: dict[str, MarketOrder] = field(default_factory=dict)
    tax_rate: float = 0.05

    def list(self, order: MarketOrder) -> None:
        if order.quantity <= 0 or order.unit_price < 0:
            raise ValueError("invalid market order")
        self.orders[order.order_id] = order

    def cancel(self, order_id: str, seller_id: str) -> bool:
        order = self.orders.get(order_id)
        if order is None or order.seller_id != seller_id:
            return False
        del self.orders[order_id]
        return True

    def search(self, item_id: str) -> list[MarketOrder]:
        return sorted((o for o in self.orders.values() if o.item_id == item_id), key=lambda o: o.unit_price)


@dataclass
class Wallet:
    currencies: dict[str, int] = field(default_factory=lambda: {"gold": 0})

    def add(self, currency: str, amount: int) -> None:
        self.currencies[currency] = self.currencies.get(currency, 0) + amount

    def spend(self, currency: str, amount: int) -> bool:
        if amount < 0 or self.currencies.get(currency, 0) < amount:
            return False
        self.currencies[currency] -= amount
        return True
