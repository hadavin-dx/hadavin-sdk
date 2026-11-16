"""Security tests for unauthorized kill prevention.

Verifies that kill switch operations maintain integrity
and cannot be bypassed.
"""

from __future__ import annotations

import pytest

from agent_killswitch import KillLevel, KillScope, KillSwitch
from agent_killswitch.backends.memory import InMemoryBackend


@pytest.mark.security
class TestUnauthorizedKill:
    """Tests to verify kill switch cannot be bypassed."""

    def test_direct_backend_manipulation_detected(self) -> None:
        """Direct backend manipulation still shows as killed."""
        backend = InMemoryBackend()
        ks = KillSwitch(backend=backend)

        # Simulate direct backend manipulation
        backend.set("global", "kill")

        # Kill switch should detect it
        status = ks.check()
        assert status.is_killed

    def test_invalid_level_ignored(self) -> None:
        """Invalid kill level values in backend are ignored."""
        backend = InMemoryBackend()
        ks = KillSwitch(backend=backend)

        # Inject invalid level directly
        backend.set("global", "invalid_level")

        # Should not crash, and should return safe (invalid = not a real kill)
        status = ks.check()
        assert not status.is_killed

    def test_empty_string_level_ignored(self) -> None:
        """Empty string in backend is treated as inactive."""
        backend = InMemoryBackend()
        ks = KillSwitch(backend=backend)

        backend.set("global", "")
        status = ks.check()
        # Empty string is not a valid KillLevel, so it's ignored
        assert not status.is_killed

    def test_scope_isolation(self) -> None:
        """Kill on one agent does not affect another."""
        ks = KillSwitch()
        ks.activate(KillLevel.KILL, KillScope.AGENT, scope_target="malicious-agent")

        status = ks.check(scope_target="innocent-agent")
        assert not status.is_killed

    def test_no_ttl_prevents_auto_resume(self) -> None:
        """Kill switches require explicit deactivation -- no auto-expire."""
        ks = KillSwitch()
        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="permanent until cleared")

        # Even after "time passes" (no TTL), still killed
        import time

        time.sleep(0.1)
        status = ks.check()
        assert status.is_killed

    def test_audit_trail_immutable(self) -> None:
        """Event history cannot be cleared through the API."""
        ks = KillSwitch()
        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="logged")

        events = ks.get_events()
        assert len(events) == 1

        # Even after deactivation, the event remains
        ks.deactivate(KillScope.GLOBAL)
        events = ks.get_events()
        assert len(events) == 1
        assert events[0].reason == "logged"

    def test_multiple_activations_all_logged(self) -> None:
        """Every activation creates an audit entry."""
        ks = KillSwitch()
        for i in range(5):
            ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason=f"attempt-{i}")

        events = ks.get_events()
        assert len(events) == 5
