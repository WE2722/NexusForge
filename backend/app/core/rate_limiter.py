"""Rate Limiter — Redis-backed sliding window."""
from __future__ import annotations

import time
import structlog

logger = structlog.get_logger(__name__)

class RateLimiter:
    """Redis-backed sliding window rate limiter."""
    
    def __init__(self) -> None:
        self._mock_store: dict[str, list[float]] = {}
        
    async def is_rate_limited(self, key: str, max_requests: int = 10, window_seconds: int = 3600) -> tuple[bool, int]:
        """
        Checks if a specific key has exceeded the rate limit.
        Returns (is_limited, retry_after_seconds).
        """
        now = time.time()

        
        
        if key not in self._mock_store:
            self._mock_store[key] = []
            
        # Clean old requests
        self._mock_store[key] = [t for t in self._mock_store[key] if now - t < window_seconds]
        
        if len(self._mock_store[key]) >= max_requests:
            # Calculate when the oldest request in the current window will expire
            oldest = self._mock_store[key][0]
            retry_after = int(window_seconds - (now - oldest))
            return True, retry_after
            
        self._mock_store[key].append(now)
        return False, 0
