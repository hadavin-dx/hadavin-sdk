"""The replay agent loop: one incident, one model, six read-only data tools and ``submit_diagnosis``.

Own loop (not ``Runtime.handle``): it calls ``llm.chat`` directly, as ``evals.gate`` does. It does not run the
production approval and limits path, so a replay pass is not proof of live behaviour. The case ends when a reply
holds a ``submit_diagnosis`` call, or when a reply has no tool call (its text is then parsed as the diagnosis).
Messages are plain ``{"role", "content": str}`` pairs: a tool call is the assistant text ``tool <name> <input
json>`` and its result the user text ``tool result <name>: <json>``.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal

from hadavin_sdk.guard.injection import Detector, injection_check
from hadavin_sdk.k1b.bundle import Bundle
from hadavin_sdk.k1b.diagnosis import Diagnosis, parse_diagnosis, parse_diagnosis_text
from hadavin_sdk.k1b.tools import ALLOWED_TOOLS, NO_DATA, SUBMIT, TOOL_SPECS, Snapshot, render
from hadavin_sdk.llm.protocol import LLM, ProviderError, ProviderExhausted

SYSTEM_PROMPT = (
    "You are diagnosing one past incident from a frozen snapshot. Use only what the tools return; cite evidence "
    "ids exactly as the tools return them. If the evidence does not support a cause, say you are not sure "
    "instead of guessing. When done, call submit_diagnosis once: either causes (service, fault_type, "
    "evidence_ids, best first) or not_sure true with no causes."
)
RAW_LIMIT = 2000


class Budget:
    """A total USD cap for the whole invocation. One reply can overshoot it; the next call is refused."""

    def __init__(self, limit: Decimal) -> None:
        self.limit = limit
        self.spent = Decimal(0)

    def charge(self, usd: Decimal) -> None:
        self.spent += usd

    @property
    def exhausted(self) -> bool:
        return self.spent >= self.limit


@dataclass
class CaseOutcome:
    status: str  # ok | error | timeout | capped
    diagnosis: Diagnosis | None = None
    raw: str | None = None  # only for unreadable output, at most RAW_LIMIT characters
    stop_reason: str | None = None
    returned_ids: set[str] = field(default_factory=set)
    hard_check_a: list[str] = field(default_factory=list)
    injection_flagged: int = 0
    tool_calls: int = 0
    halt: str | None = (
        None  # "capped" (USD cap reached) or "aborted" (non-transient provider error): stop the run
    )


def _dumps(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def run_case(
    llm: LLM,
    *,
    system: str,
    route: str,
    bundle: Bundle,
    detector: Detector,
    budget: Budget,
    max_steps: int,
    max_tool_calls: int,
    timeout_s: int,
    clock: Callable[[], float] = time.monotonic,
) -> CaseOutcome:
    """Never raises for a model or provider problem: every end is a status on the outcome. ``halt`` is set when
    the whole run must stop (USD cap, non-transient provider error); the outcome keeps what the case gathered."""
    out = CaseOutcome(status="ok")
    snap = Snapshot(bundle)
    started = clock()
    messages: list[dict[str, str]] = [
        {
            "role": "user",
            "content": _dumps({"alert": bundle.alert, "alert_time": bundle.alert_time_text}),
        }
    ]
    for _ in range(max_steps):
        if clock() - started > timeout_s:
            out.status = "timeout"
            return out
        if budget.exhausted:
            out.status, out.stop_reason, out.halt = "capped", "usd_cap", "capped"
            return out
        try:
            reply = llm.chat(messages, system=system, route=route, tools=TOOL_SPECS)
        except ProviderExhausted:
            out.status, out.stop_reason = "error", "provider_exhausted"
            return out
        except ProviderError:
            out.status, out.stop_reason, out.halt = "error", "aborted", "aborted"
            return out
        budget.charge(reply.cost_usd)
        if reply.stop_reason in ("max_tokens", "refusal"):
            out.status, out.stop_reason = "error", reply.stop_reason
            return out
        if not reply.tool_calls:
            out.diagnosis = parse_diagnosis_text(reply.text)
            if out.diagnosis is None:
                out.raw = reply.text[:RAW_LIMIT]
            return out
        for call in reply.tool_calls:
            if call.name == SUBMIT:
                out.diagnosis = parse_diagnosis(call.input)
                if out.diagnosis is None:
                    out.raw = _dumps(call.input)[:RAW_LIMIT]
                return out
            if out.tool_calls >= max_tool_calls:
                out.status, out.stop_reason = "capped", "max_tool_calls"
                return out
            out.tool_calls += 1
            if call.name not in ALLOWED_TOOLS:
                out.hard_check_a.append(call.name)
                shown, ids = _dumps({"result": "unknown tool"}), set()
            else:
                shown, ids = render(snap.call(call.name, call.input))
                verdict = injection_check(detector, shown, "k1b-tool-result")
                budget.charge(verdict.cost_usd)
                if verdict.flagged:
                    out.injection_flagged += 1
                    shown, ids = _dumps(NO_DATA), set()
            out.returned_ids |= ids
            messages.append(
                {"role": "assistant", "content": f"tool {call.name} {_dumps(call.input)}"}
            )
            messages.append({"role": "user", "content": f"tool result {call.name}: {shown}"})
    out.status, out.stop_reason = "capped", "max_steps"
    return out
