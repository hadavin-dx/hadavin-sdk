"""The model gate: one wrapper around the model client (step F).

Guarantee: values the run has identified as sensitive are replaced by their placeholders in everything sent to a model; detection of new values is done by the producers' pattern redactor.

Stated limits of that sentence (lead review rounds 1 and 2, design review D7). Each line names the test that
pins it: T = tests/test_model_gate.py, E = tests/test_runmap_enforce_map.py. The replace is the redactor's own
sweep and follows its rule (`redact._sweep`); the full list with the reasons is in `runmap.enforce_map`.
- A known value under 3 characters is never replaced. A known value that is all digits and under 6 characters, or
  a common word (`redact._COMMON`: admin, test, web ...), is never replaced UNLESS it is a secret kind of 4
  characters or more (those are replaced in every copy).
  E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept
- Any value that is not a secret kind of 4 or more (an identifier: tenant, host, address, id) is replaced only
  where no ASCII letter or digit touches it: `abc123` inside `xabc1234` stays.
  E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept
- Only the spelling the map holds is replaced: a percent-, entity- or backslash-encoded copy, a full-width or
  other look-alike spelling and a copy split by a zero-width character pass as written.
  T::test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate
- The replace is case-sensitive: a known host or e-mail address written in another letter case passes.
  T::test_d7_stated_limit_another_letter_case_of_a_known_value_is_not_replaced
- A copy split by NUL characters (a UTF-16 document: the gate reads documents as UTF-8) or by an ANSI colour
  sequence passes: the gate does not clean the text, the producers' redactor does.
  T::test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced
  E::test_stated_limit_a_copy_split_by_nul_characters_is_not_found
- A known value that itself holds a placeholder-shaped token is never replaced, and a known value written inside
  angle brackets so that it reads as a placeholder (`<ABC_1>`) is left.
  E::test_stated_limit_a_value_holding_a_placeholder_shaped_token_is_never_replaced
  E::test_stated_limit_a_known_value_written_inside_angle_brackets_reads_as_a_placeholder
- Two known values that overlap in the text without one containing the other (`abcd` and `cdef` in `abcdef`):
  one is replaced and the tail of the other stays (`<A_1>ef`); two identifiers there are both left. A value that
  is a piece of one of the map's placeholders loses to any other value, even a shorter one.
  E::test_stated_limit_partial_overlap_leaves_a_tail
- A placeholder can be damaged, with no raw value shown: by a known value that spans the end of a placeholder
  written in the same call, and in a map whose key is not a genuine placeholder.
  E::test_stated_limit_a_value_spanning_the_end_of_a_placeholder_written_in_this_call
  E::test_m_new_2_stated_limit_a_map_key_that_is_not_a_genuine_placeholder_is_not_protected
- A text that is still changing after `runmap.ENFORCE_MAX_SWEEPS` sweeps (a chain of glued identifiers) is
  refused, not sent. E::test_mj2_a_chain_settles_within_the_cap_and_is_refused_past_it
- The gate runs no pattern: a value that is in no map passes as written, also a clean key and a clean value that
  only match a pattern once composed (`"user_id": "abc123"`).
  T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched
- A known SECRET value that equals a word of the trusted framing (the tool-result marker words, a tool name) is
  replaced there too: the marker the agent loop wrote is rewritten in what is sent. OPEN, a design decision.
  T::test_d6_gap_a_secret_equal_to_a_marker_word_rewrites_the_trusted_tool_result_marker (strict expected failure)
- With no map (`mapping=None`: the eval and replay command lines, the judge with its own map) there is no enforce
  step; every audit row of such a gate says so (`decision` is `no_map`, else `map_enforced`).
  T::test_d1_every_audit_row_says_whether_the_map_was_enforced
- Only the `content` of each message and the documents are enforced. `system`, `tools` and `output_schema` are
  operator text and are forwarded untouched, as are a message's `role` and its other keys.
  T::test_t20_system_and_tools_are_not_touched
  T::test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched
- One writer per run map (m-new-7): two threads that write ONE map at the same time through `redact_text` can
  give one placeholder number to two values. The gate only reads the map; one run has one writer today.
  Not pinned by a test (a race).

Before any provider contact the gate enforces the caller's run map on every message and document (a raw copy
of a value the map holds becomes that value's existing placeholder; `runmap.enforce_map`), then asks for the
worst-case cost, checks it and reserves it. The client gets the enforced copies. After the call the gate
settles by the one settle rule below (the real cost of a reply, 0 for a marked refusal, nothing otherwise) and
writes one audit row. If the enforce step, the worst case or the reservation fails, no call is made. The gate
keeps no prices, no budgets and no patterns: the amounts come from `worst_case` and the reply, the replace
from `runmap`. What it does decide is the ORDER of the steps and WHEN a reservation is settled.

No logger, no module-level state, and no message text and no exception text in any audit row. The gate's own
refusals (`GateRefused` and its subclasses) carry a fixed code and no cause; an error of the meter, of
`worst_case` or of the client is re-raised as the same object, with whatever chain it already had. The
caller's messages, dicts and documents are never changed in place.
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
# INTERFACE (ii), version 2 (README 2.1), as core-b PUBLISHED it: switch here if it changes
# `Meter` mirrors handover/core-c/inputs/interfaces-from-core-b/ii_meter.py line for line (same method names,
# argument order and keywords) and follows the ten contract points of the README.md beside it. That file is a
# signature file, not package code, and `limits.SpendRefused` is not in src/hadavin_sdk/limits.py yet, so the
# Protocol is kept here as a local structural one and SpendRefused is NOT imported: its `.reason` is read with
# getattr. When step F lands them, import both from hadavin_sdk.limits and delete this copy. Nothing outside
# this block names a meter method, an audit string or the worst_case arguments.
# ------------------------------------------------------------------------------------------------------
# reserve: returns a reservation id only after the worst case is booked; ANY exception means no model call.
# settle: returns the overshoot; the first call for a reservation wins. If it raises (the store is down, or
# NotFound for an id it does not know), the reply is returned anyway and reserve is never retried. The store
# adds the settled cost to the run's cost: the gate adds nothing anywhere else.
# THE ONE SETTLE RULE (ORDER 011; it replaces ORDER 006 item 8):
#   (a) a reply came back with a usable cost            -> settle that cost;
#   (b) the adapter MARKED the error as refused before any response (`refused_before_response`)
#                                                       -> settle 0;
#   (c) everything else (a timeout, used-up retries, a billed reply that failed to parse, any other
#       exception, KeyboardInterrupt / SystemExit, an abandoned thread, a reply whose cost is missing,
#       negative or not a number)                       -> NO settle: the worst case stays booked and the
#                                                          store's sweep closes the reservation.
#   README contract 3 ("a request that was refused before sending and cost nothing: settle 0") is rule (b);
#   contract 4 ("real cost unknown: do NOT settle"; the sweep closes the row after 3600 seconds) is rule (c).
# worst_case: README contract 10 makes the amount the gate's job. The gate takes the function from the
# installer (core-b offers `llm.common.worst_case_usd` in the install ticket); it must cover system, messages,
# tool schemas and documents at the input price plus max_tokens at the output price, times max_attempts.


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
CODE_WORST_CASE_FAILED = (
    "worst_case_failed"  # `worst_case` raised: its error is re-raised, no reserve
)
CODE_WORST_CASE_INVALID = "worst_case_invalid"  # it returned no finite Decimal >= 0: no reserve
CODE_RESERVE_REFUSED = "reserve_refused"  # the meter's exception has no published `.reason`
CODE_RESERVATION_INVALID = "reservation_invalid"  # reserve returned no usable id: no provider call
CODE_PROVIDER_REFUSED = (
    "provider_refused"  # rule (b): marked refused before any response, settled at 0
)
CODE_PROVIDER_ERROR = "provider_error"  # rule (c): an unmarked ProviderError, NOT settled
CODE_PROVIDER_EXHAUSTED = "provider_exhausted"  # rule (c): retries used up, NOT settled
CODE_CALL_FAILED = "call_failed"  # rule (c): any other Exception from the client, NOT settled
CODE_CALL_INTERRUPTED = "call_interrupted"  # rule (c): KeyboardInterrupt, SystemExit, NOT settled
CODE_COST_UNKNOWN = "cost_unknown"  # rule (c): a reply with no usable cost; returned, NOT settled
CODE_SETTLE_FAILED = "settle_failed"  # the meter raised in settle: the worst case stays booked
CODE_OVERSHOOT = "overshoot"  # a paid call (result ok) whose real cost was above its reservation
# The `decision` field of every row: whether this bound gate enforces a run map (design review D1).
MODE_ENFORCED = "map_enforced"
MODE_NO_MAP = "no_map"
# The reasons ii_meter.py publishes for `SpendRefused.reason` (README contract 1). Only these are copied from
# a meter's exception into an audit row: a `.reason` on any other exception that is not one of them (urllib's
# URLError has one) is never copied.
# `usd_cap` is the sixth (ORDER 014: the in-memory budget of the eval and replay command lines).
SPEND_REASONS = frozenset(
    {
        "kill_switch",
        "daily_budget",
        "monthly_budget",
        "limits_unavailable",
        "bad_amount",
        "usd_cap",
    }
)
# Every error code a row of this module can carry: the published reasons plus the gate's own.
AUDIT_CODES = SPEND_REASONS | {
    CODE_GATE_REFUSED,  # what `_note` writes in place of a code that is not in this set
    CODE_MASK_REFUSED,
    CODE_WORST_CASE_FAILED,
    CODE_WORST_CASE_INVALID,
    CODE_RESERVE_REFUSED,
    CODE_RESERVATION_INVALID,
    CODE_PROVIDER_REFUSED,
    CODE_PROVIDER_ERROR,
    CODE_PROVIDER_EXHAUSTED,
    CODE_CALL_FAILED,
    CODE_CALL_INTERRUPTED,
    CODE_COST_UNKNOWN,
    CODE_SETTLE_FAILED,
    CODE_OVERSHOOT,
}


def refused_before_response(exc: BaseException) -> bool:
    """Rule (b). True only for a ProviderError (not ProviderExhausted: its attempts may have been answered)
    that the adapter marked with `refused_before_response = True`. llm/retry.py sets no such mark yet
    (handover/core-c/requests/2-refused-before-response.md), so today this is False for every real error
    and every failed call keeps its worst case booked."""
    marked = getattr(exc, "refused_before_response", False) is True
    return marked and isinstance(exc, ProviderError) and not isinstance(exc, ProviderExhausted)


def usable_amount(value: Any) -> bool:
    """A finite Decimal that is not negative: the only amount the gate reserves or settles with."""
    return isinstance(value, Decimal) and value.is_finite() and value >= 0


def usable_cost(reply: Any) -> Decimal | None:
    """Rule (a): the reply's cost when it is a usable amount, else None."""
    cost = getattr(reply, "cost_usd", None)
    return cost if usable_amount(cost) else None


# END OF INTERFACE (ii)
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


class WorstCaseInvalid(GateRefused):
    """`worst_case` returned something that is not a finite Decimal >= 0 (a float, None, NaN, a negative
    amount): nothing was reserved and no call was made. The gate does not trust the installer's function."""

    code = CODE_WORST_CASE_INVALID


class ReservationInvalid(GateRefused):
    """The meter's `reserve` returned something that is not a non-empty str: there is nothing to settle
    against, so no call was made. Whatever the meter booked stays booked until its sweep."""

    code = CODE_RESERVATION_INVALID


class ModelGate:
    """Holds the client, the meter, the audit sink, the worst-case function and the enforce step. It has NO
    `chat`: a caller must `bind` it to an agent and a run first, so an unbound gate cannot call a model.
    A client that is itself a gate is refused (TypeError), so the direct case of one call reserved twice
    cannot be built; a gate hidden inside another wrapper is NOT detected."""

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
        """A gate for one call site. `mapping` is the run's LIVE map, kept by reference and never written:
        every `chat` takes one copy of it (`runmap.snapshot`), so a value the run masks later is replaced in
        earlier text on the next call. The map has ONE writer at a time (the run's own thread, through
        `redact_text`); the gate may read it from another thread. None (a site with no run map) means no
        enforce step, and every audit row then says `no_map`. `principal` defaults to the agent id.
        The ids go into audit rows: one that is not a str is a TypeError here, not a row lost later."""
        if not all(isinstance(value, str) for value in (agent_id, run_id, source)):
            raise TypeError("agent_id, run_id and source must be str")
        if principal is not None and not isinstance(principal, str):
            raise TypeError("principal must be a str or None")
        return BoundGate(self, agent_id, run_id, mapping, principal or agent_id, source)


class BoundGate:
    """Satisfies `llm.protocol.LLM`. Order: enforce the map, worst case, reserve, provider call, settle (by
    the one settle rule in the interface block above), audit row."""

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
        self._mode = MODE_NO_MAP if mapping is None else MODE_ENFORCED

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
        except Exception:
            self._note(RESULT_REFUSED, CODE_WORST_CASE_FAILED)
            raise
        if not usable_amount(reserved):
            self._note(RESULT_REFUSED, CODE_WORST_CASE_INVALID)
            raise WorstCaseInvalid
        try:
            reservation = self._meter.reserve(self._agent_id, reserved, run_id=self._run_id)
        except Exception as exc:
            reason = getattr(exc, "reason", None)
            published = isinstance(reason, str) and reason in SPEND_REASONS
            self._note(RESULT_REFUSED, reason if published else CODE_RESERVE_REFUSED)
            raise
        if not (isinstance(reservation, str) and reservation):
            self._note(RESULT_REFUSED, CODE_RESERVATION_INVALID)
            raise ReservationInvalid
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
        if (
            cost is None
        ):  # rule (c): the call is paid and its reply is returned; nothing to settle with
            self._note(RESULT_OK, CODE_COST_UNKNOWN, reservation)
        else:  # rule (a)
            self._settle(reservation, cost, RESULT_OK, None)
        return reply

    def _settle(self, reservation: str, usd: Decimal, result: str, code: str | None) -> None:
        """Settle once and write the row. A raising meter never loses a paid reply and never hides the
        client's error: the row then says `settle_failed` (with the call's own result, so a paid call is
        still counted as `ok`) and the worst case stays booked. A paid call that cost more than was
        reserved (settle returns the overshoot) stays `ok` and carries the code `overshoot`."""
        try:
            over = self._meter.settle(reservation, usd)
            if code is None and usable_amount(over) and over > 0:
                code = CODE_OVERSHOOT
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
        bad bytes replaced). The live map is copied ONCE here (`runmap.snapshot`): every text of this call is
        enforced against the same entries, and the patterns are built at most once per call."""
        mapping = self._mapping
        try:
            if mapping is not None:
                mapping = runmap.snapshot(mapping)
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
        if error_code is not None and not (
            isinstance(error_code, str) and error_code in AUDIT_CODES
        ):
            error_code = CODE_GATE_REFUSED  # AUDIT_CODES is enforced here, not only listed
        with contextlib.suppress(Exception):
            self._audit.write_outcome(
                AuditEvent(
                    run_id=self._run_id,
                    domain=AUDIT_DOMAIN,
                    operation=AUDIT_OPERATION,
                    principal=self._principal,
                    source=self._source,
                    object_ref=reservation if isinstance(reservation, str) else None,
                    decision=self._mode,
                    result=result,
                    error_code=error_code,
                )
            )
