"""CrewAI integration for agent-killswitch.

Provides a pre-action hook that checks the kill switch before
each CrewAI agent action.

Requires: pip install agent-killswitch[crewai]
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class KillSwitchHook:
    """CrewAI pre-action hook that checks the kill switch.

    This hook is designed to be called before each agent action in
    a CrewAI workflow. If the kill switch is active, it prevents
    the action from executing.

    Example::

        from agent_killswitch import KillSwitch
        from agent_killswitch.integrations.crewai import KillSwitchHook

        ks = KillSwitch()
        hook = KillSwitchHook(killswitch=ks, crew_id="my-crew")

        # In your CrewAI setup:
        # Use hook.before_action as a step callback
        if hook.before_action(agent_id="researcher"):
            # Action is allowed
            pass

    Args:
        killswitch: The KillSwitch instance.
        crew_id: The crew ID for scope checks.
        on_blocked: Callback when an action is blocked by kill switch.
            Signature: (agent_id: str, level: str, reason: str) -> None
    """

    def __init__(
        self,
        killswitch: Any,
        crew_id: str | None = None,
        on_blocked: Callable[[str, str, str], None] | None = None,
    ) -> None:
        self._ks = killswitch
        self._crew_id = crew_id
        self._on_blocked = on_blocked

    def before_action(self, agent_id: str | None = None) -> bool:
        """Check if the agent action should proceed.

        Args:
            agent_id: The agent attempting the action.

        Returns:
            True if the action should proceed, False if blocked.
        """
        status = self._ks.check(
            scope_target=agent_id,
            crew_id=self._crew_id,
        )

        if status.is_killed:
            level_str = status.level.value if status.level else "unknown"
            reason = status.reason or ""

            logger.warning(
                "crewai_action_blocked",
                extra={
                    "agent_id": agent_id,
                    "crew_id": self._crew_id,
                    "level": level_str,
                    "reason": reason,
                },
            )

            if self._on_blocked is not None:
                try:
                    self._on_blocked(agent_id or "", level_str, reason)
                except Exception as exc:
                    logger.error(
                        "on_blocked callback error",
                        extra={"error": str(exc)},
                    )

            return False

        return True

    def create_step_callback(
        self,
        agent_id: str | None = None,
    ) -> Callable[[Any], Any]:
        """Create a CrewAI step callback function.

        Returns a callable suitable for use as a CrewAI step_callback.
        The callback checks the kill switch and raises RuntimeError
        if the switch is active.

        Args:
            agent_id: The agent ID.

        Returns:
            Callback function.
        """

        def callback(step_output: Any) -> Any:
            if not self.before_action(agent_id=agent_id):
                raise RuntimeError(f"Kill switch active for agent={agent_id}, crew={self._crew_id}")
            return step_output

        return callback

    def wrap_crew(
        self,
        crew: Any,
        agent_id_field: str = "role",
    ) -> Any:
        """Wrap a CrewAI crew with kill switch protection.

        This method patches the crew to check the kill switch before
        each agent action. Returns the modified crew.

        Args:
            crew: The CrewAI Crew instance.
            agent_id_field: Agent attribute to use as agent_id.

        Returns:
            The crew with kill switch protection applied.
        """
        if hasattr(crew, "step_callback"):
            original = crew.step_callback

            def wrapped_callback(step_output: Any) -> Any:
                # Check kill switch
                if not self.before_action(agent_id=self._crew_id):
                    raise RuntimeError(f"Kill switch active for crew={self._crew_id}")
                if original is not None:
                    return original(step_output)
                return step_output

            crew.step_callback = wrapped_callback

        return crew
