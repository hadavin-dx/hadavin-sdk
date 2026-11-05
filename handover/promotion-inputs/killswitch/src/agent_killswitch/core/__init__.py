"""Core kill switch components.

This package contains the core functionality:
- killswitch: Main KillSwitch class (unified API)
- heartbeat: HeartbeatMonitor for agent health tracking
- circuit_breaker: Circuit breaker pattern
- budget_kill: Budget-based kill triggers
- cascading: Cascading termination for agent hierarchies
- models: Data models
- enums: Enumerations
"""

from __future__ import annotations

from .enums import CircuitState, HeartbeatStatus, KillLevel, KillScope
from .models import (
    AgentRegistration,
    BudgetStatus,
    CircuitBreakerState,
    HeartbeatRecord,
    KillEvent,
    KillStatus,
)

__all__ = [
    "AgentRegistration",
    "BudgetStatus",
    "CircuitBreakerState",
    "CircuitState",
    "HeartbeatRecord",
    "HeartbeatStatus",
    "KillEvent",
    "KillLevel",
    "KillScope",
    "KillStatus",
]
