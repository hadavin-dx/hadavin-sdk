"""The replay agent loop: one incident, one model, six read-only data tools and ``submit_diagnosis``.

Own loop (not ``Runtime.handle``): it calls the model through a model gate client bound to the case, as
``evals.gate`` does (every call is reserved on the invocation's USD cap and settled). It does not run the
production approval and limits path, so a replay pass is not proof of live behaviour. The case ends when a reply
holds a ``submit_diagnosis`` call, or when a reply has no tool call (its text is then parsed as the diagnosis).
The bundle given here is already masked (``k1b.redaction``) unless the operator acknowledged otherwise.
Messages are plain ``{"role", "content": str}`` pairs: a tool call is the assistant text ``tool <name> <input
json>`` and its result the user text ``tool result <name>: <json>``.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from hadavin_sdk.guard.injection import Detector, injection_check
from hadavin_sdk.guard.injection import bind as bind_detector
from hadavin_sdk.guard.model_gate import NO_MAP, GateRefused, ModelGate
from hadavin_sdk.guard.runmap import safe_head
from hadavin_sdk.k1b.bundle import Bundle
from hadavin_sdk.k1b.diagnosis import Diagnosis, parse_diagnosis, parse_diagnosis_text
from hadavin_sdk.k1b.tools import ALLOWED_TOOLS, NO_DATA, SUBMIT, TOOL_SPECS, Snapshot, render
from hadavin_sdk.limits import Budget, SpendRefused
from hadavin_sdk.llm.protocol import LLM, ProviderError, ProviderExhausted
from hadavin_sdk.models import Reply

SYSTEM_PROMPT = (
    "You are diagnosing one past incident from a frozen snapshot. Use only what the tools return; cite evidence "
    "ids exactly as the tools return them. If the evidence does not support a cause, say you are not sure "
    "instead of guessing. When done, call submit_diagnosis once: either causes (service, fault_type, "
    "evidence_ids, best first) or not_sure true (with a short reason; causes may be left out)."
)
RAW_LIMIT = 2000


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
    via: str | None = (
        None  # how the answer arrived: "tool" (submit_diagnosis) or "text" (reply text)
    )
    halt: str | None = (
        None  # "capped" (USD cap reached) or "aborted" (non-transient provider error): stop the run
    )


def _dumps(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


class CallTimeout(Exception):
    """The provider call did not return before the case deadline."""


MIN_WAIT_S = 1.0  # floor on the wait for one call, so a case at its deadline still gives a fast call a moment


def _chat_bounded(llm: LLM, wait_s: float, /, *args: object, **kwargs: object) -> Reply:
    """``llm.chat`` with a wall-clock bound that holds for every llm kind (a socket timeout is per socket
    operation and cannot stop a slow trickle). The call runs in a daemon thread; on expiry the thread is
    abandoned (its late reply is dropped and its cost is unknown: the hold stays at the worst case), so the run never hangs. Raises
    ``CallTimeout``; any exception from the call is re-raised here."""
    box: dict[str, object] = {}
    abandoned = threading.Event()

    def work() -> None:
        try:
            box["reply"] = llm.chat(*args, **kwargs)  # type: ignore[arg-type]
        except BaseException as exc:  # noqa: BLE001 - handed to the caller thread below
            box["exc"] = exc
            if (
                abandoned.is_set()
            ):  # nobody will read it: leave the class name (never the message) in the log
                logging.getLogger(__name__).warning(
                    "abandoned llm call ended with %s", type(exc).__name__
                )

    t = threading.Thread(target=work, daemon=True, name="k1b-llm-call")
    t.start()
    t.join(max(wait_s, MIN_WAIT_S))
    if t.is_alive():
        abandoned.set()
        raise CallTimeout
    if "exc" in box:
        raise box["exc"]  # type: ignore[misc]
    return box["reply"]  # type: ignore[return-value]


def run_case(
    gate: ModelGate,
    *,
    wrap: Callable[[Any], ModelGate],
    agent_id: str,
    run_id: str,
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
    """Never raises for a model, provider, meter or gate problem: every end is a status on the outcome. ``halt``
    is set when the whole run must stop (USD cap, non-transient provider error, a refusal that is not the cap);
    the outcome keeps what the case gathered.

    `gate` is the UNBOUND model gate of the replay (its meter is `budget`); `wrap` makes such a gate for another
    client (a model-backed detector's own). The case gets its own payer run id,
    `run_id` plus the case id: the model client and a model-backed detector are bound to it here, and when the
    case ends ``budget.forfeit`` closes that id, so a call still open (its cost is unknown: a timeout, used-up
    retries, a provider error) stays booked at its worst case and a thread the case abandoned books nothing more."""
    out = CaseOutcome(status="ok")
    case_run_id = f"{run_id}:{bundle.case_id}"
    try:
        llm = gate.bind(agent_id, case_run_id, mapping=NO_MAP)
        bound = bind_detector(detector, wrap, agent_id, case_run_id, NO_MAP)
        _steps(
            out,
            llm,
            system=system,
            route=route,
            bundle=bundle,
            detector=bound,
            budget=budget,
            max_steps=max_steps,
            max_tool_calls=max_tool_calls,
            timeout_s=timeout_s,
            clock=clock,
        )
    except SpendRefused as exc:  # no call was made
        if exc.reason == "usd_cap":
            out.status, out.stop_reason, out.halt = "capped", "usd_cap", "capped"
        else:
            out.status, out.stop_reason, out.halt = "error", exc.reason, "aborted"
    except GateRefused as exc:  # no call was made
        out.status, out.stop_reason, out.halt = "error", exc.code, "aborted"
    finally:
        budget.forfeit(case_run_id)
    return out


def _steps(
    out: CaseOutcome,
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
    clock: Callable[[], float],
) -> None:
    """The steps of one case; every end is written on `out`. A meter or gate refusal is raised to `run_case`."""
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
            return
        if budget.exhausted:
            out.status, out.stop_reason, out.halt = "capped", "usd_cap", "capped"
            return
        try:
            reply = _chat_bounded(
                llm,
                timeout_s - (clock() - started),
                messages,
                system=system,
                route=route,
                tools=TOOL_SPECS,
            )
        except CallTimeout:
            # The abandoned call may still be running and billed (a retry layer can re-send): its hold stays
            # booked at the worst case (`budget.forfeit` in run_case) and the run stops, so the cap still holds.
            out.status, out.stop_reason, out.halt = "timeout", "call_timeout", "aborted"
            return
        except ProviderExhausted:
            out.status, out.stop_reason = "error", "provider_exhausted"
            return
        except ProviderError:
            out.status, out.stop_reason, out.halt = "error", "aborted", "aborted"
            return
        if reply.stop_reason in ("max_tokens", "refusal"):
            out.status, out.stop_reason = "error", reply.stop_reason
            return
        if not reply.tool_calls:
            out.via = "text"
            out.diagnosis = parse_diagnosis_text(reply.text)
            if out.diagnosis is None:
                out.raw = safe_head(reply.text, RAW_LIMIT)
            return
        for call in reply.tool_calls:
            if call.name == SUBMIT:
                out.via = "tool"
                out.diagnosis = parse_diagnosis(call.input)
                if out.diagnosis is None:
                    out.raw = safe_head(_dumps(call.input), RAW_LIMIT)
                return
            if out.tool_calls >= max_tool_calls:
                out.status, out.stop_reason = "capped", "max_tool_calls"
                return
            out.tool_calls += 1
            if call.name not in ALLOWED_TOOLS:
                out.hard_check_a.append(call.name)
                shown, ids = _dumps({"result": "unknown tool"}), set()
            else:
                shown, ids = render(snap.call(call.name, call.input))
                verdict = injection_check(detector, shown, "k1b-tool-result")
                if verdict.flagged:
                    out.injection_flagged += 1
                    shown, ids = _dumps(NO_DATA), set()
            out.returned_ids |= ids
            messages.append(
                {"role": "assistant", "content": f"tool {call.name} {_dumps(call.input)}"}
            )
            messages.append({"role": "user", "content": f"tool result {call.name}: {shown}"})
    out.status, out.stop_reason = "capped", "max_steps"
