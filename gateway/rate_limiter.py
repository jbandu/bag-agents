"""
Rate Limiter

Implements token bucket algorithm for rate limiting by role.
"""

import time
import logging
from typing import Dict, Optional
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock

from auth.rbac import Role


logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a role."""
    requests_per_minute: int
    burst_size: int


# Rate limits by role
RATE_LIMITS = {
    Role.ADMIN: RateLimitConfig(requests_per_minute=1000, burst_size=100),
    Role.OPERATIONS: RateLimitConfig(requests_per_minute=500, burst_size=50),
    Role.AGENT: RateLimitConfig(requests_per_minute=300, burst_size=30),
    Role.HANDLER: RateLimitConfig(requests_per_minute=200, burst_size=20),
    Role.PASSENGER: RateLimitConfig(requests_per_minute=60, burst_size=10),
}


class TokenBucket:
    """
    Token bucket for rate limiting.

    Implements the token bucket algorithm for smooth rate limiting.
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens per second
            capacity: Maximum tokens (burst capacity)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens consumed successfully
        """
        with self.lock:
            now = time.time()

            # Add tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            # Try to consume
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def get_available_tokens(self) -> float:
        """Get current number of available tokens."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            return min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )


class RateLimiter:
    """
    Rate limiter for API gateway.

    Manages rate limits for different users and roles.
    """

    def __init__(self):
        """Initialize rate limiter."""
        self.buckets: Dict[str, TokenBucket] = {}
        self.lock = Lock()
        self.stats = defaultdict(lambda: {"allowed": 0, "blocked": 0})

    def check_rate_limit(
        self,
        user_id: str,
        role: str,
        tokens: int = 1
    ) -> bool:
        """
        Check if request is within rate limit.

        Args:
            user_id: User identifier
            role: User role
            tokens: Number of tokens to consume

        Returns:
            True if request allowed
        """
        # Get rate limit config for role
        config = RATE_LIMITS.get(role, RATE_LIMITS[Role.PASSENGER])

        # Get or create bucket for user
        bucket_key = f"{user_id}:{role}"

        with self.lock:
            if bucket_key not in self.buckets:
                rate = config.requests_per_minute / 60.0  # Convert to per second
                self.buckets[bucket_key] = TokenBucket(
                    rate=rate,
                    capacity=config.burst_size
                )

        bucket = self.buckets[bucket_key]

        # Try to consume tokens
        allowed = bucket.consume(tokens)

        # Update stats
        if allowed:
            self.stats[role]["allowed"] += 1
        else:
            self.stats[role]["blocked"] += 1
            logger.warning(
                f"Rate limit exceeded for user {user_id} (role: {role})"
            )

        return allowed

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get rate limiting statistics.

        Returns:
            Dictionary of stats by role
        """
        return dict(self.stats)

    def reset_user(self, user_id: str, role: str):
        """
        Reset rate limit for a user.

        Args:
            user_id: User identifier
            role: User role
        """
        bucket_key = f"{user_id}:{role}"

        with self.lock:
            if bucket_key in self.buckets:
                del self.buckets[bucket_key]

    def cleanup_inactive_buckets(self, inactive_seconds: int = 3600):
        """
        Clean up buckets for inactive users.

        Args:
            inactive_seconds: Seconds of inactivity before cleanup
        """
        now = time.time()

        with self.lock:
            inactive_keys = []

            for key, bucket in self.buckets.items():
                if now - bucket.last_update > inactive_seconds:
                    inactive_keys.append(key)

            for key in inactive_keys:
                del self.buckets[key]

        if inactive_keys:
            logger.info(f"Cleaned up {len(inactive_keys)} inactive rate limit buckets")
