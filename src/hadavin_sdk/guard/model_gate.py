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
- A known value that begins with the tail of a placeholder (`>abc`) or ends with the head of one (`xyz<`) is
  replaced only where it stands clear of every placeholder: beside a placeholder written in the same call its
  tail stays readable (`<SECRET_1>abc`), but the placeholder is never cut open.
  E::test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass
- In a map whose key is not a genuine placeholder (`<host_1>`) a placeholder can be damaged, with no raw value
  shown. E::test_m_new_2_stated_limit_a_map_key_that_is_not_a_genuine_placeholder_is_not_protected
- One original held under two placeholders follows the stronger rule (a secret kind wins over an identifier
  kind, whatever the order). E::test_e5_one_original_under_two_placeholders_follows_the_stronger_rule
- A text that is still changing after `runmap.ENFORCE_MAX_SWEEPS` sweeps (a chain of glued identifiers) is
  refused, not sent. E::test_mj2_a_chain_settles_within_the_cap_and_is_refused_past_it
- The gate runs no pattern: a value that is in no map passes as written, also a clean key and a clean value that
  only match a pattern once composed (`"user_id": "abc123"`).
  T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched
- The trusted framing of a tool result (`<<TOOL RESULT call_id=ID tool=NAME>>` ... `<<END TOOL RESULT>>`, written by
  runtime/agent_loop.py) is never rewritten: the tokens are set aside and only the text between them is
  enforced. A call that carries framing (or an assistant line `tool NAME {...}`) is REFUSED, code
  `framing_refused`, when a known value EQUALS a marker word (TOOL, RESULT, END, call_id, tool), a tool name or a
  call id: a document can plant such a value (`password=RESULT`) and a run is then stopped by it (a stated cost
  of the order: a planted word stops a run that uses tools; it cannot stop one that uses none).
  T::test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker
  T::test_o17_6_a_value_that_only_lies_inside_a_framing_token_leaves_the_token_alone
  T::test_o17_6_a_tool_name_from_the_tools_list_or_an_assistant_line_counts_too
- With no map (`bind(..., mapping=NO_MAP)`: the eval and replay command lines only) there is no enforce step;
  every audit row of such a gate says so (`AuditEvent.decision` is `no_map`, else `map_enforced`). `mapping` is a
  required keyword; None is a TypeError.
  T::test_d1_every_audit_row_says_whether_the_map_was_enforced
  T::test_o17_1_bind_without_mapping_is_a_type_error_and_so_is_none_or_a_non_mapping
- Only the `content` of each message and the documents are enforced. `system`, `tools` and `output_schema` are
  operator text and are forwarded untouched, as are a message's `role` and its other keys.
  T::test_t20_system_and_tools_are_not_touched
  T::test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched
- A reply whose cost is absent or not a usable number (None, a float, NaN, negative) is returned and NOT settled
  (`cost_unknown`; the worst case stays booked). `models.Reply.cost_usd` defaults to Decimal(0), so an adapter that
  sets no cost looks like a free call: core-b must change that default.
  T::test_o17_2_a_reply_whose_cost_is_absent_or_not_a_usable_number_is_cost_unknown_and_not_settled
- One writer per run map (m-new-7): two threads that write ONE map at the same time through `redact_text` can
  give one placeholder number to two values. The gate only reads the map; one run has one writer today.
  Not pinned by a test (a race).

Before any provider contact the gate enforces the caller's run map on every message and document (a raw copy
of a value the map holds becomes that value's existing placeholder; `runmap.enforce_map`), then asks for the
worst-case cost, checks that it is a finite Decimal of 0 or more, and reserves it. The client gets the enforced
copies. After the call the gate settles by the one settle rule below (the real cost of a reply that has a usable
cost, 0 for an error the adapter marked as refused before any response, otherwise no settle) and writes one
audit row. If the enforce step, the worst case or the reservation fails, no call is made.

What the gate keeps and what it does not. It keeps no prices, no budgets and no patterns: the amounts come from
`worst_case` and the reply, the replace from `runmap`, the booking from the meter. It does hold three small
money rules of its own: an amount is usable only when it is a finite Decimal of 0 or more (reserve and settle),
the ORDER of the steps, and WHEN a reservation is settled (the one settle rule).

Exceptions and text. No logger, no module-level state, and no message text and no exception text in any audit
row (a source guard in tests/test_model_gate.py reads the whole module's syntax tree for this). EVERY failure
before the provider call that is not a `SpendRefused` (the enforce step, `worst_case` raising or returning a bad
amount, `reserve` failing with a KeyError or a store error, a bad reservation id, a framing conflict) is raised
as `GateRefused` or a subclass: a fixed `code` and neither a cause nor a context (raised outside any `except`
block), so for the caller `GateRefused` means 'no provider call was made'. A `SpendRefused` (a meter error whose
`.reason` is one of the six published reasons) and an error of the client pass as the same object with whatever
chain it already had: the gate adds nothing to it and removes nothing. The caller's messages, dicts and
documents are never changed in place.
"""

from __future__ import annotations

import contextlib
import re
from collections.abc import Callable, Mapping
from decimal import Decimal
from typing import Any, Protocol

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.guard import runmap
from hadavin_sdk.llm.protocol import LLM, ProviderError, ProviderExhausted
from hadavin_sdk.models import AuditEvent, Reply
from hadavin_sdk.tools import END_MARKER, START_MARKER

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
CODE_FRAMING_REFUSED = (
    "framing_refused"  # a known value equals a word of the trusted framing: no call
)
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
# The trusted framing of a tool result (runtime/agent_loop.py builds `<<TOOL RESULT call_id=ID tool=NAME>>`, the
# text, then `<<END TOOL RESULT>>`; the markers are `tools.START_MARKER` and `tools.END_MARKER`). The gate never
# replaces inside these tokens, and refuses a call when a known value EQUALS one of their words, a tool name or a
# call id (ORDER 017 item 6; reproduced with the real producers in tests/test_model_gate.py).
FRAMING_WORDS = frozenset(
    {*START_MARKER.strip("<>").split(), *END_MARKER.strip("<>").split(), "call_id", "tool"}
)
_FRAMING_START = re.escape(START_MARKER) + r" call_id=([^\s>]+) tool=([^\s>]+)>>"
FRAMING = re.compile(_FRAMING_START + "|" + re.escape(END_MARKER))
_ASSISTANT_CALL = re.compile(
    r"tool ([^\s{]+) "
)  # the assistant line `tool NAME {inputs}` of the same loop
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
    CODE_FRAMING_REFUSED,
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


def framing_free(
    messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, mapping: Mapping[str, str]
) -> bool:
    """False when a value the map holds EQUALS a word of the trusted framing, a tool name or a call id: a
    hostile document can plant such a value (`password=RESULT`) and every later copy of the framing word would be
    rewritten. It matters only in a call that carries tool-result framing (a start or end marker, or an assistant
    line `tool NAME {...}`); a call with none is not looked at, so a planted word cannot stop a run that uses no
    tools. Tool names come from the `tools` list and the assistant lines, call ids and names from the markers.
    Equality only: a value that merely lies inside a marker is protected by `BoundGate._enforce_text`. Returns a
    bool; the value is never returned or logged."""
    names: set[str] = set()
    framed = False
    for message in messages:
        content = message["content"]
        for token in FRAMING.finditer(content):
            framed = True
            names.update(group for group in token.groups() if group)
        call = _ASSISTANT_CALL.match(content) if message.get("role") == "assistant" else None
        if call:
            framed = True
            names.add(call.group(1))
    if not framed:
        return True
    names |= FRAMING_WORDS
    for tool in tools or ():
        if isinstance(tool, dict) and isinstance(tool.get("name"), str):
            names.add(tool["name"])
    return names.isdisjoint(mapping.values())


class GateRefused(RuntimeError):
    """THE gate exception: the gate made NO provider call. Every failure before the provider call that is not a
    `SpendRefused` (the enforce step, `worst_case`, the meter's `reserve` failing with anything but a SpendRefused
    such as a KeyError or a store that is down, a bad reservation id, a framing conflict) is raised as this type or
    one of its subclasses. It carries a stable `code` and nothing else: never text, never a secret, no cause and
    no context (it is raised outside any `except` block). A `SpendRefused` passes unchanged and an error of the
    client passes unchanged; core-b catches `GateRefused` for 'no call made, nothing booked by the gate'."""

    code = CODE_GATE_REFUSED

    def __init__(self, code: str | None = None) -> None:
        if code is not None:
            self.code = code
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


class FramingRefused(GateRefused):
    """A value of the run's map equals a word of the trusted tool-result framing, a tool name or a call id."""

    code = CODE_FRAMING_REFUSED


class _NoMap:
    """The type of `NO_MAP`. One instance; it is not a mapping and holds nothing."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "NO_MAP"


# `bind(..., mapping=NO_MAP)` says, on purpose and in the call, that this call site has no run map: no enforce step
# runs and every audit row says `no_map`. Only the eval and replay command lines (which have no run) may use it.
NO_MAP = _NoMap()


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
        mapping: Mapping[str, str] | _NoMap,
        principal: str | None = None,
        source: str = DEFAULT_SOURCE,
    ) -> BoundGate:
        """A gate for one call site. `mapping` is REQUIRED (ORDER 017 item 1): the run's LIVE map, kept by
        reference and never written: every `chat` takes one copy of it (`runmap.snapshot`), so a value the run
        masks later is replaced in earlier text on the next call. The map has ONE writer at a time (the run's own
        thread, through `redact_text`); the gate may read it from another thread. A site with no run map says so
        with `mapping=NO_MAP` (the eval and replay command lines only): no enforce step runs and every audit row
        says `no_map` in its `decision` field. None, or anything that is not a Mapping, is a TypeError: a
        forgotten map can no longer switch the guarantee off without a trace. `principal` defaults to the agent
        id. The ids go into audit rows: one that is not a str is a TypeError here, not a row lost later."""
        if not isinstance(mapping, Mapping | _NoMap):
            raise TypeError("mapping must be a Mapping (the run's map) or NO_MAP")
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
        mapping: Mapping[str, str] | _NoMap,
        principal: str,
        source: str,
    ) -> None:
        self._llm, self._meter, self._audit = gate._llm, gate._meter, gate._audit
        self._worst_case, self._enforce = gate._worst_case, gate._enforce
        self._agent_id, self._run_id, self._mapping = agent_id, run_id, mapping
        self._principal, self._source = principal, source
        self._mode = MODE_NO_MAP if isinstance(mapping, _NoMap) else MODE_ENFORCED

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
        enforced = self._enforced(messages, documents, tools)
        if isinstance(enforced, str):  # a failure code: nothing was sent, nothing is reserved
            self._note(RESULT_REFUSED, enforced)
            if enforced == CODE_FRAMING_REFUSED:
                raise FramingRefused  # raised outside any `except`: no cause and no context to leak
            raise UnmaskedInput  # raised outside any `except`: no cause and no context to leak
        messages, documents = enforced  # from here on only the enforced copies are used
        failure: str | None = None
        reserved, reservation = Decimal(0), ""
        try:
            reserved = self._worst_case(route, system, messages, tools, documents, output_schema)
        except Exception:  # noqa: BLE001 - its error is NOT passed on (it may carry text): a code instead
            failure = CODE_WORST_CASE_FAILED
        if failure is None and not usable_amount(reserved):
            failure = CODE_WORST_CASE_INVALID
        if failure is None:
            try:
                reservation = self._meter.reserve(self._agent_id, reserved, run_id=self._run_id)
            except Exception as exc:
                reason = getattr(exc, "reason", None)
                if isinstance(reason, str) and reason in SPEND_REASONS:
                    self._note(RESULT_REFUSED, reason)
                    raise  # a SpendRefused passes unchanged
                failure = CODE_RESERVE_REFUSED  # a KeyError, a down store: a code, not the error
        if failure is None and not (isinstance(reservation, str) and reservation):
            failure = CODE_RESERVATION_INVALID
        if failure is not None:  # no call; raised outside the handlers, so with no chain
            self._note(RESULT_REFUSED, failure)
            if failure == CODE_WORST_CASE_INVALID:
                raise WorstCaseInvalid
            if failure == CODE_RESERVATION_INVALID:
                raise ReservationInvalid
            raise GateRefused(failure)
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
        self,
        messages: list[dict[str, Any]],
        documents: list[bytes] | None,
        tools: list[dict[str, Any]] | None,
    ) -> tuple[list[dict[str, Any]], list[bytes] | None] | str:
        """New lists holding what will be sent, or a failure code (`mask_refused`, `framing_refused`) when the step
        failed (then nothing is sent). A message or document in which nothing is replaced is passed on as the
        same object, so the bytes are the caller's; one with a replaced value is a new dict or new bytes. A
        content that is not `str` is refused with or without a map. Documents are read as the adapters read them
        (`llm/common.py` `turns`: UTF-8, bad bytes replaced). The live map is copied ONCE here (`runmap.snapshot`):
        every text of this call is enforced against the same entries, and the patterns are built at most once
        per call. The framing tokens of a tool result are never replaced inside (`_enforce_text`)."""
        mapping = self._mapping
        try:
            if isinstance(mapping, _NoMap):
                mapping = None
            else:
                mapping = runmap.snapshot(mapping)
            sent: list[dict[str, Any]] = []
            for message in messages:
                content = message["content"] if isinstance(message, dict) else None
                if not isinstance(content, str):
                    return CODE_MASK_REFUSED
                if mapping is not None:
                    fixed = self._enforce_text(content, mapping)
                    if not isinstance(fixed, str):
                        return CODE_MASK_REFUSED
                    if fixed != content:
                        message = {**message, "content": fixed}
                sent.append(message)
            if mapping is not None and not framing_free(messages, tools, mapping):
                return CODE_FRAMING_REFUSED
            if documents is None:
                return sent, None
            docs: list[bytes] = []
            for document in documents:
                if not isinstance(document, bytes):
                    return CODE_MASK_REFUSED
                if mapping is not None:
                    text = document.decode("utf-8", "replace")
                    fixed = self._enforce(text, mapping)
                    if not isinstance(fixed, str):
                        return CODE_MASK_REFUSED
                    if fixed != text:
                        document = fixed.encode("utf-8")
                docs.append(document)
        except Exception:  # noqa: BLE001 - fail closed: a step that cannot finish means no call
            return CODE_MASK_REFUSED
        return sent, docs

    def _enforce_text(self, text: str, mapping: Mapping[str, str]) -> str:
        """Enforce the map on one message content, leaving every framing token of a tool result exactly as the
        agent loop wrote it (`<<TOOL RESULT call_id=ID tool=NAME>>`, `<<END TOOL RESULT>>`): only the stretches
        between them are enforced. A text with no framing token is enforced whole."""
        parts: list[str] = []
        end = 0
        for token in FRAMING.finditer(text):
            if token.start() > end:
                parts.append(self._enforce(text[end : token.start()], mapping))
            parts.append(token.group(0))
            end = token.end()
        if end == 0:
            return self._enforce(text, mapping)
        if end < len(text):
            parts.append(self._enforce(text[end:], mapping))
        return "".join(parts)

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
