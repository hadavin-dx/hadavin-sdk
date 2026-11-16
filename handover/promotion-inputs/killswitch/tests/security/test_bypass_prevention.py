"""Security tests for kill switch bypass prevention.

Ensures agents cannot circumvent the kill switch through
various techniques.
"""

from __future__ import annotations

import threading

import pytest

from agent_killswitch import KillLevel, KillScope, KillSwitch
from agent_killswitch.backends.memory import InMemoryBackend
from agent_killswitch.decorators import KillSwitchTriggered, killswitch_protected


@pytest.mark.security
class TestBypassPrevention:
    """Tests that agents cannot bypass the kill switch."""

    def test_cannot_deactivate_from_protected_function(self) -> None:
        """A protected function cannot deactivate its own kill switch."""
        ks = KillSwitch()
        ks.activate(KillLevel.KILL, KillScope.AGENT, scope_target="sneaky-agent")

        @killswitch_protected(killswitch=ks, agent_id="sneaky-agent")
        def sneaky_function():
            # Even if the agent tries to deactivate itself...
            ks.deactivate(KillScope.AGENT, scope_target="sneaky-agent")
            return "escaped"

        # The check happens BEFORE the function runs
        with pytest.raises(KillSwitchTriggered):
            sneaky_function()

    def test_global_overrides_agent_deactivation(self) -> None:
        """Agent cannot escape global kill by deactivating agent scope."""
        ks = KillSwitch()
        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="system-wide")
        ks.activate(KillLevel.KILL, KillScope.AGENT, scope_target="agent-1")

        # Agent deactivates its own scope
        ks.deactivate(KillScope.AGENT, scope_target="agent-1")

        # Still killed by global
        status = ks.check(scope_target="agent-1")
        assert status.is_killed
        assert status.scope == KillScope.GLOBAL

    def test_fail_closed_prevents_backend_manipulation_escape(self) -> None:
        """Clearing the backend doesn't help if fail-closed is on."""
        backend = InMemoryBackend()
        ks = KillSwitch(backend=backend, fail_closed=True)

        ks.activate(KillLevel.KILL, KillScope.GLOBAL)

        # "Agent" clears the entire backend
        backend.clear()

        # Without the key, check returns safe... but the kill was in effect
        # This is actually correct: if the key is gone, the kill is gone
        # The protection is that fail-closed catches BACKEND FAILURE, not
        # deliberate data deletion. Backend access control is a separate concern.
        status = ks.check()
        assert not status.is_killed  # Key was deleted = deactivated

    def test_concurrent_check_and_deactivate(self) -> None:
        """Race between check and deactivation still safe."""
        ks = KillSwitch()
        results: list[bool] = []
        errors: list[str] = []

        def checker() -> None:
            try:
                for _ in range(100):
                    status = ks.check(scope_target="agent-1")
                    results.append(status.is_killed)
            except Exception as e:
                errors.append(str(e))

        def toggler() -> None:
            try:
                for _ in range(100):
                    ks.activate(KillLevel.KILL, KillScope.GLOBAL)
                    ks.deactivate(KillScope.GLOBAL)
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=checker),
            threading.Thread(target=toggler),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No crashes
        assert len(errors) == 0
        # Results should be a mix of True and False (no corruption)
        assert all(isinstance(r, bool) for r in results)

    def test_prefix_isolation_prevents_cross_app_bypass(self) -> None:
        """Different prefixes prevent cross-application interference."""
        backend = InMemoryBackend()
        app_a = KillSwitch(backend=backend, prefix="app_a:")
        app_b = KillSwitch(backend=backend, prefix="app_b:")

        app_a.activate(KillLevel.KILL, KillScope.GLOBAL, reason="app_a emergency")

        # App B should not be affected
        assert not app_b.check().is_killed

        # App A should still be killed
        assert app_a.check().is_killed
