"""LangChain integration example for agent-killswitch.

Shows how to add kill switch protection to LangChain chains and agents.

Requires: pip install agent-killswitch[langchain] langchain-openai
"""

from __future__ import annotations

from agent_killswitch import KillLevel, KillScope, KillSwitch
from agent_killswitch.integrations.langchain import KillSwitchCallbackHandler


def main() -> None:
    # Create kill switch
    ks = KillSwitch()

    # Create callback handler
    handler = KillSwitchCallbackHandler(
        killswitch=ks,
        agent_id="langchain-agent",
        crew_id="research-crew",
    )

    print("Kill switch callback handler created.")
    print("Use it with LangChain:\n")
    print("  from langchain_openai import ChatOpenAI")
    print("  llm = ChatOpenAI(callbacks=[handler])")
    print("  llm.invoke('Hello')  # Kill switch checked before each call")
    print()

    # Demonstrate: activate kill switch
    ks.activate(
        KillLevel.STOP,
        KillScope.AGENT,
        scope_target="langchain-agent",
        reason="Cost limit reached",
    )

    # The handler would raise on the next LLM call
    try:
        # Simulate what happens internally
        from uuid import uuid4

        handler.on_llm_start(
            serialized={},
            prompts=["test prompt"],
            run_id=uuid4(),
        )
    except RuntimeError as e:
        print(f"LLM call blocked: {e}")

    # Deactivate and show it works again
    ks.deactivate(KillScope.AGENT, scope_target="langchain-agent")
    print("\nKill switch deactivated. LLM calls would proceed normally.")


if __name__ == "__main__":
    main()
