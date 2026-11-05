"""LangChain integration for agent-killswitch.

Provides a callback handler that checks the kill switch before and
after each LLM call, tool invocation, and chain execution.

Requires: pip install agent-killswitch[langchain]
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)

try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:
    # Create a stub so the class can be defined without the dependency
    class BaseCallbackHandler:  # type: ignore[no-redef]
        """Stub for when langchain-core is not installed."""

        pass


class KillSwitchCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler that enforces kill switch checks.

    Checks the kill switch before each LLM call and tool invocation.
    If the kill switch is active, raises an exception to halt the chain.

    Example::

        from langchain_openai import ChatOpenAI
        from agent_killswitch import KillSwitch
        from agent_killswitch.integrations.langchain import KillSwitchCallbackHandler

        ks = KillSwitch()
        handler = KillSwitchCallbackHandler(killswitch=ks, agent_id="my-agent")

        llm = ChatOpenAI(callbacks=[handler])
        llm.invoke("Hello")  # Will check kill switch before calling

    Args:
        killswitch: The KillSwitch instance to check.
        agent_id: The agent ID for scope-specific checks.
        crew_id: Optional crew ID for crew scope checks.
        raise_on_kill: If True, raise RuntimeError on kill. Default True.
    """

    def __init__(
        self,
        killswitch: Any,
        agent_id: str | None = None,
        crew_id: str | None = None,
        raise_on_kill: bool = True,
    ) -> None:
        self._ks = killswitch
        self._agent_id = agent_id
        self._crew_id = crew_id
        self._raise_on_kill = raise_on_kill

    def _check(self, action: str) -> None:
        """Check the kill switch and raise if active.

        Args:
            action: Description of the action being checked.
        """
        status = self._ks.check(
            scope_target=self._agent_id,
            crew_id=self._crew_id,
        )
        if status.is_killed:
            msg = (
                f"Kill switch active during {action}: level={status.level}, reason={status.reason}"
            )
            logger.warning("langchain_kill_switch_triggered", extra={"action": action})
            if self._raise_on_kill:
                raise RuntimeError(msg)

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Check kill switch before LLM call."""
        self._check("llm_start")

    def on_llm_end(
        self,
        response: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Check kill switch after LLM call."""
        self._check("llm_end")

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Check kill switch before tool invocation."""
        self._check("tool_start")

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Check kill switch before chain execution."""
        self._check("chain_start")
