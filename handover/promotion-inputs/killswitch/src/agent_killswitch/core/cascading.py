"""Cascading termination for agent hierarchies.

When a parent agent is killed, all children cascade. Supports
configurable cascade delay and orphan detection/cleanup.

Thread-safe: All state is protected by a reentrant lock.
No external dependencies: Uses only Python stdlib.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from typing import Any

from .enums import KillLevel, KillScope

logger = logging.getLogger(__name__)


class CascadingTerminator:
    """Manages cascading termination through agent hierarchies.

    When a parent agent is killed, the CascadingTerminator propagates
    the kill to all children (and their children, recursively) with
    a configurable delay between each cascade level.

    Example::

        from agent_killswitch import KillSwitch, CascadingTerminator

        ks = KillSwitch()
        cascade = CascadingTerminator(killswitch=ks, cascade_delay=0.5)

        # Build hierarchy
        ks.register_agent("parent")
        ks.register_agent("child-1", parent_id="parent")
        ks.register_agent("child-2", parent_id="parent")
        ks.register_agent("grandchild", parent_id="child-1")

        # Kill parent -> children and grandchild cascade
        cascade.cascade_kill("parent", level=KillLevel.KILL, reason="runaway")

    Args:
        killswitch: The KillSwitch instance that manages agent state.
        cascade_delay: Seconds to wait between cascade levels. Default 0.0.
        on_cascade: Callback when a kill cascades to a child.
            Signature: (parent_id, child_id, level) -> None
        on_orphan_detected: Callback when an orphan agent is detected.
            Signature: (agent_id,) -> None
    """

    def __init__(
        self,
        killswitch: Any,
        cascade_delay: float = 0.0,
        on_cascade: Callable[[str, str, KillLevel], None] | None = None,
        on_orphan_detected: Callable[[str], None] | None = None,
    ) -> None:
        self._ks = killswitch
        self._cascade_delay = cascade_delay
        self._on_cascade = on_cascade
        self._on_orphan_detected = on_orphan_detected
        self._lock = threading.RLock()

    def cascade_kill(
        self,
        agent_id: str,
        level: KillLevel = KillLevel.KILL,
        reason: str = "",
        activated_by: str = "cascade",
    ) -> list[str]:
        """Kill an agent and cascade to all descendants.

        Activates the kill switch on the specified agent, then
        recursively cascades to all children with optional delay.

        Args:
            agent_id: The root agent to kill.
            level: Kill level to apply. Default KILL.
            reason: Reason for the kill.
            activated_by: Who initiated the cascade.

        Returns:
            List of all agent IDs that were killed (including root).
        """
        killed: list[str] = []

        # Kill the root agent
        try:
            self._ks.activate(
                level=level,
                scope=KillScope.AGENT,
                scope_target=agent_id,
                reason=reason,
                activated_by=activated_by,
            )
            killed.append(agent_id)
        except Exception as exc:
            logger.error(
                "cascade_kill_root_failed",
                extra={"agent_id": agent_id, "error": str(exc)},
            )
            return killed

        # Cascade to children
        children = self._ks.get_children(agent_id)
        for child_id in children:
            if self._cascade_delay > 0:
                time.sleep(self._cascade_delay)

            cascade_reason = f"Cascade from parent {agent_id}: {reason}"

            try:
                self._ks.activate(
                    level=level,
                    scope=KillScope.AGENT,
                    scope_target=child_id,
                    reason=cascade_reason,
                    activated_by=f"cascade:{agent_id}",
                )
                killed.append(child_id)

                logger.info(
                    "cascade_kill_child",
                    extra={
                        "parent_id": agent_id,
                        "child_id": child_id,
                        "level": level.value,
                    },
                )

                # Fire callback
                if self._on_cascade is not None:
                    try:
                        self._on_cascade(agent_id, child_id, level)
                    except Exception as exc:
                        logger.error(
                            "on_cascade callback error",
                            extra={"error": str(exc)},
                        )

                # Recurse into grandchildren
                grandchildren_killed = self.cascade_kill(
                    child_id,
                    level=level,
                    reason=cascade_reason,
                    activated_by=f"cascade:{agent_id}",
                )
                # Avoid duplicates (child_id already added)
                for gid in grandchildren_killed:
                    if gid not in killed:
                        killed.append(gid)

            except Exception as exc:
                logger.error(
                    "cascade_kill_child_failed",
                    extra={"child_id": child_id, "error": str(exc)},
                )

        logger.info(
            "cascade_kill_complete",
            extra={
                "root_agent": agent_id,
                "total_killed": len(killed),
                "killed_agents": killed,
            },
        )

        return killed

    def detect_orphans(self) -> list[str]:
        """Detect orphaned agents (parent is dead/unregistered).

        An orphan is an agent whose parent_id is set but the parent
        is not registered in the kill switch.

        Returns:
            List of orphaned agent IDs.
        """
        orphans: list[str] = []

        with self._lock:
            # Access the killswitch's agent registry
            if not hasattr(self._ks, "_agents"):
                return orphans

            agents = dict(self._ks._agents)

        for agent_id, registration in agents.items():
            if registration.parent_id is not None and registration.parent_id not in agents:
                orphans.append(agent_id)

                if self._on_orphan_detected is not None:
                    try:
                        self._on_orphan_detected(agent_id)
                    except Exception as exc:
                        logger.error(
                            "on_orphan_detected callback error",
                            extra={"error": str(exc)},
                        )

        if orphans:
            logger.warning(
                "orphan_agents_detected",
                extra={"count": len(orphans), "agents": orphans},
            )

        return orphans

    def cleanup_orphans(
        self,
        level: KillLevel = KillLevel.STOP,
        reason: str = "Orphan cleanup",
    ) -> list[str]:
        """Detect and kill orphaned agents.

        Args:
            level: Kill level to apply to orphans. Default STOP.
            reason: Reason for the cleanup.

        Returns:
            List of killed orphan agent IDs.
        """
        orphans = self.detect_orphans()
        killed: list[str] = []

        for agent_id in orphans:
            try:
                self._ks.activate(
                    level=level,
                    scope=KillScope.AGENT,
                    scope_target=agent_id,
                    reason=reason,
                    activated_by="orphan_cleanup",
                )
                killed.append(agent_id)
            except Exception as exc:
                logger.error(
                    "orphan_cleanup_failed",
                    extra={"agent_id": agent_id, "error": str(exc)},
                )

        return killed

    def get_hierarchy(self, root_id: str | None = None) -> dict[str, Any]:
        """Get the agent hierarchy as a nested dictionary.

        Args:
            root_id: If specified, return the subtree rooted at this agent.
                    If None, return all root agents.

        Returns:
            Dictionary representing the hierarchy tree.
        """
        if not hasattr(self._ks, "_agents"):
            return {}

        agents = dict(self._ks._agents)

        def build_tree(agent_id: str) -> dict[str, Any]:
            children = [aid for aid, reg in agents.items() if reg.parent_id == agent_id]
            return {
                "agent_id": agent_id,
                "children": [build_tree(child) for child in children],
            }

        if root_id is not None:
            if root_id in agents:
                return build_tree(root_id)
            return {}

        # Find all roots (no parent)
        roots = [aid for aid, reg in agents.items() if reg.parent_id is None]
        return {
            "roots": [build_tree(root) for root in roots],
            "total_agents": len(agents),
        }
