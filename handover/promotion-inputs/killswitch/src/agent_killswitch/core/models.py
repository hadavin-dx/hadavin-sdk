"""Data models for agent-killswitch.

Defines the core data structures used throughout the library.
All models are dataclasses for zero-dependency operation (no Pydantic required).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .enums import CircuitState, HeartbeatStatus, KillLevel, KillScope


@dataclass(frozen=True)
class KillEvent:
    """Record of a kill switch activation event.

    Immutable record that captures all details of a kill switch
    activation for audit trail purposes.

    Attributes:
        event_id: Unique identifier for this event.
        level: The kill level activated (PAUSE/STOP/KILL).
        scope: The scope of the activation.
        scope_target: Target identifier (agent_id, crew_id, etc.).
        reason: Human-readable reason for the activation.
        activated_by: Identifier of who/what activated the switch.
        timestamp: UTC timestamp of the activation.
        latency_ms: Activation latency in milliseconds.
        metadata: Additional metadata for audit logging.
    """

    event_id: str
    level: KillLevel
    scope: KillScope
    scope_target: str | None
    reason: str
    activated_by: str
    timestamp: datetime
    latency_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KillStatus:
    """Current status of a kill switch check.

    Returned by KillSwitch.check() to provide full status information.

    Attributes:
        is_killed: Whether any kill switch is active.
        level: The active kill level, or None if not killed.
        scope: The scope that matched, or None.
        scope_target: The target that matched, or None.
        reason: The reason for the kill, or None.
        activated_at: When the kill was activated, or None.
    """

    is_killed: bool
    level: KillLevel | None = None
    scope: KillScope | None = None
    scope_target: str | None = None
    reason: str | None = None
    activated_at: datetime | None = None

    @staticmethod
    def safe() -> KillStatus:
        """Return a safe (not killed) status."""
        return KillStatus(is_killed=False)

    @staticmethod
    def killed(
        level: KillLevel,
        scope: KillScope,
        scope_target: str | None = None,
        reason: str = "",
        activated_at: datetime | None = None,
    ) -> KillStatus:
        """Return a killed status with details."""
        return KillStatus(
            is_killed=True,
            level=level,
            scope=scope,
            scope_target=scope_target,
            reason=reason,
            activated_at=activated_at,
        )


@dataclass
class AgentRegistration:
    """Registration record for an agent in the kill switch system.

    Attributes:
        agent_id: Unique identifier for the agent.
        parent_id: ID of the parent agent (for cascading), or None if root.
        registered_at: UTC timestamp of registration.
        metadata: Additional metadata about the agent.
    """

    agent_id: str
    parent_id: str | None = None
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HeartbeatRecord:
    """Record of an agent's heartbeat state.

    Attributes:
        agent_id: The agent being monitored.
        last_heartbeat: UTC timestamp of last heartbeat.
        status: Current health status.
        miss_count: Number of consecutive missed heartbeats.
        interval_seconds: Expected heartbeat interval.
    """

    agent_id: str
    last_heartbeat: datetime | None = None
    status: HeartbeatStatus = HeartbeatStatus.UNKNOWN
    miss_count: int = 0
    interval_seconds: float = 5.0


@dataclass
class CircuitBreakerState:
    """State of a circuit breaker.

    Attributes:
        name: Name/identifier of the circuit breaker.
        state: Current circuit state.
        failure_count: Consecutive failure count.
        success_count: Consecutive success count in HALF_OPEN state.
        last_failure_time: When the last failure occurred.
        last_state_change: When the state last changed.
        failure_threshold: Number of failures to trip the breaker.
        recovery_timeout: Seconds to wait before trying HALF_OPEN.
        half_open_max_calls: Max calls allowed in HALF_OPEN state.
    """

    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float | None = None
    last_state_change: float = field(default_factory=lambda: 0.0)
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 1


@dataclass
class BudgetStatus:
    """Budget tracking status for an agent.

    Attributes:
        agent_id: The agent being tracked.
        budget_limit: Maximum allowed cost.
        current_cost: Current accumulated cost.
        utilization: Budget utilization as a fraction (0.0 to 1.0+).
        alert_thresholds: Thresholds that trigger alerts.
        alerts_fired: Thresholds that have already fired alerts.
    """

    agent_id: str
    budget_limit: float = 0.0
    current_cost: float = 0.0
    utilization: float = 0.0
    alert_thresholds: list[float] = field(default_factory=lambda: [0.50, 0.80, 0.95])
    alerts_fired: set[float] = field(default_factory=set)
