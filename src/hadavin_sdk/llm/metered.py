"""``MeteredLLM``: any ``LLM`` behind ``Limits`` reserve and settle (R214), for the callers that are not the agent
loop (``extract()``, the evals gate, scripts). The worst case of each call is booked before it starts and replaced by
the real cost after; a refused booking raises ``OverBudget`` and the model is never called. A call that raised a
provider error is released (never billed), except ``DeadlineExceeded``, whose abandoned request may still be billed:
its worst case stays booked."""

from __future__ import annotations

from typing import Any

from hadavin_sdk.limits import Limits, prompt_bytes, worst_case_usd
from hadavin_sdk.llm.protocol import LLM, DeadlineExceeded, ProviderError
from hadavin_sdk.models import Reply


class MeteredLLM:
    def __init__(
        self,
        inner: LLM,
        limits: Limits,
        agent_id: str,
        routes: dict[str, Any],
        run_id: str | None = None,
    ) -> None:
        self.inner, self.limits, self.agent_id, self.routes, self.run_id = (
            inner,
            limits,
            agent_id,
            routes,
            run_id,
        )

    def __getattr__(self, name: str) -> Any:
        inner = self.__dict__.get("inner")
        if inner is None or name.startswith("__"):
            raise AttributeError(name)
        return getattr(inner, name)

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str,
        route: str,
        tools: list[dict[str, Any]] | None = None,
        documents: list[bytes] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> Reply:
        worst = worst_case_usd(
            self.routes[route], prompt_bytes(messages, system, documents, tools, output_schema)
        )
        res = self.limits.reserve(
            self.agent_id, worst, self.run_id
        )  # OverBudget: the model is not called
        try:
            reply = self.inner.chat(
                messages,
                system=system,
                route=route,
                tools=tools,
                documents=documents,
                output_schema=output_schema,
            )
        except DeadlineExceeded:
            self.limits.settle(res, res.usd)  # cost unknown: keep the worst case booked
            raise
        except ProviderError:
            self.limits.release(res)
            raise
        self.limits.settle(res, reply.cost_usd)
        return reply
