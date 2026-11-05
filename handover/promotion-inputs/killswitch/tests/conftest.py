"""Shared test fixtures for agent-killswitch."""

from __future__ import annotations

import pytest

from agent_killswitch import (
    BudgetKillTrigger,
    CircuitBreaker,
    HeartbeatMonitor,
    KillSwitch,
)
from agent_killswitch.backends.memory import InMemoryBackend
from agent_killswitch.core.cascading import CascadingTerminator


@pytest.fixture
def backend() -> InMemoryBackend:
    """Fresh in-memory backend for each test."""
    return InMemoryBackend()


@pytest.fixture
def killswitch(backend: InMemoryBackend) -> KillSwitch:
    """Fresh KillSwitch with in-memory backend."""
    return KillSwitch(backend=backend)


@pytest.fixture
def heartbeat_monitor() -> HeartbeatMonitor:
    """Fresh HeartbeatMonitor with short interval for testing."""
    monitor = HeartbeatMonitor(
        interval_seconds=0.1,
        miss_threshold=3,
    )
    yield monitor
    monitor.shutdown()


@pytest.fixture
def circuit_breaker() -> CircuitBreaker:
    """Fresh CircuitBreaker with low thresholds for testing."""
    return CircuitBreaker(
        name="test",
        failure_threshold=3,
        recovery_timeout=0.5,
    )


@pytest.fixture
def budget_trigger(killswitch: KillSwitch) -> BudgetKillTrigger:
    """Fresh BudgetKillTrigger with KillSwitch."""
    return BudgetKillTrigger(
        killswitch=killswitch,
        default_budget=100.0,
        alert_thresholds=[0.50, 0.80, 0.95],
    )


@pytest.fixture
def cascading(killswitch: KillSwitch) -> CascadingTerminator:
    """Fresh CascadingTerminator with KillSwitch."""
    return CascadingTerminator(killswitch=killswitch)
