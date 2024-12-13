import threading
from time import time


class RateLimiter:
    """Simple token bucket rate limiter"""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self, tokens: int = 1) -> bool:
        with self.lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + time_passed * self.rate)
            self.last_update = now

            if tokens <= self.tokens:
                self.tokens -= tokens
                return True
            return False
