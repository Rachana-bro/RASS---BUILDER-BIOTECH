"""
RASS-BUILDER: Stage 10 In-Memory Sliding Window Rate Limiter
Enforces throughput limits on sensitive endpoints (Auth, Uploads, Job Creation, DNA Analysis)
to safeguard system resources against denial of service or abuse.
"""

import time
import threading
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException, status

from .config import settings
from .correlation import get_current_request_id


class SlidingWindowRateLimiter:
    """
    Thread-safe in-memory rate limiter using sliding timestamp windows.
    Tracks requests per client IP / identifier.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # Key: (category, client_id) -> list of epoch timestamps
        self._buckets: Dict[Tuple[str, str], List[float]] = {}

    def check(self, category: str, client_id: str, max_requests: int, window_seconds: int = 60) -> Tuple[bool, int]:
        """
        Evaluates whether a request is within allowable rate limits.
        Returns:
            (allowed: bool, retry_after_seconds: int)
        """
        if not settings.rate_limit_enabled:
            return True, 0

        now = time.time()
        key = (category, client_id)

        with self._lock:
            timestamps = self._buckets.get(key, [])
            # Purge timestamps outside the active window
            cutoff = now - window_seconds
            timestamps = [t for t in timestamps if t > cutoff]

            if len(timestamps) >= max_requests:
                # Limit exceeded
                oldest = timestamps[0]
                retry_after = max(1, int(window_seconds - (now - oldest)))
                self._buckets[key] = timestamps
                return False, retry_after

            # Within limits, record timestamp
            timestamps.append(now)
            self._buckets[key] = timestamps
            return True, 0

    def reset(self):
        """Clears all rate limit buckets. Used primarily for test isolation."""
        with self._lock:
            self._buckets.clear()


# Global rate limiter instance
rate_limiter = SlidingWindowRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extracts client IP safely, accounting for forward headers if present."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "127.0.0.1"


def enforce_rate_limit(category: str, max_requests: int, window_seconds: int = 60):
    """
    FastAPI dependency factory enforcing rate limits on routes.
    """
    def dependency(request: Request):
        client_ip = get_client_ip(request)
        allowed, retry_after = rate_limiter.check(
            category=category,
            client_id=client_ip,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

        if not allowed:
            req_id = get_current_request_id()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before retrying.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-Request-ID": req_id,
                },
            )
        return True

    return dependency
