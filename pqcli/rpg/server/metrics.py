from __future__ import annotations

from collections import Counter


class Metrics:
    def __init__(self) -> None:
        self.counters: Counter[str] = Counter()
        self.gauges: dict[str, float] = {}

    def increment(self, name: str, amount: int = 1) -> None:
        self.counters[name] += amount

    def set_gauge(self, name: str, value: float) -> None:
        self.gauges[name] = value

    def snapshot(self) -> dict[str, dict[str, float]]:
        return {"counters": dict(self.counters), "gauges": dict(self.gauges)}
