"""LangGraph integration for agent-killswitch.

Provides a killswitch check node and conditional edge for use
in LangGraph state graphs.

Requires: pip install agent-killswitch[langgraph]
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class KillSwitchNode:
    """A LangGraph node that checks the kill switch.

    Use this as a node in a LangGraph StateGraph. If the kill switch
    is active, it sets a flag in the state that can be used with
    conditional edges to route to a termination node.

    Example::

        from langgraph.graph import StateGraph
        from agent_killswitch import KillSwitch
        from agent_killswitch.integrations.langgraph import KillSwitchNode

        ks = KillSwitch()
        ks_node = KillSwitchNode(killswitch=ks, agent_id="graph-agent")

        graph = StateGraph(dict)
        graph.add_node("check_kill", ks_node)
        graph.add_node("agent_work", agent_node)
        graph.add_node("terminated", termination_node)
        graph.add_conditional_edges(
            "check_kill",
            ks_node.should_continue,
            {"continue": "agent_work", "killed": "terminated"},
        )

    Args:
        killswitch: The KillSwitch instance.
        agent_id: Agent ID for scope checks.
        crew_id: Optional crew ID for crew scope checks.
        kill_state_key: Key in state dict to set when killed.
            Default "kill_switch_active".
        kill_level_key: Key in state dict to set with kill level.
            Default "kill_level".
        kill_reason_key: Key in state dict to set with kill reason.
            Default "kill_reason".
    """

    def __init__(
        self,
        killswitch: Any,
        agent_id: str | None = None,
        crew_id: str | None = None,
        kill_state_key: str = "kill_switch_active",
        kill_level_key: str = "kill_level",
        kill_reason_key: str = "kill_reason",
    ) -> None:
        self._ks = killswitch
        self._agent_id = agent_id
        self._crew_id = crew_id
        self._kill_state_key = kill_state_key
        self._kill_level_key = kill_level_key
        self._kill_reason_key = kill_reason_key

    def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        """Check the kill switch and update state.

        Args:
            state: The current LangGraph state.

        Returns:
            Updated state with kill switch status.
        """
        status = self._ks.check(
            scope_target=self._agent_id,
            crew_id=self._crew_id,
        )

        result = dict(state)
        result[self._kill_state_key] = status.is_killed
        if status.is_killed:
            result[self._kill_level_key] = status.level.value if status.level else None
            result[self._kill_reason_key] = status.reason or ""
            logger.warning(
                "langgraph_kill_switch_active",
                extra={
                    "agent_id": self._agent_id,
                    "level": result[self._kill_level_key],
                },
            )
        else:
            result[self._kill_level_key] = None
            result[self._kill_reason_key] = ""

        return result

    def should_continue(self, state: dict[str, Any]) -> str:
        """Conditional edge function: 'continue' or 'killed'.

        Use with graph.add_conditional_edges() to route based on
        kill switch status.

        Args:
            state: The current LangGraph state.

        Returns:
            'killed' if kill switch is active, 'continue' otherwise.
        """
        if state.get(self._kill_state_key, False):
            return "killed"
        return "continue"


def create_killswitch_node(
    killswitch: Any,
    agent_id: str | None = None,
    crew_id: str | None = None,
) -> tuple[Any, Any]:
    """Convenience function to create a kill switch node and condition.

    Returns a tuple of (node_function, condition_function) ready to
    add to a LangGraph StateGraph.

    Args:
        killswitch: The KillSwitch instance.
        agent_id: Agent ID for scope checks.
        crew_id: Optional crew ID.

    Returns:
        Tuple of (node_callable, condition_callable).
    """
    node = KillSwitchNode(
        killswitch=killswitch,
        agent_id=agent_id,
        crew_id=crew_id,
    )
    return node, node.should_continue
