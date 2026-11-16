"""Unit tests for BudgetKillTrigger."""

from __future__ import annotations

from agent_killswitch import BudgetKillTrigger, KillLevel, KillSwitch
from agent_killswitch.backends.memory import InMemoryBackend


class TestBudgetTracking:
    """Tests for cost tracking."""

    def test_track_cost_accumulates(self, budget_trigger: BudgetKillTrigger) -> None:
        budget_trigger.set_budget("a1", 100.0)
        budget_trigger.track_cost("a1", 25.0)
        budget_trigger.track_cost("a1", 30.0)
        status = budget_trigger.get_status("a1")
        assert status is not None
        assert status.current_cost == 55.0

    def test_track_cost_calculates_utilization(self, budget_trigger: BudgetKillTrigger) -> None:
        budget_trigger.set_budget("a1", 100.0)
        budget_trigger.track_cost("a1", 50.0)
        status = budget_trigger.get_status("a1")
        assert status is not None
        assert abs(status.utilization - 0.5) < 0.001

    def test_track_cost_auto_creates_budget(self, budget_trigger: BudgetKillTrigger) -> None:
        # Default budget is 100.0
        result = budget_trigger.track_cost("new-agent", 10.0)
        assert result.current_cost == 10.0
        assert result.budget_limit == 100.0

    def test_unlimited_budget(self) -> None:
        trigger = BudgetKillTrigger(default_budget=0.0)
        trigger.track_cost("a1", 99999.0)
        status = trigger.get_status("a1")
        assert status is not None
        assert status.utilization == 0.0


class TestBudgetAlerts:
    """Tests for alert thresholds."""

    def test_alert_at_50_percent(self) -> None:
        alerts: list[tuple[str, float]] = []
        trigger = BudgetKillTrigger(
            default_budget=100.0,
            on_alert=lambda aid, u: alerts.append((aid, u)),
        )
        trigger.set_budget("a1", 100.0)
        trigger.track_cost("a1", 51.0)
        assert len(alerts) == 1
        assert alerts[0][0] == "a1"
        assert alerts[0][1] >= 0.5

    def test_alert_at_80_percent(self) -> None:
        alerts: list[tuple[str, float]] = []
        trigger = BudgetKillTrigger(
            default_budget=100.0,
            on_alert=lambda aid, u: alerts.append((aid, u)),
        )
        trigger.set_budget("a1", 100.0)
        trigger.track_cost("a1", 81.0)
        # Should fire 50% and 80% alerts
        assert len(alerts) == 2

    def test_alert_fires_only_once(self) -> None:
        alerts: list[tuple[str, float]] = []
        trigger = BudgetKillTrigger(
            default_budget=100.0,
            on_alert=lambda aid, u: alerts.append((aid, u)),
        )
        trigger.set_budget("a1", 100.0)
        trigger.track_cost("a1", 51.0)
        trigger.track_cost("a1", 5.0)
        trigger.track_cost("a1", 5.0)
        # 50% alert should only fire once
        fifty_alerts = [a for a in alerts if a[1] < 0.8]
        assert len(fifty_alerts) == 1


class TestBudgetExceeded:
    """Tests for budget exceeded behavior."""

    def test_kill_on_exceed(self) -> None:
        backend = InMemoryBackend()
        ks = KillSwitch(backend=backend)
        trigger = BudgetKillTrigger(killswitch=ks, kill_on_exceed=True)
        trigger.set_budget("a1", 50.0)
        trigger.track_cost("a1", 55.0)
        # Agent should be killed
        status = ks.check(scope_target="a1")
        assert status.is_killed
        assert status.level == KillLevel.KILL

    def test_pause_on_exceed(self) -> None:
        backend = InMemoryBackend()
        ks = KillSwitch(backend=backend)
        trigger = BudgetKillTrigger(killswitch=ks, kill_on_exceed=False)
        trigger.set_budget("a1", 50.0)
        trigger.track_cost("a1", 55.0)
        status = ks.check(scope_target="a1")
        assert status.is_killed
        assert status.level == KillLevel.PAUSE

    def test_on_budget_exceeded_callback(self) -> None:
        exceeded: list[tuple[str, float, float]] = []
        trigger = BudgetKillTrigger(
            default_budget=50.0,
            on_budget_exceeded=lambda a, c, level: exceeded.append((a, c, level)),
        )
        trigger.set_budget("a1", 50.0)
        trigger.track_cost("a1", 55.0)
        assert len(exceeded) == 1
        assert exceeded[0][0] == "a1"
        assert exceeded[0][1] == 55.0
        assert exceeded[0][2] == 50.0


class TestBudgetReset:
    """Tests for budget reset."""

    def test_reset_cost(self, budget_trigger: BudgetKillTrigger) -> None:
        budget_trigger.set_budget("a1", 100.0)
        budget_trigger.track_cost("a1", 75.0)
        budget_trigger.reset_cost("a1")
        status = budget_trigger.get_status("a1")
        assert status is not None
        assert status.current_cost == 0.0
        assert status.utilization == 0.0

    def test_reset_clears_alerts(self, budget_trigger: BudgetKillTrigger) -> None:
        budget_trigger.set_budget("a1", 100.0)
        budget_trigger.track_cost("a1", 90.0)
        budget_trigger.reset_cost("a1")
        status = budget_trigger.get_status("a1")
        assert status is not None
        assert len(status.alerts_fired) == 0


class TestBudgetManagement:
    """Tests for budget management operations."""

    def test_remove_agent(self, budget_trigger: BudgetKillTrigger) -> None:
        budget_trigger.set_budget("a1", 100.0)
        budget_trigger.remove_agent("a1")
        assert budget_trigger.get_status("a1") is None

    def test_get_all_statuses(self, budget_trigger: BudgetKillTrigger) -> None:
        budget_trigger.set_budget("a1", 100.0)
        budget_trigger.set_budget("a2", 200.0)
        budget_trigger.track_cost("a1", 10.0)
        all_statuses = budget_trigger.get_all_statuses()
        assert len(all_statuses) == 2
        assert all_statuses["a1"].current_cost == 10.0

    def test_tracked_agents_count(self, budget_trigger: BudgetKillTrigger) -> None:
        assert budget_trigger.tracked_agents == 0
        budget_trigger.set_budget("a1", 50.0)
        budget_trigger.set_budget("a2", 50.0)
        assert budget_trigger.tracked_agents == 2
