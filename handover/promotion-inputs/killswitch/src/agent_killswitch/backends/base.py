"""Abstract backend protocol for kill switch state storage.

Backends provide the storage layer for kill switch state. The protocol
defines the minimal interface that any backend must implement.

Two implementations are provided:
- InMemoryBackend: Zero-dependency, dict-based (default)
- RedisBackend: Distributed, Redis-backed (optional)

Custom backends can be created by implementing this protocol.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class KillSwitchBackend(Protocol):
    """Protocol for kill switch state backends.

    All methods are synchronous. For async usage, wrap in an executor
    or use an async-native backend.

    The backend MUST be fail-closed: if any operation fails, the caller
    should treat the agent as KILLED for safety.
    """

    def get(self, key: str) -> str | None:
        """Get a value by key.

        Args:
            key: The storage key.

        Returns:
            The stored value as a string, or None if not found.
        """
        ...

    def set(self, key: str, value: str) -> None:
        """Set a value by key. No TTL -- explicit deletion required.

        Args:
            key: The storage key.
            value: The value to store.
        """
        ...

    def delete(self, key: str) -> None:
        """Delete a key.

        Args:
            key: The storage key to delete.
        """
        ...

    def get_many(self, keys: list[str]) -> list[str | None]:
        """Get multiple values in a single operation.

        Args:
            keys: List of storage keys.

        Returns:
            List of values (or None) in the same order as keys.
        """
        ...

    def keys(self, pattern: str) -> list[str]:
        """Find keys matching a pattern.

        The pattern uses simple prefix matching (not glob).
        Pass "prefix*" to match all keys starting with "prefix".

        Args:
            pattern: Key pattern to match (prefix with trailing *).

        Returns:
            List of matching keys.
        """
        ...

    def exists(self, key: str) -> bool:
        """Check if a key exists.

        Args:
            key: The storage key.

        Returns:
            True if the key exists.
        """
        ...

    def clear(self) -> None:
        """Remove all keys. Use with caution -- primarily for testing."""
        ...
