from __future__ import annotations

from collections import defaultdict, deque
from time import monotonic


class RateLimiter:
    def __init__(self, limit: int = 30, window_seconds: float = 1.0) -> None:
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = monotonic()
        events = self._events[key]
        while events and now - events[0] >= self.window_seconds:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True
