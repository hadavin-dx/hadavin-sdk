"""End-to-end test for the full kill switch flow.

Tests the complete lifecycle: registration -> monitoring -> kill -> audit.
"""

from __future__ import annotations

import pytest

from agent_killswitch import (
    BudgetKillTrigger,
    KillLevel,
    KillScope,
    KillSwitch,
)
from agent_killswitch.core.cascading import CascadingTerminator


class TestFullKillFlow:
    """E2E test for the complete kill switch lifecycle."""

    @pytest.mark.e2e
    def test_agent_lifecycle(self) -> None:
        """Test: register -> work -> kill -> verify -> deactivate."""
        ks = KillSwitch()

        # 1. Register agents
        ks.register_agent("supervisor")
        ks.register_agent("worker-1", parent_id="supervisor")
        ks.register_agent("worker-2", parent_id="supervisor")

        # 2. Verify all agents are safe
        assert not ks.check(scope_target="supervisor").is_killed
        assert not ks.check(scope_target="worker-1").is_killed
        assert not ks.check(scope_target="worker-2").is_killed

        # 3. Kill one worker
        event = ks.activate(
            KillLevel.STOP,
            KillScope.AGENT,
            scope_target="worker-1",
            reason="runaway cost",
            activated_by="operator",
        )
        assert event.level == KillLevel.STOP
        assert event.latency_ms < 500  # Latency guarantee

        # 4. Verify kill status
        assert ks.check(scope_target="worker-1").is_killed
        assert not ks.check(scope_target="worker-2").is_killed
        assert not ks.check(scope_target="supervisor").is_killed

        # 5. Verify audit trail
        events = ks.get_events()
        assert len(events) == 1
        assert events[0].scope_target == "worker-1"

        # 6. Deactivate
        ks.deactivate(KillScope.AGENT, scope_target="worker-1")
        assert not ks.check(scope_target="worker-1").is_killed

    @pytest.mark.e2e
    def test_global_kill_overrides_all(self) -> None:
        """Test: global kill overrides all agent-level states."""
        ks = KillSwitch()
        ks.register_agent("a1")
        ks.register_agent("a2")

        # Agent-level pause
        ks.activate(KillLevel.PAUSE, KillScope.AGENT, scope_target="a1")

        # Global kill overrides everything
        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="emergency")

        status = ks.check(scope_target="a1")
        assert status.is_killed
        assert status.level == KillLevel.KILL
        assert status.scope == KillScope.GLOBAL

        # Even agents without individual kills are affected
        status = ks.check(scope_target="a2")
        assert status.is_killed
        assert status.scope == KillScope.GLOBAL

    @pytest.mark.e2e
    def test_cascading_kill_with_budget(self) -> None:
        """Test: budget exceeded -> cascading kill to children."""
        ks = KillSwitch()
        cascade = CascadingTerminator(killswitch=ks)
        budget = BudgetKillTrigger(killswitch=ks, kill_on_exceed=True)

        # Build hierarchy
        ks.register_agent("lead")
        ks.register_agent("worker-a", parent_id="lead")
        ks.register_agent("worker-b", parent_id="lead")

        # Set budget for lead
        budget.set_budget("lead", 50.0)

        # Track costs incrementally
        budget.track_cost("lead", 20.0)
        assert not ks.check(scope_target="lead").is_killed

        budget.track_cost("lead", 35.0)  # Total: $55 > $50
        assert ks.check(scope_target="lead").is_killed

        # Now cascade to children
        killed = cascade.cascade_kill("lead", KillLevel.KILL, reason="budget cascade")
        assert "lead" in killed
        assert "worker-a" in killed
        assert "worker-b" in killed

    @pytest.mark.e2e
    def test_multiple_scopes_and_levels(self) -> None:
        """Test complex multi-scope scenarios."""
        ks = KillSwitch()

        # Crew-level PAUSE
        ks.activate(KillLevel.PAUSE, KillScope.CREW, scope_target="crew-alpha")

        # Agent-level STOP on specific agent
        ks.activate(KillLevel.STOP, KillScope.AGENT, scope_target="worker-1")

        # Check: crew member (not worker-1) gets PAUSE from crew
        status = ks.check(scope_target="worker-2", crew_id="crew-alpha")
        assert status.is_killed
        assert status.level == KillLevel.PAUSE
        assert status.scope == KillScope.CREW

        # Check: worker-1 in crew gets CREW scope (higher priority)
        status = ks.check(scope_target="worker-1", crew_id="crew-alpha")
        assert status.is_killed
        assert status.scope == KillScope.CREW  # Crew has higher priority

        # Deactivate crew
        ks.deactivate(KillScope.CREW, scope_target="crew-alpha")

        # Now worker-1 still has agent-level STOP
        status = ks.check(scope_target="worker-1")
        assert status.is_killed
        assert status.level == KillLevel.STOP
        assert status.scope == KillScope.AGENT
