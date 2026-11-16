"""OpenAI Agents SDK integration for agent-killswitch.

Provides a guardrail function and input guard compatible with the
OpenAI Agents SDK.

Requires: pip install agent-killswitch[openai]
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class KillSwitchGuardrail:
    """OpenAI Agents SDK guardrail that enforces kill switch checks.

    Can be used as an input guardrail or output guardrail in the
    OpenAI Agents SDK.

    Example::

        from agent_killswitch import KillSwitch
        from agent_killswitch.integrations.openai_agents import KillSwitchGuardrail

        ks = KillSwitch()
        guardrail = KillSwitchGuardrail(killswitch=ks, agent_id="openai-agent")

        # Use as input guardrail
        result = guardrail.check_input("user message")
        if not result["allowed"]:
            print(f"Blocked: {result['reason']}")

    Args:
        killswitch: The KillSwitch instance.
        agent_id: Agent ID for scope checks.
        crew_id: Optional crew ID for crew scope checks.
    """

    def __init__(
        self,
        killswitch: Any,
        agent_id: str | None = None,
        crew_id: str | None = None,
    ) -> None:
        self._ks = killswitch
        self._agent_id = agent_id
        self._crew_id = crew_id

    def check_input(self, user_input: Any) -> dict[str, Any]:
        """Check kill switch before processing input.

        Args:
            user_input: The user input being processed.

        Returns:
            Dictionary with keys:
            - 'allowed': bool
            - 'reason': str (if blocked)
            - 'level': str (if blocked)
        """
        status = self._ks.check(
            scope_target=self._agent_id,
            crew_id=self._crew_id,
        )

        if status.is_killed:
            level_str = status.level.value if status.level else "unknown"
            return {
                "allowed": False,
                "reason": status.reason or "Kill switch is active",
                "level": level_str,
            }

        return {"allowed": True, "reason": "", "level": ""}

    def check_output(self, output: Any) -> dict[str, Any]:
        """Check kill switch before returning output.

        Args:
            output: The agent output being validated.

        Returns:
            Dictionary with keys:
            - 'allowed': bool
            - 'reason': str (if blocked)
            - 'level': str (if blocked)
        """
        return self.check_input(output)

    def as_guardrail_function(self) -> Any:
        """Return a guardrail function compatible with the OpenAI SDK.

        Returns:
            An async function suitable for use as a guardrail.
        """

        async def guardrail_fn(
            context: Any,
            agent: Any,
            input_data: Any,
        ) -> Any | None:
            """Guardrail function that checks the kill switch.

            Args:
                context: The run context.
                agent: The agent being guarded.
                input_data: The input being processed.

            Returns:
                None if allowed, or a GuardrailFunctionOutput if blocked.
            """
            status = self._ks.check(
                scope_target=self._agent_id,
                crew_id=self._crew_id,
            )

            if status.is_killed:
                level_str = status.level.value if status.level else "unknown"
                reason = status.reason or "Kill switch is active"
                logger.warning(
                    "openai_agents_guardrail_blocked",
                    extra={
                        "agent_id": self._agent_id,
                        "level": level_str,
                        "reason": reason,
                    },
                )

                # Try to use the SDK's GuardrailFunctionOutput if available
                try:
                    from openai.agents import GuardrailFunctionOutput, GuardrailTripwireTriggered

                    output = GuardrailFunctionOutput(
                        output_info={"blocked": True, "reason": reason, "level": level_str},
                        tripwire_triggered=True,
                    )
                    raise GuardrailTripwireTriggered(output)
                except ImportError:
                    # The openai.agents extra is not installed. That is an expected,
                    # supported configuration - chaining the ImportError here would
                    # imply something went wrong, so suppress the context.
                    raise RuntimeError(
                        f"Kill switch active: level={level_str}, reason={reason}"
                    ) from None

            return None

        return guardrail_fn
