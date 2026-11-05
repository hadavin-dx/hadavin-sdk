"""Integration tests for LangChain callback handler."""

from __future__ import annotations

from uuid import uuid4

import pytest

from agent_killswitch import KillLevel, KillScope, KillSwitch
from agent_killswitch.integrations.langchain import KillSwitchCallbackHandler


class TestKillSwitchCallbackHandler:
    """Tests for the LangChain callback handler."""

    @pytest.fixture
    def handler(self) -> tuple[KillSwitch, KillSwitchCallbackHandler]:
        ks = KillSwitch()
        handler = KillSwitchCallbackHandler(
            killswitch=ks,
            agent_id="test-agent",
        )
        return ks, handler

    def test_llm_start_passes_when_safe(
        self, handler: tuple[KillSwitch, KillSwitchCallbackHandler]
    ) -> None:
        _ks, h = handler
        # Should not raise
        h.on_llm_start(
            serialized={},
            prompts=["test"],
            run_id=uuid4(),
        )

    def test_llm_start_raises_when_killed(
        self, handler: tuple[KillSwitch, KillSwitchCallbackHandler]
    ) -> None:
        ks, h = handler
        ks.activate(KillLevel.KILL, KillScope.AGENT, scope_target="test-agent")

        with pytest.raises(RuntimeError, match="Kill switch active"):
            h.on_llm_start(
                serialized={},
                prompts=["test"],
                run_id=uuid4(),
            )

    def test_tool_start_checks_kill_switch(
        self, handler: tuple[KillSwitch, KillSwitchCallbackHandler]
    ) -> None:
        ks, h = handler
        ks.activate(KillLevel.STOP, KillScope.GLOBAL)

        with pytest.raises(RuntimeError):
            h.on_tool_start(
                serialized={},
                input_str="test",
                run_id=uuid4(),
            )

    def test_chain_start_checks_kill_switch(
        self, handler: tuple[KillSwitch, KillSwitchCallbackHandler]
    ) -> None:
        ks, h = handler
        ks.activate(KillLevel.PAUSE, KillScope.GLOBAL)

        with pytest.raises(RuntimeError):
            h.on_chain_start(
                serialized={},
                inputs={},
                run_id=uuid4(),
            )

    def test_no_raise_mode(self) -> None:
        ks = KillSwitch()
        ks.activate(KillLevel.KILL, KillScope.GLOBAL)
        h = KillSwitchCallbackHandler(
            killswitch=ks,
            agent_id="a1",
            raise_on_kill=False,
        )
        # Should not raise
        h.on_llm_start(serialized={}, prompts=["test"], run_id=uuid4())

    def test_crew_id_check(self) -> None:
        ks = KillSwitch()
        h = KillSwitchCallbackHandler(
            killswitch=ks,
            agent_id="a1",
            crew_id="crew-1",
        )
        ks.activate(KillLevel.STOP, KillScope.CREW, scope_target="crew-1")

        with pytest.raises(RuntimeError):
            h.on_llm_start(serialized={}, prompts=["test"], run_id=uuid4())
