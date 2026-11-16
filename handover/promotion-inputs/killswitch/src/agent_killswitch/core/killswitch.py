"""Main KillSwitch class -- the unified API for agent safety controls.

Provides a single entry point for:
- Activating/deactivating kill switches at tiered levels
- Checking kill status with scope priority resolution
- Registering agents in a hierarchy for cascading termination
- Audit trail of all kill events

The kill switch operates OUTSIDE the agent reasoning path -- it is checked
at the infrastructure/middleware level, not in the agent's prompt or
decision loop.

Fail-closed: If the backend is unreachable, the kill switch defaults
to KILLED state. Safety first.

Key scheme (configurable prefix):
    {prefix}global              -> level
    {prefix}crew:{scope_target} -> level
    {prefix}agent:{scope_target} -> level
    {prefix}task:{scope_target} -> level

Priority order: GLOBAL > CREW > AGENT > TASK
"""

from __future__ import annotations

import contextlib
import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ..backends.memory import InMemoryBackend
from .enums import LEVEL_LATENCY_GUARANTEE_MS, KillLevel, KillScope
from .models import AgentRegistration, KillEvent, KillStatus

logger = logging.getLogger(__name__)

# Scope priority: higher index = lower priority
_SCOPE_PRIORITY: list[KillScope] = [
    KillScope.GLOBAL,
    KillScope.CREW,
    KillScope.AGENT,
    KillScope.TASK,
]

# Key templates per scope
_KEY_TEMPLATES: dict[KillScope, str] = {
    KillScope.GLOBAL: "global",
    KillScope.CREW: "crew:{scope_target}",
    KillScope.AGENT: "agent:{scope_target}",
    KillScope.TASK: "task:{scope_target}",
}


class KillSwitch:
    """Operational safety kill switch for autonomous AI agents.

    The KillSwitch provides tiered emergency controls (PAUSE/STOP/KILL)
    across configurable scopes (GLOBAL/CREW/AGENT/TASK). It is designed
    to be checked at the infrastructure layer before every agent action.

    Thread-safe: All internal state is protected by a reentrant lock.
    Fail-closed: Backend failures result in KILLED status for safety.

    Example::

        from agent_killswitch import KillSwitch, KillLevel, KillScope

        ks = KillSwitch()

        # Register an agent
        ks.register_agent("agent-1")

        # Check status (returns KillStatus)
        status = ks.check("agent-1")
        if status.is_killed:
            print(f"Agent killed: {status.level}")

        # Activate kill switch
        ks.activate(KillLevel.STOP, KillScope.AGENT, "agent-1", reason="runaway")

        # Deactivate
        ks.deactivate(KillScope.AGENT, "agent-1")

    Args:
        backend: Storage backend. Defaults to InMemoryBackend.
        prefix: Key prefix for backend storage. Defaults to "".
        on_kill: Optional callback invoked on every activation.
            Signature: (event: KillEvent) -> None
        fail_closed: If True (default), backend errors result in KILLED.
            If False, backend errors result in safe (not killed).
    """

    def __init__(
        self,
        backend: Any = None,
        prefix: str = "",
        on_kill: Callable[[KillEvent], None] | None = None,
        fail_closed: bool = True,
    ) -> None:
        self._backend = backend if backend is not None else InMemoryBackend()
        self._prefix = prefix
        self._on_kill = on_kill
        self._fail_closed = fail_closed
        self._lock = threading.RLock()

        # Agent registry
        self._agents: dict[str, AgentRegistration] = {}

        # Audit trail
        self._events: list[KillEvent] = []

        # Activation reasons (stored alongside level)
        self._reasons: dict[str, str] = {}
        self._activation_times: dict[str, datetime] = {}

        logger.info(
            "KillSwitch initialized",
            extra={
                "backend": type(self._backend).__name__,
                "prefix": prefix,
                "fail_closed": fail_closed,
            },
        )

    # -- Key management --

    def _make_key(self, scope: KillScope, scope_target: str | None = None) -> str:
        """Build the storage key for a given scope.

        Args:
            scope: The kill scope.
            scope_target: Required for non-GLOBAL scopes.

        Returns:
            The full storage key including prefix.

        Raises:
            ValueError: If scope requires scope_target but none provided.
        """
        if scope != KillScope.GLOBAL and not scope_target:
            raise ValueError(f"scope_target required for {scope.value} scope")

        template = _KEY_TEMPLATES[scope]
        raw_key = template.format(scope_target=scope_target) if scope_target else template
        return f"{self._prefix}{raw_key}"

    # -- Core operations --

    def activate(
        self,
        level: KillLevel,
        scope: KillScope,
        scope_target: str | None = None,
        reason: str = "",
        activated_by: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> KillEvent:
        """Activate the kill switch at the specified level and scope.

        Sets the backend flag and returns a KillEvent with activation
        details. The latency is measured and logged.

        Latency guarantees: PAUSE <200ms, STOP <300ms, KILL <500ms.

        Args:
            level: The kill level (PAUSE, STOP, or KILL).
            scope: The scope (GLOBAL, CREW, AGENT, or TASK).
            scope_target: Target identifier (required for non-GLOBAL).
            reason: Human-readable reason for the activation.
            activated_by: Identifier of who/what activated the switch.
            metadata: Additional metadata for audit logging.

        Returns:
            KillEvent with activation details including latency.

        Raises:
            ValueError: If scope requires scope_target but none provided.
        """
        start = time.monotonic()

        key = self._make_key(scope, scope_target)

        with self._lock:
            try:
                self._backend.set(key, level.value)
            except Exception as exc:
                logger.error(
                    "KillSwitch backend SET failed, recording locally",
                    extra={"key": key, "error": str(exc)},
                )

            # Store reason and activation time
            self._reasons[key] = reason
            self._activation_times[key] = datetime.now(timezone.utc)

        elapsed_ms = (time.monotonic() - start) * 1000

        event = KillEvent(
            event_id=uuid4().hex,
            level=level,
            scope=scope,
            scope_target=scope_target,
            reason=reason,
            activated_by=activated_by,
            timestamp=datetime.now(timezone.utc),
            latency_ms=elapsed_ms,
            metadata=metadata or {},
        )

        with self._lock:
            self._events.append(event)

        # Log at appropriate severity
        log_extra = {
            "event_id": event.event_id,
            "level": level.value,
            "scope": scope.value,
            "scope_target": scope_target,
            "latency_ms": round(elapsed_ms, 2),
            "activated_by": activated_by,
            "reason": reason,
        }

        if level == KillLevel.KILL:
            logger.critical("kill_switch_KILL_activated", extra=log_extra)
        elif level == KillLevel.STOP:
            logger.warning("kill_switch_STOP_activated", extra=log_extra)
        else:
            logger.info("kill_switch_PAUSE_activated", extra=log_extra)

        # Check latency guarantee
        guarantee = LEVEL_LATENCY_GUARANTEE_MS[level]
        if elapsed_ms > guarantee:
            logger.error(
                "kill_switch_latency_exceeded",
                extra={
                    "level": level.value,
                    "guarantee_ms": guarantee,
                    "actual_ms": round(elapsed_ms, 2),
                },
            )

        # Fire callback
        if self._on_kill is not None:
            try:
                self._on_kill(event)
            except Exception as exc:
                logger.error(
                    "kill_switch on_kill callback error",
                    extra={"error": str(exc)},
                )

        return event

    def deactivate(
        self,
        scope: KillScope,
        scope_target: str | None = None,
        deactivated_by: str = "system",
    ) -> None:
        """Deactivate the kill switch for the specified scope.

        Requires explicit deactivation -- there is no auto-expire TTL
        to prevent accidental resumption of compromised agents.

        Args:
            scope: The scope to deactivate.
            scope_target: Required for non-GLOBAL scopes.
            deactivated_by: Identifier of who/what deactivated.

        Raises:
            ValueError: If scope requires scope_target but none provided.
        """
        key = self._make_key(scope, scope_target)

        with self._lock:
            try:
                self._backend.delete(key)
            except Exception as exc:
                logger.error(
                    "KillSwitch backend DELETE failed",
                    extra={"key": key, "error": str(exc)},
                )
            self._reasons.pop(key, None)
            self._activation_times.pop(key, None)

        logger.info(
            "kill_switch_deactivated",
            extra={
                "scope": scope.value,
                "scope_target": scope_target,
                "deactivated_by": deactivated_by,
            },
        )

    def check(
        self,
        scope_target: str | None = None,
        crew_id: str | None = None,
    ) -> KillStatus:
        """Check if any kill switch is active for the given target.

        Checks backend flags in priority order: GLOBAL > CREW > AGENT > TASK.
        Returns the highest-priority active kill switch level.

        Fail-closed: If the backend is unreachable and fail_closed is True,
        returns KILLED status.

        Args:
            scope_target: The agent_id or task_id to check. Also used for
                AGENT and TASK scope lookups.
            crew_id: Optional crew_id for CREW scope lookup.

        Returns:
            KillStatus with is_killed=True/False and details.
        """
        # Build keys to check in priority order
        keys: list[tuple[KillScope, str | None, str]] = []

        # Global always checked
        try:
            global_key = self._make_key(KillScope.GLOBAL)
            keys.append((KillScope.GLOBAL, None, global_key))
        except ValueError:
            pass

        # Crew scope
        if crew_id:
            try:
                crew_key = self._make_key(KillScope.CREW, crew_id)
                keys.append((KillScope.CREW, crew_id, crew_key))
            except ValueError:
                pass

        # Agent scope
        if scope_target:
            try:
                agent_key = self._make_key(KillScope.AGENT, scope_target)
                keys.append((KillScope.AGENT, scope_target, agent_key))
            except ValueError:
                pass

            # Task scope
            try:
                task_key = self._make_key(KillScope.TASK, scope_target)
                keys.append((KillScope.TASK, scope_target, task_key))
            except ValueError:
                pass

        if not keys:
            return KillStatus.safe()

        # Get all values in one operation
        raw_keys = [k[2] for k in keys]
        try:
            values = self._backend.get_many(raw_keys)
        except Exception as exc:
            logger.error(
                "KillSwitch backend GET_MANY failed",
                extra={"keys": raw_keys, "error": str(exc)},
            )
            if self._fail_closed:
                return KillStatus.killed(
                    level=KillLevel.KILL,
                    scope=KillScope.GLOBAL,
                    reason=f"Backend failure (fail-closed): {exc}",
                )
            return KillStatus.safe()

        # Return first (highest-priority) active level
        for (scope, target, key), value in zip(keys, values, strict=False):
            if value is not None:
                try:
                    level = KillLevel(value)
                except ValueError:
                    logger.warning(
                        "Invalid kill level in backend",
                        extra={"key": key, "value": value},
                    )
                    continue

                with self._lock:
                    reason = self._reasons.get(key, "")
                    activated_at = self._activation_times.get(key)

                return KillStatus.killed(
                    level=level,
                    scope=scope,
                    scope_target=target,
                    reason=reason,
                    activated_at=activated_at,
                )

        return KillStatus.safe()

    # -- Agent registration --

    def register_agent(
        self,
        agent_id: str,
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentRegistration:
        """Register an agent in the kill switch hierarchy.

        Args:
            agent_id: Unique identifier for the agent.
            parent_id: ID of the parent agent for cascading, or None.
            metadata: Optional metadata about the agent.

        Returns:
            The AgentRegistration record.

        Raises:
            ValueError: If parent_id is specified but not registered.
        """
        if parent_id is not None:
            with self._lock:
                if parent_id not in self._agents:
                    raise ValueError(f"Parent agent not registered: {parent_id}")

        registration = AgentRegistration(
            agent_id=agent_id,
            parent_id=parent_id,
            metadata=metadata or {},
        )

        with self._lock:
            self._agents[agent_id] = registration

        logger.info(
            "agent_registered",
            extra={
                "agent_id": agent_id,
                "parent_id": parent_id,
            },
        )
        return registration

    def unregister_agent(self, agent_id: str) -> None:
        """Remove an agent from the hierarchy.

        Also cleans up any agent-scoped kill switch for this agent.

        Args:
            agent_id: The agent to unregister.
        """
        with self._lock:
            self._agents.pop(agent_id, None)

        # Clean up agent-scoped kill switch
        with contextlib.suppress(ValueError, Exception):
            self.deactivate(KillScope.AGENT, agent_id, deactivated_by="unregister")

        logger.info("agent_unregistered", extra={"agent_id": agent_id})

    def get_children(self, agent_id: str) -> list[str]:
        """Get IDs of all direct children of an agent.

        Args:
            agent_id: The parent agent ID.

        Returns:
            List of child agent IDs.
        """
        with self._lock:
            return [reg.agent_id for reg in self._agents.values() if reg.parent_id == agent_id]

    def get_all_descendants(self, agent_id: str) -> list[str]:
        """Get IDs of all descendants (children, grandchildren, etc.).

        Args:
            agent_id: The root agent ID.

        Returns:
            List of all descendant agent IDs in breadth-first order.
        """
        descendants: list[str] = []
        queue = self.get_children(agent_id)

        while queue:
            child = queue.pop(0)
            descendants.append(child)
            queue.extend(self.get_children(child))

        return descendants

    # -- Status and audit --

    def get_status(self) -> dict[str, Any]:
        """Return all active kill switches across all scopes.

        Returns:
            Dictionary with active kill switches and counts.
        """
        status: dict[str, Any] = {
            "global": None,
            "crews": {},
            "agents": {},
            "tasks": {},
            "total_active": 0,
            "registered_agents": 0,
        }

        # Check global
        try:
            global_key = self._make_key(KillScope.GLOBAL)
            global_val = self._backend.get(global_key)
            if global_val:
                status["global"] = global_val
                status["total_active"] += 1
        except (ValueError, Exception):
            pass

        # Scan for scoped keys
        for scope_name, scope_enum in [
            ("crews", KillScope.CREW),
            ("agents", KillScope.AGENT),
            ("tasks", KillScope.TASK),
        ]:
            try:
                pattern = f"{self._prefix}{scope_enum.value}:*"
                matched_keys = self._backend.keys(pattern)
                for key in matched_keys:
                    val = self._backend.get(key)
                    if val:
                        # Extract target from key
                        parts = key.split(":", 1)
                        target = parts[1] if len(parts) > 1 else key
                        status[scope_name][target] = val
                        status["total_active"] += 1
            except Exception:
                pass

        with self._lock:
            status["registered_agents"] = len(self._agents)

        return status

    def get_events(self, limit: int = 100) -> list[KillEvent]:
        """Return the most recent kill events.

        Args:
            limit: Maximum number of events to return.

        Returns:
            List of KillEvent records, most recent first.
        """
        with self._lock:
            return list(reversed(self._events[-limit:]))

    def get_event_count(self) -> dict[str, int]:
        """Return count of events by level.

        Returns:
            Dictionary of level -> count.
        """
        counts: dict[str, int] = {"pause": 0, "stop": 0, "kill": 0}
        with self._lock:
            for event in self._events:
                counts[event.level.value] += 1
        return counts

    @property
    def is_active(self) -> bool:
        """Check if any kill switch is currently active globally.

        Returns:
            True if the global kill switch is active.
        """
        try:
            key = self._make_key(KillScope.GLOBAL)
            val = self._backend.get(key)
            return val is not None
        except Exception:
            return self._fail_closed
