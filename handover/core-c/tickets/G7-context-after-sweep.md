# G7: context patterns run again after the sweep (ORDER 012, escalation E3)

Status: BUILT, not committed (builder, 2026-11-20). Evidence: evidence/G7-1.md.

## Problem
Line 1 `BSB: <bank code>`, line 2 `paid <same bank code>/<account>`. One `redact()` / `runmap.redact_text` pass gave
`paid <BANKCODE_1>/12345678`: the account stayed readable; a second pass masked it. Cause: the account pattern needs a
literal `<BANKCODE_n>` before the digits; on line 2 only the sweep writes it, after the pattern pass. `redact_many` had
the same gap (code in one string, account in another; measured).

## Patterns in the table that name a placeholder (step 1)
| Pattern | How it depends on a placeholder | After G7 |
|---|---|---|
| BANKACCT, account straight after its code (`<BANKCODE_\d+>` literal in the regex) | cannot match without it | FIXED: run again after the sweep |
| BANKACCT, account after an account keyword (regex names none; `_mask` asks `_bank_context`, whose `_BANK_CONTEXT` names `<BANKCODE_\d+>` within 100 chars) | counts only with context; a swept code is one form of it (measured: same gap) | FIXED: run again after the sweep |
| SECRET, cookie header (`(?!<[A-Z][A-Z0-9]*_\d+>(?:\s|$))`) | negative guard only: a swept placeholder can only stop a match, and the value would be the placeholder itself | NOT re-run, nothing to fix (measured: second pass changes nothing) |

No other entry of `PATTERNS` names a placeholder shape (pinned by `test_the_table_has_no_other_pattern_that_names_a_placeholder`).

RELATED, NOT FIXED, for the lead (found while listing; outside "names a placeholder"): patterns whose VALUE class admits
`<` `>` and has a minimum length gain a match once the sweep writes a placeholder inside a short token. Measured on
this code: `password=V` then `Bearer V+xy` (token under 12 chars) gives `Bearer <SECRET_1>xy` after one pass and
`Bearer <BEARER_1>` after two; same for `Basic V+ab` (under 8) and `authorization: V+ab` (under 8). What stays readable
after one pass is the short tail beside a masked value. A full fix is to run the whole table to a fixed point (about
twice the pattern cost), or to add BEARER, BASIC and the authorization pattern to `_CONTEXT_PATTERNS` with a mark of
`<` (three more pattern passes on almost every text). Not done: the order said the context patterns only.

## Design
`guard/redact.py` only; no regex changed; no public signature changed.
- `_CONTEXT_PATTERNS`: the two BANKACCT entries of `PATTERNS` (the same compiled objects). `_CONTEXT_MARK = "<BANKCODE_"`.
- `_Redactor.settle(texts)`: after the sweep, while some text holds the mark: run the context patterns over the swept
  texts; nothing changed -> done; the map grew -> sweep every text again (the new account's other copies); repeat.
- Called by `redact()` (when it sweeps) and by `redact_many()` (all strings as one batch).
- Bound: `_CONTEXT_ROUNDS = 4` rounds plus one check. One round does the work: a found account is swept as a BANKACCT
  placeholder, which no context pattern reads. A further round has work only if a sweep writes a NEW bank-code
  placeholder (the sweep does not revisit a value after a shorter neighbour is replaced: a planted adjacency per
  round). At the bound, if the check still finds a value: `ContextNotSettled` (a RuntimeError, message is its own name);
  `runmap._scan` turns it into `RedactionError("ContextNotSettled")`: nothing is sent, the run map is not written.
- Cost: a text with no `<BANKCODE_` pays one substring test. Otherwise each round is two linear pattern passes and at
  most one sweep (the existing linear sweep; a map rebuild only when the map grew). At most 5 rounds, so linear and
  inside the existing caps; runmap's size caps and time budget are untouched.

## Invariants
- One pass now gives exactly what two passes of the old path gave, for the context patterns (tested per shape).
- A second `redact()` / `redact_text` pass over the output changes neither text nor map for these shapes; `is_masked` is True.
- Text without a bank-code placeholder: byte-identical result and map to the old path.
- Never returns a text when the context patterns can still find a value (raise at the bound).
- `_sweep_copies=False` (find only) is unchanged.

## Tests
NEW tests/test_redact_context_after_sweep.py: 42 non-perf, 3 perf. One-pass (direct, keyword mirror, redact_many, run map
that already holds the code, redact_untrusted), idempotence, map kinds, 8 must-keep shapes, table guard, bound and
fail-closed, signatures, timing. Fail-before: 28 of 42 failed on the old code (evidence).
tests/test_runmap_is_masked.py: NOT edited by this builder. During the build its owner replaced both shape-B tests
(the strict xfail `test_shape_b_round_trip_holds_for_a_bank_code_beside_an_account` and the recording test
`test_shape_b_recorded_one_pass_leaves_the_account_number_and_a_second_pass_masks_it`) by one passing test,
`test_shape_b_one_pass_masks_the_account_beside_a_bank_code_and_is_a_fixed_point`. Before that replacement, with this
change in place, the first was XPASS(strict) and the second FAILED (old `once`: `paid <BANKCODE_1>/12345678`, new:
`paid <BANKCODE_1>/<BANKACCT_1>`); raw output in evidence. Final state of that file with this change: 29 passed, 1 xfailed
(the redact_untrusted round trip, kept).

## Second finding: `redact_untrusted` over its own output (caller table)
| Call site | Input | Can the input be output of redact_untrusted? |
|---|---|---|
| runtime/agent_loop.py:412 (document) | the trigger document, raw bytes | Not from this run. Only if the document itself quotes an earlier masked text (a ticket that pastes a previous report): outside content, escaped by design |
| tools.py:982 `redact_layered` <- tools.py:967 `prepare_output` <- tools.py:1198 (toolbox) and agent_loop.py:311 (plain tool) | the tool's raw return value | Normal result: no, unless the tool echoes its arguments: `restore_value` leaves secret-kind placeholders in the arguments, so an echo carries genuine `<SECRET_n>` back in (measured: `password=<SECRET_1>` echoed -> `password=<SECRET_2>`, map gains `<SECRET_2>` = the escaped token) |
| the same two sites, ERROR path: tools.py:1193 and agent_loop.py:309 `error_reason(exc)` then `prepare_output` | the exception message | YES, always. `error_reason` (tools.py:1005) runs `redact_bounded(message, {}, neutralise_untrusted)` with a throwaway map, then `prepare_output` runs `redact_untrusted` with the run map on that output. Measured: `login failed password=V host A` -> after error_reason `password=<SECRET_1> host <IPV4_1>` -> after prepare_output `password=<SECRET_2> host ‹IPV4_1›`, run map gains `<SECRET_2>` = `‹SECRET_1›` |
| k1b/redaction.py:188 `redact_bundle` <- k1b/replay.py:158 | every string of a case bundle read from disk | No: pass 1 and pass 2 both walk the ORIGINAL bundle (pass 1's output is dropped), and the masked bundle is cached per case, not re-masked. A bundle file that quotes masked text is outside content, as the document |
| evals.py:63 | golden case input file, fresh map | No (same outside-content note) |
| guard/judge.py:71, guard/bedrock_guardrail.py, runtime/evidence.py, approvals/channel.py, approvals/slack_channel.py | already redacted text | They use `redact_text` without the untrusted hook (judge, guardrail, evidence) or with the channel's own hook that keeps placeholders (channel): not this finding |
| demos/ | none of the three names occurs | No caller |

Verdict: ONE caller can and does: the tool-error path (both loops). No value leaks (the text is masked twice); the harm
is a junk secret entry in the run map (`<SECRET_n>` = `‹SECRET_1›`, swept as every-copy from later texts) and
`is_masked(..., neutralise_untrusted)` False for such output. The escape of the throwaway `<IPV4_1>` in the second
pass is REQUIRED (it is not the run map's `<IPV4_1>`), so the double pass cannot simply keep placeholders.

Fix, NOT APPLIED (it changes what a strict expected-failure test in a held file reports, and one option is in tools.py):
- (a) in `guard/redact.py` `_Redactor._mask`: a value that is nothing but ESCAPED look-alikes (`‹KIND_n›`) and genuine
  placeholders is left alone, as a value of genuine placeholders already is. About 4 lines. Tried as a monkeypatch,
  not in the file: the error path then gives `password=‹SECRET_1› host ‹IPV4_1›` with an empty run map, and
  `test_round_trip_of_redact_untrusted_with_the_same_hook_and_escaped_lookalikes` PASSES (so its strict xfail marker
  must go in the same change). Gives up: a real password spelled exactly `‹WORD_1›` is not masked.
- (b) in tools.py: `error_reason` returns the scrubbed message without its own pattern pass when the caller redacts
  next (both callers do). Removes the double pass at its source; does not help an echoing tool.
Recommended: (a), then (b) if the lead wants one pass on the error path.

## Stays out
No pattern regex, no pattern order, no change to `runmap.py`, `tools.py`, the sweep rule or the caps. BEARER / BASIC /
authorization length case (above). The second finding's fix.

## NOT CHECKED
- A text that really needs more than one round (the planted adjacency) was not constructed; the bound is tested by
  setting it to 0 and to 1.
- The whole test suite: only the files that mention `redact` (41 files + warden_port + the held runmap/gate files read-only).
- Timing on Windows or under load; timing through `runmap.redact_text` with views (only `redact()` measured).
- Whether any producer outside src/ and demos/ (a customer's tool wrapper) calls `redact_untrusted` twice.
- The two unrelated failures in the batch (test_k5_producers: `guard/model_gate.py` not registered; test_stage_names: a
  literal in tests/test_runmap_enforce_map.py) come from files other agents hold; not investigated further.
