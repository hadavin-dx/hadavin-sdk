"""Framework integrations for agent-killswitch.

Each integration is a thin adapter that connects the core kill switch
to a specific AI agent framework. Integrations are lazy-loaded to
avoid requiring the framework as a dependency.

Available integrations:
- langchain: LangChain callback handler
- langgraph: LangGraph node and conditional edge
- crewai: CrewAI pre-action hook
- openai_agents: OpenAI Agents SDK guardrail
- asyncio_tasks: Generic asyncio.Task cancellation
"""

from __future__ import annotations

__all__: list[str] = []
