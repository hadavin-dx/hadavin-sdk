"""Redis backend for distributed kill switch state storage.

Requires the `redis` optional dependency:
    pip install agent-killswitch[redis]

This backend is suitable for:
- Multi-process applications
- Distributed systems
- Production deployments where multiple services need shared kill state

The backend uses Redis pipelines for efficient multi-key operations
and falls back to fail-closed behavior on connection errors.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RedisBackend:
    """Redis-backed storage for kill switch state.

    Uses Redis for sub-millisecond flag checks across distributed systems.
    All keys use a configurable prefix (default: "killswitch:") to avoid
    collisions with other Redis users.

    Fail-closed behavior: If Redis is unreachable, operations raise
    exceptions. The KillSwitch class interprets backend failures as
    KILLED state for safety.

    Example::

        import redis
        from agent_killswitch.backends.redis import RedisBackend

        client = redis.Redis(host="localhost", port=6379, db=0)
        backend = RedisBackend(client, prefix="myapp:killswitch:")

    Args:
        redis_client: A redis.Redis or redis.StrictRedis instance.
        prefix: Key prefix for all kill switch keys.
            Defaults to "killswitch:".
    """

    def __init__(
        self,
        redis_client: Any,
        prefix: str = "killswitch:",
    ) -> None:
        """Initialize the Redis backend.

        Args:
            redis_client: A Redis client instance. Must support get, set,
                delete, pipeline, scan_iter, and exists methods.
            prefix: Key prefix for namespacing. Defaults to "killswitch:".
        """
        self._redis = redis_client
        self._prefix = prefix

    def _prefixed(self, key: str) -> str:
        """Add prefix to a key if not already prefixed.

        Args:
            key: The raw key.

        Returns:
            The prefixed key.
        """
        if key.startswith(self._prefix):
            return key
        return f"{self._prefix}{key}"

    def _unprefixed(self, key: str) -> str:
        """Remove prefix from a key.

        Args:
            key: The prefixed key.

        Returns:
            The raw key without prefix.
        """
        if key.startswith(self._prefix):
            return key[len(self._prefix) :]
        return key

    def get(self, key: str) -> str | None:
        """Get a value from Redis.

        Args:
            key: The storage key.

        Returns:
            The stored value as a string, or None if not found.

        Raises:
            Exception: On Redis connection failure (fail-closed).
        """
        try:
            val = self._redis.get(self._prefixed(key))
            if val is not None and isinstance(val, bytes):
                return val.decode("utf-8")
            return val
        except Exception:
            logger.error("Redis GET failed for key=%s", key, exc_info=True)
            raise

    def set(self, key: str, value: str) -> None:
        """Set a value in Redis. No TTL -- explicit deletion required.

        Args:
            key: The storage key.
            value: The value to store.

        Raises:
            Exception: On Redis connection failure.
        """
        try:
            self._redis.set(self._prefixed(key), value)
        except Exception:
            logger.error("Redis SET failed for key=%s", key, exc_info=True)
            raise

    def delete(self, key: str) -> None:
        """Delete a key from Redis.

        Args:
            key: The storage key to delete.

        Raises:
            Exception: On Redis connection failure.
        """
        try:
            self._redis.delete(self._prefixed(key))
        except Exception:
            logger.error("Redis DELETE failed for key=%s", key, exc_info=True)
            raise

    def get_many(self, keys: list[str]) -> list[str | None]:
        """Get multiple values using a Redis pipeline (single round-trip).

        Args:
            keys: List of storage keys.

        Returns:
            List of values (or None) in the same order as keys.

        Raises:
            Exception: On Redis connection failure.
        """
        try:
            pipe = self._redis.pipeline(transaction=False)
            for key in keys:
                pipe.get(self._prefixed(key))
            results = pipe.execute()
            return [r.decode("utf-8") if isinstance(r, bytes) else r for r in results]
        except Exception:
            logger.error("Redis pipeline GET failed for keys=%s", keys, exc_info=True)
            raise

    def keys(self, pattern: str) -> list[str]:
        """Find keys matching a pattern using Redis SCAN.

        Args:
            pattern: Key pattern. If it ends with '*', uses SCAN with
                    the prefixed pattern. Otherwise matches exact key.

        Returns:
            List of matching keys (without prefix).

        Raises:
            Exception: On Redis connection failure.
        """
        try:
            if pattern.endswith("*"):
                redis_pattern = self._prefixed(pattern)
                found: list[str] = []
                for key in self._redis.scan_iter(match=redis_pattern):
                    if isinstance(key, bytes):
                        key = key.decode("utf-8")
                    found.append(self._unprefixed(key))
                return found
            else:
                prefixed = self._prefixed(pattern)
                if self._redis.exists(prefixed):
                    return [pattern]
                return []
        except Exception:
            logger.error("Redis KEYS failed for pattern=%s", pattern, exc_info=True)
            raise

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis.

        Args:
            key: The storage key.

        Returns:
            True if the key exists.

        Raises:
            Exception: On Redis connection failure.
        """
        try:
            return bool(self._redis.exists(self._prefixed(key)))
        except Exception:
            logger.error("Redis EXISTS failed for key=%s", key, exc_info=True)
            raise

    def clear(self) -> None:
        """Remove all keys with our prefix. Use with caution.

        Raises:
            Exception: On Redis connection failure.
        """
        try:
            pattern = f"{self._prefix}*"
            keys_to_delete: list[Any] = []
            for key in self._redis.scan_iter(match=pattern):
                keys_to_delete.append(key)
            if keys_to_delete:
                self._redis.delete(*keys_to_delete)
        except Exception:
            logger.error("Redis CLEAR failed", exc_info=True)
            raise

    def __repr__(self) -> str:
        return f"RedisBackend(prefix={self._prefix!r})"
