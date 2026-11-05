"""Integration tests for the LangGraph, CrewAI and OpenAI Agents adapters.

These three adapters import their framework lazily, inside the methods that need it, so the
modules are importable — and testable — with none of the optional extras installed. Until
these tests existed they sat at 0% coverage purely because nothing imported them, which is
the least useful reason for code to be untested: it was never that the code was hard to
reach, only that no one reached for it.

Each test asserts the behaviour that actually matters for a safety control: that a live kill
switch is observed, that scope is respected, and that the adapter reports it in whatever
shape its host framework expects.
"""

from __future__ import annotations

import pytest

from agent_killswitch import KillLevel, KillScope, KillSwitch
from agent_killswitch.integrations.crewai import KillSwitchHook
from agent_killswitch.integrations.langgraph import KillSwitchNode
from agent_killswitch.integrations.openai_agents import KillSwitchGuardrail


@pytest.fixture
def ks() -> KillSwitch:
    return KillSwitch()


# --------------------------------------------------------------------- LangGraph


class TestKillSwitchNode:
    """The LangGraph node writes kill state into the graph state dict."""

    def test_passes_state_through_untouched_when_not_killed(self, ks: KillSwitch) -> None:
        node = KillSwitchNode(killswitch=ks, agent_id="graph-agent")

        result = node({"messages": ["hello"], "step": 3})

        assert result["kill_switch_active"] is False
        # the caller's own state must survive the node
        assert result["messages"] == ["hello"]
        assert result["step"] == 3

    def test_marks_state_killed_with_level_and_reason(self, ks: KillSwitch) -> None:
        node = KillSwitchNode(killswitch=ks, agent_id="graph-agent")
        ks.activate(
            KillLevel.KILL,
            KillScope.AGENT,
            scope_target="graph-agent",
            reason="runaway loop",
        )

        result = node({})

        assert result["kill_switch_active"] is True
        assert result["kill_level"] == KillLevel.KILL.value
        assert result["kill_reason"] == "runaway loop"

    def test_does_not_mutate_the_state_it_was_given(self, ks: KillSwitch) -> None:
        """LangGraph merges returned state; mutating the input in place is a bug."""
        node = KillSwitchNode(killswitch=ks, agent_id="graph-agent")
        original = {"step": 1}

        node(original)

        assert original == {"step": 1}

    def test_should_continue_routes_on_the_flag(self, ks: KillSwitch) -> None:
        node = KillSwitchNode(killswitch=ks, agent_id="graph-agent")

        assert node.should_continue({"kill_switch_active": False}) == "continue"
        assert node.should_continue({"kill_switch_active": True}) == "killed"
        # absent key must fail open to "continue", not raise
        assert node.should_continue({}) == "continue"

    def test_another_agents_kill_does_not_stop_this_node(self, ks: KillSwitch) -> None:
        node = KillSwitchNode(killswitch=ks, agent_id="graph-agent")
        ks.activate(KillLevel.KILL, KillScope.AGENT, scope_target="somebody-else")

        assert node({})["kill_switch_active"] is False


# --------------------------------------------------------------------- CrewAI


class TestKillSwitchHook:
    """The CrewAI hook answers a single question: may this action proceed?"""

    def test_allows_the_action_when_not_killed(self, ks: KillSwitch) -> None:
        hook = KillSwitchHook(killswitch=ks)

        assert hook.before_action("researcher") is True

    def test_blocks_the_action_when_killed(self, ks: KillSwitch) -> None:
        hook = KillSwitchHook(killswitch=ks)
        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="stop everything")

        assert hook.before_action("researcher") is False

    def test_calls_the_on_blocked_callback_with_the_detail(self, ks: KillSwitch) -> None:
        seen: list[tuple[str, str, str]] = []
        hook = KillSwitchHook(
            killswitch=ks,
            on_blocked=lambda agent, level, reason: seen.append((agent, level, reason)),
        )
        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="budget blown")

        hook.before_action("writer")

        assert seen == [("writer", KillLevel.KILL.value, "budget blown")]

    def test_a_raising_callback_cannot_break_the_block(self, ks: KillSwitch) -> None:
        """A broken callback must not turn a blocked action into an allowed one."""

        def boom(agent: str, level: str, reason: str) -> None:
            raise RuntimeError("callback is broken")

        hook = KillSwitchHook(killswitch=ks, on_blocked=boom)
        ks.activate(KillLevel.KILL, KillScope.GLOBAL)

        assert hook.before_action("writer") is False

    def test_crew_scope_is_respected(self, ks: KillSwitch) -> None:
        hook = KillSwitchHook(killswitch=ks, crew_id="crew-a")
        ks.activate(KillLevel.KILL, KillScope.CREW, scope_target="crew-a")

        assert hook.before_action("any-agent") is False


# --------------------------------------------------------------------- OpenAI Agents


class TestKillSwitchGuardrail:
    """The OpenAI Agents guardrail returns a verdict dict rather than raising."""

    def test_input_allowed_when_not_killed(self, ks: KillSwitch) -> None:
        guard = KillSwitchGuardrail(killswitch=ks, agent_id="assistant")

        verdict = guard.check_input("what is the weather?")

        assert verdict == {"allowed": True, "reason": "", "level": ""}

    def test_input_blocked_with_reason_and_level(self, ks: KillSwitch) -> None:
        guard = KillSwitchGuardrail(killswitch=ks, agent_id="assistant")
        ks.activate(
            KillLevel.PAUSE,
            KillScope.AGENT,
            scope_target="assistant",
            reason="rate limited",
        )

        verdict = guard.check_input("anything")

        assert verdict["allowed"] is False
        assert verdict["level"] == KillLevel.PAUSE.value
        assert verdict["reason"] == "rate limited"

    def test_output_is_checked_on_the_same_terms_as_input(self, ks: KillSwitch) -> None:
        """A kill that lands mid-run must still stop the answer going out."""
        guard = KillSwitchGuardrail(killswitch=ks, agent_id="assistant")
        assert guard.check_output("a drafted answer")["allowed"] is True

        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="emergency")

        assert guard.check_output("a drafted answer")["allowed"] is False

    def test_blocked_verdict_always_carries_a_reason(self, ks: KillSwitch) -> None:
        """Even when the operator gave no reason, the verdict must explain itself."""
        guard = KillSwitchGuardrail(killswitch=ks, agent_id="assistant")
        ks.activate(KillLevel.KILL, KillScope.GLOBAL)

        verdict = guard.check_input("x")

        assert verdict["allowed"] is False
        assert verdict["reason"], "a blocked verdict with an empty reason is unusable"
