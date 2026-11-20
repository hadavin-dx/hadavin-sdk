"""The model gate: one wrapper around the model client (step F).

Guarantee: values the run has identified as sensitive are replaced by their placeholders in the `content` of every message and in every document sent to a model; detection of new values is done by the producers' pattern redactor. NOT enforced: `system`, `tools` and `output_schema` are operator text and are forwarded untouched (the install-time check that `system` comes only from the prompt registry belongs to core-b), and a message's `role` and other keys.

Stated limits of that sentence (lead review rounds 1 and 2, design review D7). Each line names the test that
pins it: T = tests/test_model_gate.py, E = tests/test_runmap_enforce_map.py. The replace is the redactor's own
sweep and follows its rule (`redact._sweep`); the full list with the reasons is in `runmap.enforce_map`.
- A known value under 3 characters is never replaced. A known value that is all digits and under 6 characters, or
  a common word (`redact._COMMON`: admin, test, web ...), is never replaced UNLESS it is a secret kind of 4
  characters or more (those are replaced in every copy).
  E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept
- Any value that is not a secret kind of 4 or more (an identifier: tenant, host, address, id) is replaced only
  where no ASCII letter or digit touches it: `abc123` inside `xabc1234` stays. A PHONE value is replaced where no
  digit touches it (ticket G8): a known `4155550132` in `build4155550132` is sent to the model as `build<PHONE_1>`.
  E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept
- Only the spelling the map holds is replaced: a percent-, entity- or backslash-encoded copy, a full-width or
  other look-alike spelling and a copy split by a zero-width character pass as written. EXCEPTION (code review round
  3, M2): for a value that is not ASCII the redactor also sweeps its folded (NFKC) spellings, so a full-width
  `TENANT` known as such is replaced, and so is the plain `TENANT`; each spelling is its own item and never cuts
  the placeholder written for another. Since G13 (E19 M2) the net reads those forms: for a value of a SECRET kind the
  call is then refused (`held_value_left`); an identifier in such a form passes as written.
  T::test_t7_a_hidden_spelling_of_a_known_secret_refuses_the_call_an_identifier_passes
  T::test_r3_c_m2_stated_rule_the_sweep_also_replaces_the_folded_spelling_of_a_non_ascii_value
- The replace is case-sensitive: a known host or e-mail address written in another letter case passes.
  T::test_d7_stated_limit_another_letter_case_of_a_known_value_is_not_replaced
- The gate does not clean the text it sends. A copy of a SECRET value split by NUL characters (a UTF-16 document: the
  gate reads documents as UTF-8) refuses the call (G13: the net reads the text without NUL); a copy of an identifier split
  so, and any copy split by an ANSI colour sequence, passes as written.
  T::test_g13b_5_the_stated_limits_a_base64_copy_and_a_nul_split_identifier_are_sent
  T::test_d7_a_copy_split_by_nul_or_utf16_refuses_the_call_an_ansi_split_copy_passes
  E::test_stated_limit_a_copy_split_by_nul_characters_is_not_found
- A known value that itself holds a placeholder-shaped token is never replaced, and a known value written inside
  angle brackets so that it reads as a placeholder (`<ABC_1>`) is left by the sweep. For a value of a SECRET kind
  the gate's net then refuses the call (`held_value_left`, below); for an identifier kind the value passes as written.
  Placeholder-shaped means ASCII capitals and digits and `_` followed by digits of ANY script (`\\d`), and
  `isdigit()` counts digits of any script too: 'all digits' in these limits means that.
  E::test_stated_limit_a_value_holding_a_placeholder_shaped_token_is_never_replaced
  E::test_stated_limit_a_known_value_written_inside_angle_brackets_reads_as_a_placeholder
  E::test_r3_n7_stated_limit_digits_of_any_script_count_as_digits_and_as_placeholder_digits
- Two known values that overlap in the text without one containing the other (`abcd` and `cdef` in `abcdef`):
  since G9 the text read back with the map's placeholders put back is checked, and the readable rest is replaced
  by the EXISTING placeholder of a value that covers it, a secret's where one does, else the identifier's
  (`<SECRET_1><SECRET_2>`, `<TENANT_1><TENANT_2>`; the map is not written; restored, the shared part of two
  identifiers appears twice). Two identifiers that touch each other there are both left. A value that is a piece
  of one of the map's placeholders is not in the main sweep: its rest stays. The net (`held_value_left`)
  checks values of SECRET kinds only: the rest of a held-back secret refuses the call, the rest of a held-back identifier passes
  silently (a stated limit).
  E::test_trap3_a_partial_overlap_of_two_secret_values_is_masked_with_their_placeholders
  E::test_trap3_an_overlap_of_two_identifiers_is_masked_with_their_placeholders
- A known value that begins with the tail of a placeholder (`>abc`) or ends with the head of one (`xyz<`) is
  replaced only where it stands clear of every placeholder: beside a placeholder written in the same call its
  tail stays readable (`<SECRET_1>abc`), but the placeholder is never cut open. For a SECRET value the net refuses
  the call when 4 or more of its characters stand there (G13).
  E::test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass
- In a map whose key is not a genuine placeholder (`<host_1>`) a placeholder can be damaged, with no raw value
  shown. E::test_m_new_2_stated_limit_a_map_key_that_is_not_a_genuine_placeholder_is_not_protected
- One original held under two placeholders follows the stronger rule (a secret kind wins over an identifier
  kind, whatever the order). E::test_e5_one_original_under_two_placeholders_follows_the_stronger_rule
- A text that is still changing after `runmap.ENFORCE_MAX_SWEEPS` sweeps (a chain of glued identifiers) is
  refused, not sent. E::test_mj2_a_chain_settles_within_the_cap_and_is_refused_past_it
- The net (`runmap.held_value_left`, code `held_value_left`): after each enforced chunk, a value of a SECRET kind
  (4 or more characters) that still stands raw refuses the call. Only an exact KEY of the map hides a value: a
  forged `<AKIA...EXAMPLE_1>` does not. Each chunk is checked on its own, so a value that SPANS a chunk (a fixed
  framing word between: `password="tool read_logs"`) is cut by it and passes as written; checking it would also
  refuse every value that merely lies inside a fixed word (`ESULT`). G13 (E19): the net also refuses (1) a piece of 4 or
  more characters of a SECRET value that touches a key of the map and is the value's start (before the key) or end (after
  it): `hunter2-<SECRET_2>`, and (2) a SECRET value found in a decoded form of the chunk (`runmap.held_in_views`: without
  NUL, NFKC, invisible characters removed, JSON/percent/entity/backslash escapes undone, composed). G13b: a piece that is
  only the public start of a value (`https://` of a webhook URL, `Bearer `) or only separator characters is not read,
  so `https://<HOSTNAME_1>/health` is sent beside a webhook value (a secret whose own first characters are ordinary
  words still refuses text that starts so beside a key: a stated limit). A text over `runmap.VIEW_WINDOW` is read in
  windows; a value of more than 1,636 characters gets an overlap of `runmap.WINDOW_OVERLAP_MAX` only (its raw copy is
  found on the whole text). NOT read: a piece from the middle of a value between two keys, a piece one character
  away from a key, a piece shorter than 4, another letter case, an ANSI-split copy, a base64-encoded copy (the
  producers' G4 step), a copy in several stacked escape layers (`%26%23...`) that crosses a window edge of a text over
  `VIEW_WINDOW` characters and is longer than the overlap, and the forms the decoder does not undo: UTF-7,
  quoted-printable, hex or ROT13 dumps, reversed text, homoglyphs NFKC leaves alone, a secret wrapped across lines.
  T::test_g13_10_a_secret_in_a_decoded_form_refuses_the_call
  T::test_g13_13_m1_a_secret_prefix_beside_a_key_refuses_the_call
  T::test_g13b_1_a_url_scheme_beside_a_key_is_sent_while_a_webhook_value_is_in_the_map
  T::test_g13b_3_a_long_secret_does_not_refuse_a_long_non_ascii_chunk
  T::test_g13b_5_the_stated_limits_a_base64_copy_and_a_nul_split_identifier_are_sent
  E::test_g13_4_boundaries_of_the_piece_rule
  T::test_r3_m3_a_secret_hidden_in_a_placeholder_shaped_token_that_is_not_a_key_refuses_the_call
  T::test_r3_m3_the_net_covers_every_secret_value_not_only_the_held_back_ones
  T::test_r3_n2_stated_limit_a_value_spanning_a_fixed_framing_word_is_not_replaced
- Budgets (design review round 3, M1 M2 N5): one budget per chat call (characters, steps, time). A step is one per
  text and one per held-back value that occurs in it; the time is a CPU deadline given to the redactor's sweep. At most
  `runmap.ENFORCE_MAX_ENTRIES` entries and `runmap.ENFORCE_MAX_HELD` held-back values; past a budget the call is
  refused with its own code `mask_budget_exceeded` (a subclass of `UnmaskedInput`). NOT bounded: ONE regex scan of
  ONE text stretch inside the redactor (a 256 KB text of `a` with 500 planted `aaa...` values takes about 7 s before
  the deadline is read: slicing the scan is redact.py's job, see ESCALATIONS). The pattern state is kept in the bound
  gate between calls. At most `MAX_FRAMING_TOKENS` framing tokens are read per message; what follows is plain text.
  T::test_r3_m1b_planted_held_values_past_the_old_cap_of_256_do_not_brick_the_run
  T::test_r3_m1_an_honest_long_history_with_a_big_held_set_is_not_refused
  T::test_r3_n5_a_message_of_thousands_of_forged_tokens_costs_a_bounded_number_of_enforce_calls
  T::test_r3_m2_a_deadline_inside_the_sweep_is_a_budget_refusal_with_its_own_code
  T::test_r3_m2_the_patterns_are_built_once_per_map_change_even_with_a_held_back_value
- The gate runs no pattern: a value that is in no map passes as written, also a clean key and a clean value that
  only match a pattern once composed (`"user_id": "abc123"`).
  T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched
- The trusted framing of a tool result (`<<TOOL RESULT call_id=ID tool=NAME>>` ... `<<END TOOL RESULT>>`, written by
  runtime/agent_loop.py) keeps its FIXED words exactly (`<<TOOL RESULT call_id=`, ` tool=`, `>>`, the end marker,
  and the `tool ` of an assistant line `tool NAME {...}`); the call id, the tool name and everything between the
  tokens ARE enforced (review round 2, dz2-B1: a forged token `call_id=x_<secret>_y` is not a hiding place). A
  tool name is enforced the same way in the assistant line and in the token, so both read alike. A call is
  REFUSED, code `framing_refused`, only when a value of a SECRET kind (4 or more characters, swept in every copy)
  EQUALS a tool name (the `tools` list, an assistant line, a token) or a call id, or is a SUBSTRING of a name in the
  `tools` list: the `tools` list is forwarded untouched and would show it. A tool name that is in the call's `tools`
  stays EXACT in the assistant line and the token (an identifier inside it, tenant `billing` in `get_billing_info`,
  is not rewritten); a name that is only in a message is enforced. A host or tenant named `tool` or `search`
  does not stop a run. A document is enforced whole: a framing token inside a document is data. A planted value that
  equals a tool name refuses every later call of the run (design review round 3, M1a): keeping such a value out of the
  map is the producer side's job (core-b, request 3), the gate cannot tell it from a real secret.
  T::test_o17_6_reproduction_a_planted_value_that_equals_a_framing_word_rewrites_the_trusted_marker
  T::test_o17_6_a_value_that_only_lies_inside_a_framing_word_leaves_the_fixed_words_alone
  T::test_r2_b1_a_known_value_inside_a_token_slot_never_reaches_the_client
  T::test_o17_6_a_tool_name_from_the_tools_list_or_an_assistant_line_counts_too
  T::test_r2_m4_an_identifier_kind_value_equal_to_a_tool_name_does_not_stop_the_run
  T::test_r3_c_m1_a_tool_name_in_the_tools_list_stays_exact_when_a_known_value_lies_inside_it
  T::test_r3_c_m1_a_secret_that_is_part_of_a_listed_tool_name_refuses_the_call
  T::test_r3_n1_a_framing_token_inside_the_name_of_an_assistant_line_is_not_copied_twice
- With no map (`bind(..., mapping=NO_MAP)`: the eval and replay command lines only) there is no enforce step;
  every audit row of such a gate says so (`AuditEvent.decision` is `no_map`). `map_enforced` is written only when
  the enforce function is the module default (`runmap.enforce_map`) AND the call's map held an entry
  (`map_enforced_empty` otherwise); an injected `enforce=` is `enforce_custom`; a refusal of the enforce step is
  `map_failed`. The row says what was configured; it is not a proof that every value was replaced.
  `mapping` is a required keyword; it must be a `runmap.RunMap` or NO_MAP, anything else (None, a plain dict, a
  `dict(run_map)` copy) is a TypeError. An EMPTY run map is accepted and marked `map_enforced_empty` (contested with
  ORDER 020 m-2: the lead decides; pinned, not endorsed). `enforce=` is a test-only hook.
  T::test_r3_m4_an_enforce_function_other_than_the_default_is_marked_and_documented_as_test_only
  T::test_r2_m5_the_audit_decision_says_what_was_really_enforced
  T::test_d1_every_audit_row_says_whether_the_map_was_enforced
  T::test_o17_1_bind_without_mapping_is_a_type_error_and_so_is_none_or_a_non_mapping
- A document is read as the adapters read it (UTF-8, bad bytes replaced): a binary document is decoded lossily
  and what the gate sends is that text. Not pinned beyond the existing bytes tests.
- Only the `content` of each message and the documents are enforced. `system`, `tools` and `output_schema` are
  operator text and are forwarded untouched, as are a message's `role` and its other keys.
  T::test_t20_system_and_tools_are_not_touched
  T::test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched
- A reply whose cost is absent or not a usable number (None, a float, NaN, negative, `-0`, an absurd exponent, or a
  `cost_usd` that raises on read) is returned and NOT settled (`cost_unknown`; the worst case stays booked). `models.Reply.cost_usd` defaults to Decimal(0), so an adapter that
  sets no cost looks like a free call: core-b must change that default.
  T::test_o17_2_a_reply_whose_cost_is_absent_or_not_a_usable_number_is_cost_unknown_and_not_settled
  T::test_r3_n3_a_cost_or_worst_case_that_is_not_a_sane_amount_is_not_usable
  T::test_r3_n3_a_cost_property_that_raises_after_the_paid_call_is_cost_unknown_and_the_reply_is_returned
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
row (a source guard in tests/test_model_gate.py reads the whole module's syntax tree for this). Every failure
before the provider call that is an Exception and not a `SpendRefused` (the enforce step, `worst_case` raising or returning a bad
amount, `reserve` failing with a KeyError or a store error, a bad reservation id, a framing conflict) is raised
as `GateRefused` or a subclass: a fixed `code` and neither a cause nor a context (raised outside any `except`
block), so for the caller `GateRefused` means 'no provider call was made'. A BaseException (KeyboardInterrupt) in
the enforce step, `worst_case`, `reserve` or the instant after it writes a row (`call_interrupted`,
`reserve_interrupted`) and passes on as it is: for
`reserve` the meter may already have booked the amount (the sweep closes it). A `SpendRefused` (a meter error whose
`.reason` is one of the six published reasons) and an error of the client pass as the same object with whatever
chain it already had: the gate adds nothing to it and removes nothing. The caller's messages, dicts and
documents are never changed in place.
"""

from __future__ import annotations

import contextlib
import itertools
import re
from collections.abc import Callable, Mapping
from decimal import Decimal
from typing import Any, Protocol, Self

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
#                                                       -> settle 0. The mark counts on a ProviderError and
#                                                          on a ProviderExhausted (then it means EVERY attempt
#                                                          the retry layer made was refused, nothing billed);
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


_DEFAULT_ENFORCE = runmap.enforce_map  # the audit says `map_enforced` only for this function
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
CODE_MASK_BUDGET = (
    "mask_budget_exceeded"  # the enforce step ran out of its size, step or time budget: no call
)
CODE_WORST_CASE_FAILED = "worst_case_failed"  # `worst_case` raised: its error is NOT passed on (it may carry text), no reserve
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
CODE_RESERVE_INTERRUPTED = "reserve_interrupted"  # a BaseException in `reserve`: it may have booked
CODE_HELD_LEFT = "held_value_left"  # a held-back secret value still raw after the sweeps: no call
CODE_COST_UNKNOWN = "cost_unknown"  # rule (c): a reply with no usable cost; returned, NOT settled
CODE_SETTLE_FAILED = "settle_failed"  # the meter raised in settle: the worst case stays booked
CODE_OVERSHOOT = "overshoot"  # a paid call (result ok) whose real cost was above its reservation
# The `decision` field of every row: whether this bound gate enforces a run map (design review D1).
MODE_ENFORCED = "map_enforced"  # the default enforce function ran against a map with entries
MODE_EMPTY = "map_enforced_empty"  # the default function, but the run's map held no entry
MODE_CUSTOM = "enforce_custom"  # an injected `enforce=` (tests): not the module's function
MODE_FAILED = "map_failed"  # the enforce step refused: nothing was sent
MODE_NO_MAP = "no_map"
# The trusted framing of a tool result (runtime/agent_loop.py builds `<<TOOL RESULT call_id=ID tool=NAME>>`, the
# text, then `<<END TOOL RESULT>>`; the markers are `tools.START_MARKER` and `tools.END_MARKER`). The gate never
# replaces inside the FIXED words of these tokens; the call id, the tool name and the text between are enforced.
FRAMING = re.compile(
    "(?P<head>"
    + re.escape(START_MARKER)
    + r" call_id=)(?P<id>[^\s>]+)(?P<mid> tool=)(?P<name>[^\s>]+)(?P<tail>>>)"
    + "|(?P<end>"
    + re.escape(END_MARKER)
    + ")"
)
_ASSISTANT_CALL = re.compile(
    r"tool ([^\s{]+) "
)  # the assistant line `tool NAME {inputs}` of the same loop (one per message: agent_loop.py builds one)
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
AUDIT_CODES = (
    SPEND_REASONS
    | {
        CODE_GATE_REFUSED,  # what `_note` writes in place of a code that is not in this set (a bug guard)
        CODE_MASK_REFUSED,
        CODE_MASK_BUDGET,
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
        CODE_RESERVE_INTERRUPTED,
        CODE_HELD_LEFT,
        CODE_COST_UNKNOWN,
        CODE_SETTLE_FAILED,
        CODE_OVERSHOOT,
    }
)


def refused_before_response(exc: BaseException) -> bool:
    """Rule (b). True only for a ProviderError (a ProviderExhausted is one) that the adapter marked with the exact
    value `refused_before_response = True`. On a ProviderExhausted the mark means EVERY attempt the retry layer
    made was refused before any response, so nothing was billed (handover/core-c/requests/2-refused-before-response.md,
    "Update 13:2xZ"). An unmarked ProviderExhausted stays under rule (c). The gate CANNOT verify the mark: the
    adapter must set it on an exhausted error only when no attempt produced a response or may have been billed (a
    timeout after the request was sent is NOT a refusal). A non-ProviderError with the mark, a truthy value that
    is not True and a mark that raises on read are not honoured (a class-level mark on a ProviderExhausted subclass
    is honoured like an instance one). Only attempts rejected BEFORE processing count (a refused connection or DNS
    failure before the send, a 4xx on a request the provider did not process); a timeout, a 5xx or a 429 after
    processing may have been billed and must not be marked. A marked ProviderError after earlier retried attempts is the
    adapter's call: the gate reads only this exception, so the retry layer must not mark when an earlier attempt may
    have been billed. llm/retry.py sets no mark yet, so today this is
    False for every real error and every failed call keeps its worst case booked."""
    try:
        marked = getattr(exc, "refused_before_response", False) is True
    except Exception:  # noqa: BLE001  a property that raises is not a mark (the audit row must still be written)
        return False
    return marked and isinstance(exc, ProviderError)


def spend_reason(error: BaseException) -> str | None:
    """The published reason of a `SpendRefused`-shaped error, else None. Shaped: a class (or a base) named
    `SpendRefused` and a `.reason` that is one of SPEND_REASONS. Duck typing until `limits.SpendRefused` exists
    (then: isinstance). The attribute read is guarded: a property that raises is not a SpendRefused. Nothing of
    the error is returned but one of the fixed reasons."""
    try:
        reason = getattr(error, "reason", None)
        named = any(cls.__name__ == "SpendRefused" for cls in type(error).__mro__)
    except Exception:  # noqa: BLE001 - a hostile property
        return None
    return reason if named and isinstance(reason, str) and reason in SPEND_REASONS else None


# The largest decimal exponent (of the leading digit) and the smallest exponent an amount may have: a Decimal such as
# `1E+999999` is finite and not negative, and no money amount (design review round 3, N3).
MAX_AMOUNT_MAGNITUDE = 15  # `Decimal.adjusted()`: at most 10**16 USD
MIN_AMOUNT_EXPONENT = -64


def usable_amount(value: Any) -> bool:
    """A finite Decimal of 0 or more with a sane exponent: the only amount the gate reserves or settles with. A
    negative zero (`Decimal("-0")`), NaN, an infinity and an absurd exponent are not usable."""
    return (
        isinstance(value, Decimal)
        and value.is_finite()
        and not value.is_signed()
        and value.adjusted() <= MAX_AMOUNT_MAGNITUDE
        and value.as_tuple().exponent >= MIN_AMOUNT_EXPONENT
    )


def usable_cost(reply: Any) -> Decimal | None:
    """Rule (a): the reply's cost when it is a usable amount, else None. A `cost_usd` that raises on read is no
    cost (the call is paid: the row says `cost_unknown`, the reply is returned)."""
    try:
        cost = getattr(reply, "cost_usd", None)
    except Exception:  # noqa: BLE001 - a hostile property: no usable cost
        return None
    return cost if usable_amount(cost) else None


# END OF INTERFACE (ii)
# ======================================================================================================


MAX_FRAMING_TOKENS = (
    64  # framing tokens read per message; the rest of the text is enforced as plain text
)


def framing_tokens(content: str) -> list[re.Match[str]]:
    """The framing tokens of one message content, at most `MAX_FRAMING_TOKENS` (design review round 3, N5: one
    message of ten thousand forged tokens costs a bounded amount). What follows the last token read is plain text."""
    return list(itertools.islice(FRAMING.finditer(content), MAX_FRAMING_TOKENS))


def framing_free(
    messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, snap: runmap.MapSnapshot
) -> bool:
    """False when a value of a SECRET kind (swept in every copy: `snap.secret_values`) EQUALS a tool name (the
    `tools` list, an assistant line `tool NAME {...}`, a framing token) or a call id, or is a SUBSTRING of a name in
    the `tools` list (that list is forwarded untouched, so the name would show the value; code review round 3, M1). A
    piece of a call id, or of a name that is only in a message (not in `tools`), never refuses: that slot is enforced
    and no raw copy of it is forwarded (review round 3 asked to refuse a piece of a call id too: NOT done, the forged
    token `call_id=x_<secret>_y` of dz2-B1 is exactly such a case and is a hiding place no more, not a reason to stop). Values that the sweep never replaces, and values of an identifier kind (a host or tenant named `search`),
    never refuse a call: the slots are enforced instead. Returns a bool; the value is never returned or logged."""
    names: set[str] = set()
    for message in messages:
        content = message["content"]
        for token in framing_tokens(content):
            if token.group("id"):
                names.add(token.group("id"))
            if token.group("name"):
                names.add(token.group("name"))
        call = _ASSISTANT_CALL.match(content) if message.get("role") == "assistant" else None
        if call:
            names.add(call.group(1))
    listed = tool_names(tools)
    secrets = snap.secret_values
    if not (names | listed).isdisjoint(secrets):
        return False
    # a piece of a listed name: one joined string, one substring test per secret value
    shown = "\n".join(sorted(listed))
    return not any(value in shown for value in secrets)


def tool_names(tools: list[dict[str, Any]] | None) -> frozenset[str]:
    """The names in the call's `tools` list (a dict with a str `name`): operator text, forwarded as it is."""
    return frozenset(
        tool["name"]
        for tool in tools or ()
        if isinstance(tool, dict) and isinstance(tool.get("name"), str)
    )


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


class MaskBudgetExceeded(UnmaskedInput):
    """The enforce step ran out of its budget (a text or the map too large, too many steps, the time): this call
    only is refused, with its own code, so an operator can tell a size problem from a bad input."""

    code = CODE_MASK_BUDGET


class HeldValueLeft(UnmaskedInput):
    """Safety net: a value of a secret kind still stood raw after the sweeps (a value that spans a framing
    word, hides in a forged placeholder-shaped token, or a bug)."""

    code = CODE_HELD_LEFT


class WorstCaseInvalid(GateRefused):
    """`worst_case` returned something that is not a finite Decimal >= 0 (a float, None, NaN, a negative
    amount): nothing was reserved and no call was made. The gate does not trust the installer's function."""

    code = CODE_WORST_CASE_INVALID


class ReservationInvalid(GateRefused):
    """The meter's `reserve` returned something that is not a non-empty str: there is nothing to settle
    against, so no call was made. Whatever the meter booked stays booked until its sweep."""

    code = CODE_RESERVATION_INVALID


class FramingRefused(GateRefused):
    """A value of a secret kind equals a tool name or a call id."""

    code = CODE_FRAMING_REFUSED


class _NoMap:
    """The type of `NO_MAP`. One instance (`type(NO_MAP)()` returns it); it is not a mapping and holds nothing."""

    __slots__ = ()
    _one: Any = None

    def __new__(cls) -> Self:
        if cls._one is None:
            cls._one = super().__new__(cls)
        return cls._one

    def __repr__(self) -> str:
        return "NO_MAP"


# `bind(..., mapping=NO_MAP)` says, on purpose and in the call, that this call site has no run map: no enforce step
# runs and every audit row says `no_map`. Only the eval and replay command lines (which have no run) may use it.
NO_MAP = _NoMap()


class ModelGate:
    """Holds the client, the meter, the audit sink, the worst-case function and the enforce step. It has NO
    `chat`: a caller must `bind` it to an agent and a run first, so an unbound gate cannot call a model.
    A client that is itself a gate is refused (TypeError), so the direct case of one call reserved twice
    cannot be built; a gate hidden inside another wrapper is NOT detected.

    `enforce=` is a test-only hook (design review round 3, M4): production code leaves it at the default
    (`runmap.enforce_map`). Every audit row of a gate with another function says `enforce_custom`, and the install
    test (tests/test_gate_install_callers.py) refuses an `enforce=` argument anywhere in src. The gate cannot tell a
    production caller from a test, so it does not refuse the argument itself."""

    def __init__(
        self,
        llm: LLM,
        *,
        meter: Meter,
        audit: AuditSink | None,
        worst_case: WorstCase,
        enforce: Enforce = _DEFAULT_ENFORCE,
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
        mapping: runmap.RunMap | _NoMap,
        principal: str | None = None,
        source: str = DEFAULT_SOURCE,
    ) -> BoundGate:
        """A gate for one call site. `mapping` is REQUIRED (ORDER 017 item 1): the run's LIVE map, kept by
        reference and never written: every `chat` takes one copy of it (`runmap.snapshot`), so a value the run
        masks later is replaced in earlier text on the next call. The map has ONE writer at a time (the run's own
        thread, through `redact_text`); the gate may read it from another thread. A site with no run map says so
        with `mapping=NO_MAP` (the eval and replay command lines only): no enforce step runs and every audit row
        says `no_map` in its `decision` field. None, or anything that is not a `runmap.RunMap` (a plain dict, a copy
        made with `dict(run_map)` is a stale map that would still read `map_enforced`), is a TypeError: a forgotten
        or wrong map can no longer switch the guarantee off without a trace. A RunMap that is not the run's own, or
        a `RunMap(dict(run_map))` copy, cannot be told from the real one: the install tests (core-b) cover that. `principal` defaults to the agent
        id. The ids go into audit rows: one that is not a str is a TypeError here, not a row lost later."""
        if not isinstance(mapping, runmap.RunMap | _NoMap):
            raise TypeError("mapping must be the run's RunMap or NO_MAP")
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
        mapping: runmap.RunMap | _NoMap,
        principal: str,
        source: str,
    ) -> None:
        self._llm, self._meter, self._audit = gate._llm, gate._meter, gate._audit
        self._worst_case, self._enforce = gate._worst_case, gate._enforce
        self._agent_id, self._run_id, self._mapping = agent_id, run_id, mapping
        self._principal, self._source = principal, source
        self._mode = MODE_NO_MAP if isinstance(mapping, _NoMap) else None
        self._custom = gate._enforce is not _DEFAULT_ENFORCE
        self._built: dict[
            str, Any
        ] = {}  # built patterns kept between calls (`runmap.snapshot(cache=...)`)

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
        try:
            enforced = self._enforced(messages, documents, tools)
        except BaseException:  # KeyboardInterrupt in the enforce step: a row, then on as it is
            self._note(RESULT_FAILED, CODE_CALL_INTERRUPTED, decision=MODE_FAILED)
            raise
        if isinstance(enforced, str):  # a failure code: nothing was sent, nothing is reserved
            self._note(RESULT_REFUSED, enforced, decision=MODE_FAILED)
            if enforced == CODE_FRAMING_REFUSED:
                raise FramingRefused  # raised outside any `except`: no cause and no context to leak
            if enforced == CODE_HELD_LEFT:
                raise HeldValueLeft
            if enforced == CODE_MASK_BUDGET:
                raise MaskBudgetExceeded
            raise UnmaskedInput  # raised outside any `except`: no cause and no context to leak
        messages, documents, mode = enforced  # from here on only the enforced copies are used
        failure: str | None = None
        reserved, reservation = Decimal(0), ""
        try:
            reserved = self._worst_case(route, system, messages, tools, documents, output_schema)
        except Exception:  # noqa: BLE001 - its error is NOT passed on (it may carry text): a code instead
            failure = CODE_WORST_CASE_FAILED
        except (
            BaseException
        ):  # KeyboardInterrupt: a row, then on as it is (nothing is reserved yet)
            self._note(RESULT_FAILED, CODE_CALL_INTERRUPTED, decision=mode)
            raise
        if failure is None and not usable_amount(reserved):
            failure = CODE_WORST_CASE_INVALID
        if failure is None:
            try:
                reservation = self._meter.reserve(self._agent_id, reserved, run_id=self._run_id)
            except Exception as exc:
                reason = spend_reason(exc)
                if reason is not None:
                    self._note(RESULT_REFUSED, reason, decision=mode)
                    raise  # a SpendRefused passes unchanged
                failure = CODE_RESERVE_REFUSED  # a KeyError, a down store: a code, not the error
            except (
                BaseException
            ):  # the meter may have booked the amount already: the sweep closes it
                self._note(RESULT_FAILED, CODE_RESERVE_INTERRUPTED, decision=mode)
                raise
        try:
            if failure is None and not (isinstance(reservation, str) and reservation):
                failure = CODE_RESERVATION_INVALID
        except BaseException:  # between reserve and the call: the amount IS booked
            self._note(RESULT_FAILED, CODE_CALL_INTERRUPTED, reservation, mode)
            raise
        if failure is not None:  # no call; raised outside the handlers, so with no chain
            self._note(RESULT_REFUSED, failure, decision=mode)
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
                self._settle(reservation, Decimal(0), RESULT_FAILED, CODE_PROVIDER_REFUSED, mode)
            else:  # rule (c): the cost is unknown, the worst case stays booked
                exhausted = isinstance(exc, ProviderExhausted)
                code = CODE_PROVIDER_EXHAUSTED if exhausted else CODE_PROVIDER_ERROR
                self._note(RESULT_FAILED, code, reservation, mode)
            raise
        except Exception:  # rule (c): may have been billed (a reply that fails to parse, a timeout)
            self._note(RESULT_FAILED, CODE_CALL_FAILED, reservation, mode)
            raise
        except BaseException:  # rule (c): going down, cost unknown
            self._note(RESULT_FAILED, CODE_CALL_INTERRUPTED, reservation, mode)
            raise
        cost = usable_cost(reply)
        if (
            cost is None
        ):  # rule (c): the call is paid and its reply is returned; nothing to settle with
            self._note(RESULT_OK, CODE_COST_UNKNOWN, reservation, mode)
        else:  # rule (a)
            self._settle(reservation, cost, RESULT_OK, None, mode)
        return reply

    def _settle(
        self, reservation: str, usd: Decimal, result: str, code: str | None, decision: str | None
    ) -> None:
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
        self._note(result, code, reservation, decision)

    def _enforced(
        self,
        messages: list[dict[str, Any]],
        documents: list[bytes] | None,
        tools: list[dict[str, Any]] | None,
    ) -> tuple[list[dict[str, Any]], list[bytes] | None, str | None] | str:
        """(new messages, new documents, the audit `decision`) or a failure code (`mask_refused`,
        `mask_budget_exceeded`, `framing_refused`, `held_value_left`) when the step failed (then nothing is sent). A
        message or document in which nothing is replaced is passed on as the same object, so the bytes are the
        caller's; one with a replaced value is a new dict or new bytes. A content that is not `str` is refused with
        or without a map. Documents are read as the adapters read them (`llm/common.py` `turns`: UTF-8, bad bytes
        replaced, so a binary one is decoded lossily). The live map is copied ONCE here (`runmap.snapshot`): every
        text of this call is enforced against the same entries and shares one budget, and the patterns are built at
        most once per map change (kept in this bound gate). The fixed words of a tool-result token are never
        replaced (`_enforce_text`). Every enforced chunk is checked by the safety net (`runmap.held_value_left` and, G13, `runmap.held_in_views`)."""
        mapping = self._mapping
        try:
            if isinstance(mapping, _NoMap):
                mapping = None
            else:
                mapping = runmap.snapshot(mapping, self._built)
            if mapping is not None and not framing_free(messages, tools, mapping):
                return CODE_FRAMING_REFUSED
            listed = tool_names(tools)
            sent: list[dict[str, Any]] = []
            for message in messages:
                content = message["content"] if isinstance(message, dict) else None
                if not isinstance(content, str):
                    return CODE_MASK_REFUSED
                if mapping is not None:
                    fixed, code = self._enforce_text(content, mapping, message.get("role"), listed)
                    if code is not None:
                        return code
                    if fixed != content:
                        message = {**message, "content": fixed}
                sent.append(message)
            docs: list[bytes] | None = None
            if documents is not None:
                docs = []
                for document in documents:
                    if not isinstance(document, bytes):
                        return CODE_MASK_REFUSED
                    if mapping is not None:
                        text = document.decode("utf-8", "replace")
                        fixed, code = self._chunk(text, mapping)
                        if code is not None:
                            return code
                        if fixed != text:
                            document = fixed.encode("utf-8")
                    docs.append(document)
        except runmap.InputTooLarge:  # size, step or time budget: this call only
            return CODE_MASK_BUDGET
        except Exception:  # noqa: BLE001 - fail closed: a step that cannot finish means no call
            return CODE_MASK_REFUSED
        if mapping is None:
            mode = MODE_NO_MAP
        elif self._custom:
            mode = MODE_CUSTOM
        else:
            mode = MODE_ENFORCED if len(mapping) else MODE_EMPTY
        return sent, docs, mode

    def _chunk(self, text: str, mapping: Mapping[str, str]) -> tuple[str, str | None]:
        """(the enforced text, None) or ("", a failure code): one stretch enforced and then checked by the safety net
        (a value of a secret kind still raw in it; since G13 also a piece of one beside a key of the map and a secret value
        in a decoded form of the text: `runmap.held_value_left` and `runmap.held_in_views`)."""
        fixed = self._enforce(text, mapping)
        if not isinstance(fixed, str):
            return "", CODE_MASK_REFUSED
        if runmap.held_value_left(fixed, mapping) or runmap.held_in_views(fixed, mapping):
            return "", CODE_HELD_LEFT
        return fixed, None

    def _enforce_text(
        self,
        text: str,
        mapping: Mapping[str, str],
        role: Any = None,
        listed: frozenset[str] = frozenset(),
    ) -> tuple[str, str | None]:
        """Enforce the map on one message content: (the text, None) or ("", a failure code). The FIXED words of the
        agent loop's framing (`<<TOOL RESULT call_id=`, ` tool=`, `>>`, `<<END TOOL RESULT>>`, and the `tool ` of an
        assistant line `tool NAME {...}`) are kept exactly; the call id, the tool name and every stretch between
        them are enforced. A tool name that is in the call's `tools` list stays EXACT (that list is forwarded
        untouched and the model must see the same name in both places; a secret that equals or is part of such a name
        has refused the call already, `framing_free`). The assistant line and the token read alike. A text with no
        framing is enforced whole. At most `MAX_FRAMING_TOKENS` tokens are read; what follows is one plain stretch.
        A token that starts inside the name of the assistant line is not read as one (it would be copied twice)."""
        call = _ASSISTANT_CALL.match(text) if role == "assistant" else None
        tokens = framing_tokens(text)
        if not tokens and call is None:
            return self._chunk(text, mapping)
        parts: list[str] = []
        failure: list[str] = []
        end = 0

        def put(chunk: str, exact: bool = False) -> None:
            if not chunk or failure:
                return
            if exact:
                parts.append(chunk)
                return
            fixed, code = self._chunk(chunk, mapping)
            if code is not None:
                failure.append(code)
            parts.append(fixed)

        def slot(name: str) -> None:
            put(name, exact=name in listed)

        if call is not None:
            put("tool ", exact=True)
            slot(call.group(1))
            end = call.end(1)
        for token in tokens:
            # a token that starts inside what is already written (the assistant line's own name) is not read again
            if token.start() < end:
                continue
            put(text[end : token.start()])
            if token.group("end"):
                put(token.group("end"), exact=True)
            else:
                put(token.group("head"), exact=True)
                put(token.group("id"))
                put(token.group("mid"), exact=True)
                slot(token.group("name"))
                put(token.group("tail"), exact=True)
            end = token.end()
        put(text[end:])
        if failure:
            return "", failure[0]
        return "".join(parts), None

    def _note(
        self,
        result: str,
        error_code: str | None,
        reservation: str | None = None,
        decision: str | None = None,
    ) -> None:
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
                    decision=self._mode or decision,
                    result=result,
                    error_code=error_code,
                )
            )
