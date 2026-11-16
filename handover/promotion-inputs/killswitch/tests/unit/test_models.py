"""Unit tests for data models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_killswitch.core.enums import (
    CircuitState,
    HeartbeatStatus,
    KillLevel,
    KillScope,
)
from agent_killswitch.core.models import (
    AgentRegistration,
    BudgetStatus,
    CircuitBreakerState,
    HeartbeatRecord,
    KillEvent,
    KillStatus,
)


class TestKillLevel:
    """Tests for KillLevel enum."""

    def test_values(self) -> None:
        assert KillLevel.PAUSE.value == "pause"
        assert KillLevel.STOP.value == "stop"
        assert KillLevel.KILL.value == "kill"

    def test_severity_ordering(self) -> None:
        assert KillLevel.PAUSE < KillLevel.STOP
        assert KillLevel.STOP < KillLevel.KILL
        assert KillLevel.KILL > KillLevel.PAUSE

    def test_severity_values(self) -> None:
        assert KillLevel.PAUSE.severity == 1
        assert KillLevel.STOP.severity == 2
        assert KillLevel.KILL.severity == 3

    def test_comparison_operators(self) -> None:
        assert KillLevel.PAUSE <= KillLevel.PAUSE
        assert KillLevel.PAUSE >= KillLevel.PAUSE
        assert not (KillLevel.KILL < KillLevel.PAUSE)

    def test_from_string(self) -> None:
        assert KillLevel("pause") == KillLevel.PAUSE
        assert KillLevel("stop") == KillLevel.STOP
        assert KillLevel("kill") == KillLevel.KILL


class TestKillScope:
    """Tests for KillScope enum."""

    def test_values(self) -> None:
        assert KillScope.GLOBAL.value == "global"
        assert KillScope.CREW.value == "crew"
        assert KillScope.AGENT.value == "agent"
        assert KillScope.TASK.value == "task"


class TestKillStatus:
    """Tests for KillStatus dataclass."""

    def test_safe_factory(self) -> None:
        status = KillStatus.safe()
        assert not status.is_killed
        assert status.level is None
        assert status.scope is None

    def test_killed_factory(self) -> None:
        status = KillStatus.killed(
            level=KillLevel.KILL,
            scope=KillScope.GLOBAL,
            reason="test",
        )
        assert status.is_killed
        assert status.level == KillLevel.KILL
        assert status.scope == KillScope.GLOBAL
        assert status.reason == "test"

    def test_killed_with_all_fields(self) -> None:
        now = datetime.now(timezone.utc)
        status = KillStatus.killed(
            level=KillLevel.STOP,
            scope=KillScope.AGENT,
            scope_target="a1",
            reason="runaway",
            activated_at=now,
        )
        assert status.scope_target == "a1"
        assert status.activated_at == now


class TestKillEvent:
    """Tests for KillEvent dataclass."""

    def test_frozen(self) -> None:
        event = KillEvent(
            event_id="e1",
            level=KillLevel.KILL,
            scope=KillScope.GLOBAL,
            scope_target=None,
            reason="test",
            activated_by="system",
            timestamp=datetime.now(timezone.utc),
            latency_ms=1.5,
        )
        with pytest.raises(AttributeError):
            event.level = KillLevel.PAUSE  # type: ignore[misc]

    def test_metadata_default(self) -> None:
        event = KillEvent(
            event_id="e1",
            level=KillLevel.KILL,
            scope=KillScope.GLOBAL,
            scope_target=None,
            reason="test",
            activated_by="system",
            timestamp=datetime.now(timezone.utc),
            latency_ms=1.5,
        )
        assert event.metadata == {}


class TestHeartbeatStatus:
    """Tests for HeartbeatStatus enum."""

    def test_values(self) -> None:
        assert HeartbeatStatus.ALIVE.value == "alive"
        assert HeartbeatStatus.SUSPECT.value == "suspect"
        assert HeartbeatStatus.DEAD.value == "dead"
        assert HeartbeatStatus.UNKNOWN.value == "unknown"


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_values(self) -> None:
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestAgentRegistration:
    """Tests for AgentRegistration dataclass."""

    def test_defaults(self) -> None:
        reg = AgentRegistration(agent_id="a1")
        assert reg.agent_id == "a1"
        assert reg.parent_id is None
        assert reg.registered_at is not None

    def test_with_parent(self) -> None:
        reg = AgentRegistration(agent_id="a1", parent_id="p1")
        assert reg.parent_id == "p1"


class TestHeartbeatRecord:
    """Tests for HeartbeatRecord dataclass."""

    def test_defaults(self) -> None:
        rec = HeartbeatRecord(agent_id="a1")
        assert rec.agent_id == "a1"
        assert rec.last_heartbeat is None
        assert rec.status == HeartbeatStatus.UNKNOWN
        assert rec.miss_count == 0
        assert rec.interval_seconds == 5.0


class TestBudgetStatus:
    """Tests for BudgetStatus dataclass."""

    def test_defaults(self) -> None:
        bs = BudgetStatus(agent_id="a1")
        assert bs.budget_limit == 0.0
        assert bs.current_cost == 0.0
        assert bs.utilization == 0.0
        assert len(bs.alert_thresholds) == 3

    def test_custom_thresholds(self) -> None:
        bs = BudgetStatus(agent_id="a1", alert_thresholds=[0.25, 0.75])
        assert len(bs.alert_thresholds) == 2


class TestCircuitBreakerState:
    """Tests for CircuitBreakerState dataclass."""

    def test_defaults(self) -> None:
        cbs = CircuitBreakerState(name="test")
        assert cbs.state == CircuitState.CLOSED
        assert cbs.failure_count == 0
        assert cbs.failure_threshold == 5
        assert cbs.recovery_timeout == 30.0
