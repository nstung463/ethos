from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class RateLimitRule:
    scope: str
    limit: int
    window_seconds: int


class RateLimiter:
    """Small in-memory sliding-window limiter for abuse control."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, *, rule: RateLimitRule, key: str) -> tuple[bool, int]:
        now = time.time()
        bucket_key = f"{rule.scope}:{key}"
        with self._lock:
            bucket = self._events[bucket_key]
            cutoff = now - rule.window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= rule.limit:
                retry_after = max(1, int(rule.window_seconds - (now - bucket[0])))
                return False, retry_after
            bucket.append(now)
            return True, 0
