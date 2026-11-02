"""``MeteredLLM``: any ``LLM`` behind ``Limits`` reserve and settle (R214), for the callers that are not the agent
loop (``extract()``, the evals gate, scripts). The worst case of each call is booked before it starts and replaced by
the real cost after; a refused booking raises ``OverBudget`` and the model is never called. A call that raised a provider
error is settled with ``cost_to_settle`` (the billing contract on ``ProviderError``): released when nothing was sent
or every request was refused (4xx, 429); booked at its cost when the provider answered and billed (never at zero); the
worst case stays booked when a request may have been processed (timeout, reset, 5xx, ``DeadlineExceeded``). If the
store cannot take the settlement of a good reply, the worst case stays booked (it fails safe), the failure is logged
and the reply is still returned.

Scope: this wraps the calls it is given. The agent loop reserves every call; ``extract()`` and ``evals.gate`` meter only
when a ``MeteredLLM`` / ``limits=`` is passed; the K1b replay has its own sequential USD cap."""

from __future__ import annotations

import logging
from typing import Any

from hadavin_sdk.limits import Limits, prompt_bytes, worst_case_usd
from hadavin_sdk.llm.protocol import LLM, ProviderError, cost_to_settle
from hadavin_sdk.models import Reply

_LOG = logging.getLogger("hadavin_sdk.llm.metered")


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
        except ProviderError as exc:
            # The billing contract (llm/protocol.py): release only if nothing was sent or every request was
            # refused; book a billed answer at its cost; keep the worst case when the outcome is unknown.
            self._settle(res, cost_to_settle(exc, res.usd))
            raise
        self._settle(res, reply.cost_usd)
        return reply

    def _settle(self, res: Any, actual: Any) -> None:
        try:
            self.limits.settle(res, actual)
        except Exception as exc:  # noqa: BLE001 - the worst case stays booked; a good reply is not thrown away
            _LOG.warning("settle failed, worst case stays booked: %s", type(exc).__name__)
