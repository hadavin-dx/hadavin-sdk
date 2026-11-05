"""agent-killswitch: Operational safety controls for autonomous AI agents.

Zero-dependency kill switch, heartbeat monitor, circuit breaker, and
budget controls for AI agents. Works with any framework (LangChain,
LangGraph, CrewAI, OpenAI Agents SDK, asyncio) or standalone.

Quick start::

    from agent_killswitch import KillSwitch, KillLevel, KillScope

    ks = KillSwitch()
    ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="emergency")
    status = ks.check()
    assert status.is_killed

Core classes:
    KillSwitch: Main kill switch with tiered levels and scoped targets.
    HeartbeatMonitor: Track agent health via periodic heartbeats.
    CircuitBreaker: Protect against cascading failures.
    BudgetKillTrigger: Kill agents that exceed their budget.
    CascadingTerminator: Propagate kills through agent hierarchies.

Decorators:
    killswitch_protected: Check kill switch before/after function calls.
    with_heartbeat: Send heartbeats during long-running operations.
    circuit_breaker: Wrap functions with circuit breaker protection.
"""

from __future__ import annotations

from ._version import __version__
from .core.budget_kill import BudgetKillTrigger
from .core.cascading import CascadingTerminator
from .core.circuit_breaker import CircuitBreaker, CircuitBreakerOpen
from .core.enums import CircuitState, HeartbeatStatus, KillLevel, KillScope
from .core.heartbeat import HeartbeatMonitor
from .core.killswitch import KillSwitch
from .core.models import (
    AgentRegistration,
    BudgetStatus,
    CircuitBreakerState,
    HeartbeatRecord,
    KillEvent,
    KillStatus,
)
from .decorators import KillSwitchTriggered, killswitch_protected, with_heartbeat
from .decorators import circuit_breaker as circuit_breaker_decorator

__all__ = [
    "AgentRegistration",
    "BudgetKillTrigger",
    "BudgetStatus",
    "CascadingTerminator",
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "CircuitBreakerState",
    "CircuitState",
    "HeartbeatMonitor",
    "HeartbeatRecord",
    "HeartbeatStatus",
    # Models
    "KillEvent",
    # Enums
    "KillLevel",
    "KillScope",
    "KillStatus",
    # Core classes
    "KillSwitch",
    "KillSwitchTriggered",
    # Version
    "__version__",
    "circuit_breaker_decorator",
    # Decorators
    "killswitch_protected",
    "with_heartbeat",
]
