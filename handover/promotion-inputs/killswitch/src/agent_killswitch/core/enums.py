"""Enumerations for agent-killswitch.

Defines the core enums used throughout the library:
- KillLevel: Tiered severity (PAUSE/STOP/KILL)
- KillScope: Breadth of impact (GLOBAL/CREW/AGENT/TASK)
- HeartbeatStatus: Agent health states
- CircuitState: Circuit breaker states
"""

from __future__ import annotations

from enum import Enum


class KillLevel(str, Enum):
    """Kill switch activation tiers with latency guarantees.

    Each tier escalates the severity of the kill switch:
    - PAUSE: Graceful -- stop new tasks, let in-flight complete (<200ms)
    - STOP:  Forceful -- checkpoint in-flight, pause all (<300ms)
    - KILL:  Immediate -- terminate everything (<500ms)

    Numeric ordering: PAUSE < STOP < KILL (higher = more severe).
    """

    PAUSE = "pause"
    STOP = "stop"
    KILL = "kill"

    @property
    def severity(self) -> int:
        """Return numeric severity for comparison.

        Returns:
            Integer severity: PAUSE=1, STOP=2, KILL=3.
        """
        return _SEVERITY_MAP[self]

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, KillLevel):
            return NotImplemented
        return self.severity > other.severity

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, KillLevel):
            return NotImplemented
        return self.severity >= other.severity

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, KillLevel):
            return NotImplemented
        return self.severity < other.severity

    def __le__(self, other: object) -> bool:
        if not isinstance(other, KillLevel):
            return NotImplemented
        return self.severity <= other.severity


_SEVERITY_MAP: dict[KillLevel, int] = {
    KillLevel.PAUSE: 1,
    KillLevel.STOP: 2,
    KillLevel.KILL: 3,
}

# Latency guarantees per level (milliseconds)
LEVEL_LATENCY_GUARANTEE_MS: dict[KillLevel, float] = {
    KillLevel.PAUSE: 200.0,
    KillLevel.STOP: 300.0,
    KillLevel.KILL: 500.0,
}


class KillScope(str, Enum):
    """Kill switch scope -- how broadly the kill switch applies.

    Priority order for checking: GLOBAL > CREW > AGENT > TASK.
    A global KILL overrides a crew-level PAUSE.
    """

    GLOBAL = "global"
    CREW = "crew"
    AGENT = "agent"
    TASK = "task"


class HeartbeatStatus(str, Enum):
    """Health status of an agent based on heartbeat monitoring.

    - ALIVE: Heartbeat received within expected interval
    - SUSPECT: One or more missed heartbeats, not yet dead
    - DEAD: Exceeded miss threshold, considered unresponsive
    - UNKNOWN: No heartbeat data available
    """

    ALIVE = "alive"
    SUSPECT = "suspect"
    DEAD = "dead"
    UNKNOWN = "unknown"


class CircuitState(str, Enum):
    """Circuit breaker states.

    - CLOSED: Normal operation, requests pass through
    - OPEN: Failing, requests are rejected immediately
    - HALF_OPEN: Testing recovery, limited requests pass through
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
