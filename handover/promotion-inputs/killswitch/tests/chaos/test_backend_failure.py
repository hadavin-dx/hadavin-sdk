"""Chaos tests for backend failure scenarios.

Verifies fail-closed behavior when the backend is unreliable.
"""

from __future__ import annotations

import random

import pytest

from agent_killswitch import KillLevel, KillScope, KillSwitch


class FlakeyBackend:
    """Backend that fails randomly to test fault tolerance."""

    def __init__(self, failure_rate: float = 0.5) -> None:
        self._store: dict[str, str] = {}
        self._failure_rate = failure_rate

    def _maybe_fail(self) -> None:
        if random.random() < self._failure_rate:
            raise ConnectionError("Simulated backend failure")

    def get(self, key: str) -> str | None:
        self._maybe_fail()
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._maybe_fail()
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._maybe_fail()
        self._store.pop(key, None)

    def get_many(self, keys: list[str]) -> list[str | None]:
        self._maybe_fail()
        return [self._store.get(k) for k in keys]

    def keys(self, pattern: str) -> list[str]:
        self._maybe_fail()
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [k for k in self._store if k.startswith(prefix)]
        return [k for k in self._store if k == pattern]

    def exists(self, key: str) -> bool:
        self._maybe_fail()
        return key in self._store

    def clear(self) -> None:
        self._store.clear()


class AlwaysFailBackend:
    """Backend that always fails."""

    def get(self, key: str) -> str | None:
        raise ConnectionError("Backend is down")

    def set(self, key: str, value: str) -> None:
        raise ConnectionError("Backend is down")

    def delete(self, key: str) -> None:
        raise ConnectionError("Backend is down")

    def get_many(self, keys: list[str]) -> list[str | None]:
        raise ConnectionError("Backend is down")

    def keys(self, pattern: str) -> list[str]:
        return []

    def exists(self, key: str) -> bool:
        return False

    def clear(self) -> None:
        pass


@pytest.mark.chaos
class TestBackendFailure:
    """Test kill switch behavior with failing backends."""

    def test_fail_closed_on_total_failure(self) -> None:
        """When backend is completely down, fail-closed returns KILLED."""
        ks = KillSwitch(backend=AlwaysFailBackend(), fail_closed=True)
        status = ks.check(scope_target="agent-1")
        assert status.is_killed
        assert status.level == KillLevel.KILL

    def test_fail_open_when_configured(self) -> None:
        """When configured fail-open, backend failure returns safe."""
        ks = KillSwitch(backend=AlwaysFailBackend(), fail_closed=False)
        status = ks.check(scope_target="agent-1")
        assert not status.is_killed

    def test_flakey_backend_fail_closed(self) -> None:
        """With a flakey backend, fail-closed ensures safety."""
        random.seed(42)
        backend = FlakeyBackend(failure_rate=0.5)
        ks = KillSwitch(backend=backend, fail_closed=True)

        killed_count = 0
        safe_count = 0
        for _ in range(100):
            status = ks.check(scope_target="agent-1")
            if status.is_killed:
                killed_count += 1
            else:
                safe_count += 1

        # With 50% failure rate and fail-closed, we should see some kills
        assert killed_count > 0, "Should have some fail-closed kills"

    def test_activate_survives_backend_error(self) -> None:
        """Activation should not crash even if backend fails."""
        ks = KillSwitch(backend=AlwaysFailBackend(), fail_closed=True)

        # Should not raise -- activation logs the error but continues
        event = ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="emergency")
        assert event.level == KillLevel.KILL

    def test_deactivate_survives_backend_error(self) -> None:
        """Deactivation should not crash even if backend fails."""
        ks = KillSwitch(backend=AlwaysFailBackend(), fail_closed=True)
        # Should not raise
        ks.deactivate(KillScope.GLOBAL)
