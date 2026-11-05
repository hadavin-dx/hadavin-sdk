"""Chaos tests for concurrent kill operations.

Verifies thread safety under concurrent activation, deactivation,
and check operations.
"""

from __future__ import annotations

import threading

import pytest

from agent_killswitch import KillLevel, KillScope, KillSwitch


@pytest.mark.chaos
class TestConcurrentKills:
    """Test concurrent kill switch operations for thread safety."""

    def test_concurrent_activations(self) -> None:
        """Multiple threads activating kill switches simultaneously."""
        ks = KillSwitch()
        errors: list[str] = []

        def activate_worker(agent_id: str) -> None:
            try:
                for _ in range(50):
                    ks.activate(
                        KillLevel.KILL,
                        KillScope.AGENT,
                        scope_target=agent_id,
                        reason=f"kill {agent_id}",
                    )
                    ks.deactivate(KillScope.AGENT, scope_target=agent_id)
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=activate_worker, args=(f"agent-{i}",)) for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_concurrent_checks(self) -> None:
        """Multiple threads checking kill switch status simultaneously."""
        ks = KillSwitch()
        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="concurrent test")
        errors: list[str] = []

        def check_worker() -> None:
            try:
                for _ in range(100):
                    status = ks.check(scope_target="agent-1")
                    if not status.is_killed:
                        errors.append("Expected killed but got safe")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=check_worker) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_concurrent_register_unregister(self) -> None:
        """Multiple threads registering/unregistering agents."""
        ks = KillSwitch()
        errors: list[str] = []

        def register_worker(n: int) -> None:
            try:
                for i in range(50):
                    agent_id = f"agent-{n}-{i}"
                    ks.register_agent(agent_id)
                    ks.unregister_agent(agent_id)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=register_worker, args=(n,)) for n in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_concurrent_mixed_operations(self) -> None:
        """Mix of activations, deactivations, and checks."""
        ks = KillSwitch()
        errors: list[str] = []
        iterations = 50

        def activator() -> None:
            try:
                for _ in range(iterations):
                    ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="test")
            except Exception as e:
                errors.append(f"activator: {e}")

        def deactivator() -> None:
            try:
                for _ in range(iterations):
                    ks.deactivate(KillScope.GLOBAL)
            except Exception as e:
                errors.append(f"deactivator: {e}")

        def checker() -> None:
            try:
                for _ in range(iterations):
                    ks.check(scope_target="agent-1")
            except Exception as e:
                errors.append(f"checker: {e}")

        threads = [
            threading.Thread(target=activator),
            threading.Thread(target=deactivator),
            threading.Thread(target=checker),
            threading.Thread(target=checker),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
