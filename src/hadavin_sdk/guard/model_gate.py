"""The model gate: one wrapper around the model client (step F).

Guarantee: values the run has identified as sensitive are replaced by their placeholders in everything sent to a model; detection of new values is done by the producers' pattern redactor.

Stated limits of that sentence (lead review round 1; each is pinned by the test named, T = tests/test_model_gate.py,
E = tests/test_runmap_enforce_map.py). The replace is the redactor's own sweep and follows its rule (`redact._sweep`):
- A known value under 3 characters is never replaced. A known value that is all digits and under 6 characters, or
  a common word (`redact._COMMON`: prod, test, web ...), is never replaced UNLESS it is a secret kind of 4
  characters or more (those are replaced in every copy).
  E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept
- Any value that is not a secret kind of 4 or more (an identifier: tenant, host, address, id) is replaced only
  where no ASCII letter or digit touches it: `abc123` inside `xabc1234` stays.
  E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept
- Only the spelling the map holds is replaced: a percent-, entity- or backslash-encoded copy, a full-width or
  other look-alike spelling and a copy split by a zero-width character pass as written.
  T::test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate
- Two known values that overlap in the text without one containing the other (`abcd` and `cdef` in `abcdef`):
  one is replaced and the tail of the other stays (`<A_1>ef`); two identifiers there are both left.
  E::test_stated_limit_partial_overlap_leaves_a_tail
- The gate runs no pattern: a value that is in no map passes as written, also a clean key and a clean value that
  only match a pattern once composed (`"user_id": "abc123"`).
  T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched
- With no map (`mapping=None`: the eval and replay command lines, the judge with its own map) there is no enforce
  step. `system` and `tools` are operator text and are not touched.

Before any provider contact the gate enforces the caller's run map on every message and document (a raw copy
of a value the map holds becomes that value's existing placeholder; `runmap.enforce_map`), then reserves the
worst-case cost. The client gets the enforced copies. After the call the gate settles the real cost and writes
one audit row. If the enforce step or the reservation fails, no call is made. The gate holds no money logic and
no redaction logic of its own: it only orders the steps.

No logger, no module-level state, and no message text, no exception text and no exception chain in any audit
row or in any exception raised here. The caller's messages, dicts and documents are never changed in place.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Mapping
from decimal import Decimal
from typing import Any, Protocol

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.guard import runmap
from hadavin_sdk.llm.protocol import LLM, ProviderError, ProviderExhausted
from hadavin_sdk.models import AuditEvent, Reply

# ======================================================================================================
# ASSUMED INTERFACE (ii): switch here when core-b publishes it
# `Meter` mirrors INTERFACE (ii) as the lead published it (ORDER 006; inputs/draft-ticket-F-store-with-
# INTERFACE-ii.md lines 113-135). It is a local structural Protocol: `limits.SpendRefused` does not exist
# yet and is NOT imported; its `.reason` is read with getattr. Nothing outside this block names a meter
# method, an audit string or the worst_case arguments.
# ------------------------------------------------------------------------------------------------------
# reserve: returns a reservation id only after the worst case is booked; ANY exception means no model call.
# settle: returns the overshoot; the first call for a reservation wins.
# THE ONE SETTLE RULE (ORDER 011; it replaces ORDER 006 item 8):
#   (a) a reply came back with a usable cost            -> settle that cost;
#   (b) the adapter MARKED the error as refused before any response (`refused_before_response`)
#                                                       -> settle 0;
#   (c) everything else (a timeout, used-up retries, a billed reply that failed to parse, any other
#       exception, KeyboardInterrupt / SystemExit, an abandoned thread, a reply whose cost is missing,
#       negative or not a number)                       -> NO settle: the worst case stays booked and the
#                                                          store's sweep closes the reservation.
# worst_case: supplied by the installer; it resolves the route name and covers the client's retries.


class Meter(Protocol):
    def reserve(self, agent_id: str, worst_usd: Decimal, *, run_id: str | None = None) -> str: ...

    def settle(self, reservation_id: str, actual_usd: Decimal) -> Decimal: ...


WorstCase = Callable[
    [
        str,  # route
        str,  # system
        list[dict[str, Any]],  # messages
        list[dict[str, Any]] | None,  # tools
        list[bytes] | None,  # documents
        dict[str, Any] | None,  # output_schema
    ],
    Decimal,
]
# (text, the run's map) -> the text with the map's values replaced; any raise means no call
Enforce = Callable[[str, Mapping[str, str]], str]

AUDIT_DOMAIN = "llm"
AUDIT_OPERATION = "chat"
DEFAULT_SOURCE = "gate"
RESULT_OK = "ok"
RESULT_REFUSED = "refused"
RESULT_FAILED = "failed"
CODE_GATE_REFUSED = "gate_refused"
CODE_MASK_REFUSED = "mask_refused"
CODE_RESERVE_REFUSED = "reserve_refused"  # the meter's exception has no published `.reason`
CODE_PROVIDER_REFUSED = "provider_refused"  # rule (b): marked refused before any response, settled at 0
CODE_PROVIDER_ERROR = "provider_error"  # rule (c): an unmarked ProviderError, NOT settled
CODE_PROVIDER_EXHAUSTED = "provider_exhausted"  # rule (c): retries used up, NOT settled
CODE_CALL_FAILED = "call_failed"  # rule (c): any other Exception from the client, NOT settled
CODE_CALL_INTERRUPTED = "call_interrupted"  # rule (c): KeyboardInterrupt, SystemExit, NOT settled
CODE_COST_UNKNOWN = "cost_unknown"  # rule (c): a reply with no usable cost; returned, NOT settled
CODE_SETTLE_FAILED = "settle_failed"  # the meter raised in settle: the worst case stays booked
# The reasons INTERFACE (ii) publishes for `SpendRefused.reason`. Only these become an audit error code: a
# `.reason` on any other exception (urllib's URLError has one) is never copied.
SPEND_REASONS = frozenset(
    {"kill_switch", "daily_budget", "monthly_budget", "limits_unavailable", "bad_amount"}
)


def refused_before_response(exc: BaseException) -> bool:
    """Rule (b). True only for a ProviderError (not ProviderExhausted: its attempts may have been answered)
    that the adapter marked with `refused_before_response = True`. llm/retry.py sets no such mark yet
    (handover/core-c/requests/2-refused-before-response.md), so today this is False for every real error
    and every failed call keeps its worst case booked."""
    marked = getattr(exc, "refused_before_response", False) is True
    return marked and isinstance(exc, ProviderError) and not isinstance(exc, ProviderExhausted)


def usable_cost(reply: Any) -> Decimal | None:
    """Rule (a): the reply's cost when it is a finite Decimal that is not negative, else None."""
    cost = getattr(reply, "cost_usd", None)
    if isinstance(cost, Decimal) and cost.is_finite() and cost >= 0:
        return cost
    return None


# END OF ASSUMED INTERFACE (ii)
# ======================================================================================================


class GateRefused(RuntimeError):
    """The gate made no model call. Carries a stable `code` and nothing else: never text, never a secret."""

    code = CODE_GATE_REFUSED

    def __init__(self) -> None:
        super().__init__(self.code)


class UnmaskedInput(GateRefused):
    """The run map could not be enforced on what the caller passed (a content that is not `str`, a text over
    the cap, a bad map, any failure of the enforce step). Never raised because a pattern matched."""

    code = CODE_MASK_REFUSED


class ModelGate:
    """Holds the client, the meter, the audit sink, the worst-case function and the enforce step. It has NO
    `chat`: a caller must `bind` it to an agent and a run first, so an unbound gate cannot call a model.
    A client that is already a gate is refused (TypeError): one call must never be reserved twice."""

    def __init__(
        self,
        llm: LLM,
        *,
        meter: Meter,
        audit: AuditSink | None,
        worst_case: WorstCase,
        enforce: Enforce = runmap.enforce_map,
    ) -> None:
        if isinstance(llm, ModelGate | BoundGate):
            raise TypeError("the client is already a model gate")
        self._llm, self._meter, self._audit = llm, meter, audit
        self._worst_case, self._enforce = worst_case, enforce

    def bind(
        self,
        agent_id: str,
        run_id: str,
        *,
        mapping: Mapping[str, str] | None = None,
        principal: str | None = None,
        source: str = DEFAULT_SOURCE,
    ) -> BoundGate:
        """A gate for one call site. `mapping` is the run's LIVE map, kept by reference (never copied, never
        written): a value the run masks later is replaced in earlier text on the next call. None (a site
        with no run map) means no enforce step. `principal` defaults to the agent id."""
        return BoundGate(self, agent_id, run_id, mapping, principal or agent_id, source)


class BoundGate:
    """Satisfies `llm.protocol.LLM`. Order: enforce the map, reserve, provider call, settle (by the one
    settle rule in the interface block above), audit row."""

    def __init__(
        self,
        gate: ModelGate,
        agent_id: str,
        run_id: str,
        mapping: Mapping[str, str] | None,
        principal: str,
        source: str,
    ) -> None:
        self._llm, self._meter, self._audit = gate._llm, gate._meter, gate._audit
        self._worst_case, self._enforce = gate._worst_case, gate._enforce
        self._agent_id, self._run_id, self._mapping = agent_id, run_id, mapping
        self._principal, self._source = principal, source

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
        enforced = self._enforced(messages, documents)
        if enforced is None:
            self._note(RESULT_REFUSED, CODE_MASK_REFUSED)
            raise UnmaskedInput  # raised outside any `except`: no cause and no context to leak
        messages, documents = enforced  # from here on only the enforced copies are used
        try:
            reserved = self._worst_case(route, system, messages, tools, documents, output_schema)
            reservation = self._meter.reserve(self._agent_id, reserved, run_id=self._run_id)
        except Exception as exc:
            reason = getattr(exc, "reason", None)
            published = isinstance(reason, str) and reason in SPEND_REASONS
            self._note(RESULT_REFUSED, reason if published else CODE_RESERVE_REFUSED)
            raise
        try:
            reply = self._llm.chat(
                messages,
                system=system,
                route=route,
                tools=tools,
                documents=documents,
                output_schema=output_schema,
            )
        except ProviderError as exc:
            if refused_before_response(exc):  # rule (b): it cost nothing
                self._settle(reservation, Decimal(0), RESULT_FAILED, CODE_PROVIDER_REFUSED)
            else:  # rule (c): the cost is unknown, the worst case stays booked
                exhausted = isinstance(exc, ProviderExhausted)
                code = CODE_PROVIDER_EXHAUSTED if exhausted else CODE_PROVIDER_ERROR
                self._note(RESULT_FAILED, code, reservation)
            raise
        except Exception:  # rule (c): may have been billed (a reply that fails to parse, a timeout)
            self._note(RESULT_FAILED, CODE_CALL_FAILED, reservation)
            raise
        except BaseException:  # rule (c): going down, cost unknown
            self._note(RESULT_FAILED, CODE_CALL_INTERRUPTED, reservation)
            raise
        cost = usable_cost(reply)
        if cost is None:  # rule (c): the call is paid and its reply is returned; nothing to settle with
            self._note(RESULT_OK, CODE_COST_UNKNOWN, reservation)
        else:  # rule (a)
            self._settle(reservation, cost, RESULT_OK, None)
        return reply

    def _settle(self, reservation: str, usd: Decimal, result: str, code: str | None) -> None:
        """Settle once and write the row. A raising meter never loses a paid reply and never hides the
        client's error: the row then says `settle_failed` (with the call's own result, so a paid call is
        still counted as `ok`) and the worst case stays booked."""
        try:
            self._meter.settle(reservation, usd)
        except Exception:  # noqa: BLE001 - see the docstring
            code = CODE_SETTLE_FAILED
        self._note(result, code, reservation)

    def _enforced(
        self, messages: list[dict[str, Any]], documents: list[bytes] | None
    ) -> tuple[list[dict[str, Any]], list[bytes] | None] | None:
        """New lists holding what will be sent, or None when the step failed (then nothing is sent). A message
        or document in which nothing is replaced is passed on as the same object, so the bytes are the
        caller's; one with a replaced value is a new dict or new bytes. A content that is not `str` is refused
        with or without a map. Documents are read as the adapters read them (`llm/common.py` `turns`: UTF-8,
        bad bytes replaced)."""
        mapping = self._mapping
        try:
            sent: list[dict[str, Any]] = []
            for message in messages:
                content = message["content"] if isinstance(message, dict) else None
                if not isinstance(content, str):
                    return None
                if mapping is not None:
                    fixed = self._enforce(content, mapping)
                    if not isinstance(fixed, str):
                        return None
                    if fixed != content:
                        message = {**message, "content": fixed}
                sent.append(message)
            if documents is None:
                return sent, None
            docs: list[bytes] = []
            for document in documents:
                if not isinstance(document, bytes):
                    return None
                if mapping is not None:
                    text = document.decode("utf-8", "replace")
                    fixed = self._enforce(text, mapping)
                    if not isinstance(fixed, str):
                        return None
                    if fixed != text:
                        document = fixed.encode("utf-8")
                docs.append(document)
        except Exception:  # noqa: BLE001 - fail closed: a step that cannot finish means no call
            return None
        return sent, docs

    def _note(self, result: str, error_code: str | None, reservation: str | None = None) -> None:
        """One audit row: codes only, and the reservation id (when one was made) as the object reference, so
        a row can be matched to the spend row. A missing, parking (None) or raising sink never changes the
        outcome."""
        if self._audit is None:
            return
        with contextlib.suppress(Exception):
            self._audit.write_outcome(
                AuditEvent(
                    run_id=self._run_id,
                    domain=AUDIT_DOMAIN,
                    operation=AUDIT_OPERATION,
                    principal=self._principal,
                    source=self._source,
                    object_ref=reservation if isinstance(reservation, str) else None,
                    result=result,
                    error_code=error_code,
                )
            )
