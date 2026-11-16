"""Chaos tests for network partition scenarios.

Simulates network partitions where the backend becomes temporarily
unreachable, then recovers.
"""

from __future__ import annotations

import pytest

from agent_killswitch import KillLevel, KillScope, KillSwitch


class PartitionableBackend:
    """Backend that can simulate network partitions."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._partitioned = False

    def partition(self) -> None:
        """Simulate network partition."""
        self._partitioned = True

    def heal(self) -> None:
        """Heal the network partition."""
        self._partitioned = False

    def _check_partition(self) -> None:
        if self._partitioned:
            raise ConnectionError("Network partition")

    def get(self, key: str) -> str | None:
        self._check_partition()
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._check_partition()
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._check_partition()
        self._store.pop(key, None)

    def get_many(self, keys: list[str]) -> list[str | None]:
        self._check_partition()
        return [self._store.get(k) for k in keys]

    def keys(self, pattern: str) -> list[str]:
        self._check_partition()
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [k for k in self._store if k.startswith(prefix)]
        return [k for k in self._store if k == pattern]

    def exists(self, key: str) -> bool:
        self._check_partition()
        return key in self._store

    def clear(self) -> None:
        self._store.clear()


@pytest.mark.chaos
class TestNetworkPartition:
    """Test kill switch during network partitions."""

    def test_partition_then_heal(self) -> None:
        """Kill switch recovers after partition heals."""
        backend = PartitionableBackend()
        ks = KillSwitch(backend=backend, fail_closed=True)

        # Normal operation: activate
        ks.activate(KillLevel.STOP, KillScope.GLOBAL, reason="test")
        assert ks.check().is_killed

        # Partition: fail-closed
        backend.partition()
        status = ks.check()
        assert status.is_killed  # Fail-closed

        # Heal: back to normal
        backend.heal()
        status = ks.check()
        assert status.is_killed  # Still killed because we activated earlier
        assert status.level == KillLevel.STOP

    def test_deactivation_during_partition(self) -> None:
        """Deactivation during partition is lost but fail-closed stays safe."""
        backend = PartitionableBackend()
        ks = KillSwitch(backend=backend, fail_closed=True)

        # Activate
        ks.activate(KillLevel.KILL, KillScope.GLOBAL)
        assert ks.check().is_killed

        # Partition: deactivation fails silently
        backend.partition()
        ks.deactivate(KillScope.GLOBAL)

        # Still partitioned: fail-closed
        status = ks.check()
        assert status.is_killed

        # Heal: activation is still in backend (deactivation was lost)
        backend.heal()
        status = ks.check()
        assert status.is_killed  # Kill persists

    def test_activation_during_partition(self) -> None:
        """Activation during partition is lost but fail-closed stays safe."""
        backend = PartitionableBackend()
        ks = KillSwitch(backend=backend, fail_closed=True)

        # Partition before activation
        backend.partition()
        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="during partition")

        # Check during partition: fail-closed
        status = ks.check()
        assert status.is_killed

        # Heal: activation was lost (backend was down)
        backend.heal()
        status = ks.check()
        assert not status.is_killed  # Activation was lost
