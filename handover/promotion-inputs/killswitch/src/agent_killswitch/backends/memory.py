"""In-memory backend for kill switch state storage.

Zero-dependency, thread-safe, dict-based backend. This is the default
backend and is suitable for:
- Single-process applications
- Testing and development
- Applications that don't need distributed state

For distributed systems, use the RedisBackend instead.
"""

from __future__ import annotations

import threading


class InMemoryBackend:
    """Thread-safe in-memory backend using a dictionary.

    All operations are protected by a reentrant lock for thread safety.
    This backend is the default when no external backend is configured.

    Example::

        from agent_killswitch.backends.memory import InMemoryBackend

        backend = InMemoryBackend()
        backend.set("killswitch:global", "kill")
        assert backend.get("killswitch:global") == "kill"
    """

    def __init__(self) -> None:
        """Initialize the in-memory backend."""
        self._store: dict[str, str] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> str | None:
        """Get a value by key.

        Args:
            key: The storage key.

        Returns:
            The stored value, or None if not found.
        """
        with self._lock:
            return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        """Set a value by key.

        Args:
            key: The storage key.
            value: The value to store.
        """
        with self._lock:
            self._store[key] = value

    def delete(self, key: str) -> None:
        """Delete a key.

        Args:
            key: The storage key to delete.
        """
        with self._lock:
            self._store.pop(key, None)

    def get_many(self, keys: list[str]) -> list[str | None]:
        """Get multiple values atomically.

        Args:
            keys: List of storage keys.

        Returns:
            List of values in the same order as keys.
        """
        with self._lock:
            return [self._store.get(k) for k in keys]

    def keys(self, pattern: str) -> list[str]:
        """Find keys matching a prefix pattern.

        Args:
            pattern: Key pattern. If it ends with '*', matches prefix.
                    Otherwise, matches exact key.

        Returns:
            List of matching keys.
        """
        with self._lock:
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                return [k for k in self._store if k.startswith(prefix)]
            return [k for k in self._store if k == pattern]

    def exists(self, key: str) -> bool:
        """Check if a key exists.

        Args:
            key: The storage key.

        Returns:
            True if the key exists.
        """
        with self._lock:
            return key in self._store

    def clear(self) -> None:
        """Remove all keys."""
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        """Return the number of stored keys."""
        with self._lock:
            return len(self._store)

    def __repr__(self) -> str:
        with self._lock:
            return f"InMemoryBackend(keys={len(self._store)})"
