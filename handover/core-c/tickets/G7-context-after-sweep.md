# G7: one more pattern pass after the sweep (ORDERS 012 and 013, escalations E3 and E5)

Status: BUILT as ordered in ORDER 013 (builder, 2026-11-20); FIX ROUND 2 (ORDER 020 MJ-B and the G7 result review, same day) replaced the one extra pass by a
capped fixed-point loop: read "Design as built, round 2" first, the older sections describe round 1 and are kept as the record.
Evidence: evidence/G7-1.md (parts in order of work; "G7 fix round 2" is the last).
This text replaces the first design (context patterns only, bounded rounds): that design is GONE from the code.

## Design as built, ROUND 2 (supersedes "Design as built" below and the ORDER 013 one-pass wording)
`_Redactor.settle(originals, swept)` (guard/redact.py), called by `redact()` and `redact_many()`:
1. pattern pass 1 (`find`), sweep 1 (as before).
2. Round 1: the whole table runs again over each string that pass 1 or sweep 1 changed. If the map did NOT grow, done.
3. If the map grew: sweep every string again (the new value's other copies go). The strings THAT sweep changed (a placeholder now
   stands where a value stood) go through the table again: round 2, and so on, only over the strings the last sweep changed.
4. Hard cap `_SETTLE_ROUNDS = 4` rounds. A text the last sweep still changed after round 4 is not settled: `RedactionError("NotSettled")`
   (the type `redact_text` re-raises as RedactionError; nothing is shown). A refusal, never a silent leak.
5. Deadline: `settle` checks the call's deadline (the `_deadline` of `redact`, the same CPU clock as `REDACT_BUDGET_S`; new keyword
   `_deadline=None` on `redact_many`, callers unchanged) before every round and raises `InputTooLarge` when it is spent. A round is never skipped.
6. Cost: text that needs no more passes pays nothing extra (a clean text: 1 pass, 1 sweep; one planted secret: 2 passes, 1 sweep; the chain of
   three: 3 passes over the one text that changed). Measured 2026-11-20 (CPU s, best of 3): 100,000 chars of bank lines 0.395 (one pass 0.182,
   round 1 code 0.484 on the earlier machine run); 60,000 -> 240,000 chars 0.263 -> 1.023 (linear); hostile `password=` at the 262,144 cap with
   planted matches through `redact_untrusted` with views 1.9 s (round 1 code 1.7 s); `curl -u ` 4.0 s; all under the 6 s budget.
7. Compound tail (dz-2): when `_place` stores a compound SECRET entry whose written form held placeholders (`<SECRET_1>xy`), that spelling is
   registered; `sweep` replaces it as a literal on the unsplit text before the placeholder split. Other copies the first sweep had cut to
   `<SECRET_1>xy` no longer keep `xy`. A rolled-back entry (fold journal) is ignored (checked against the map).
Fixed by the loop: the chain of three (`password=V`, `BSB: <code>V`, `paid <code>/<account>`) and the compound tail (BEARER up to 7 characters,
BASIC / authorization / `"auth":` about 3, `sig=` up to 11). Both strict expected failures of round 1 are now ordinary passing tests.

## Limits that remain after round 2
- A chain that needs more than 4 rounds is REFUSED (RedactionError), not masked. No natural chain found needs more than 3 passes; the cap is tested by
  setting it to 1.
- Boundary class, fail safe (cb nit, pinned in tests/test_redact_settle_loop.py): a boundary pattern (SSN, PHONE, EMAIL, IBAN, UUID, IPV4, APIKEY) can
  match where pass 1 saw a word character and the sweep then left a placeholder: `password=hunter` then `ref hunter123-45-6789` gives
  `ref <SECRET_1><SSN_1>`. A fresh call on the second line alone would not mask the digits. More is masked, never less.
- The sweep's own rule for short or common values (under 3 characters; all-digit under 6; common words; an identifier where a letter or digit touches it) is unchanged.
- A secret that no pattern matches and no known value contains is not found (as before; the patterns are the control).
- The test generator and the reference loop cover the shapes listed in the evidence, not every chain.
- The deadline is checked between rounds, not inside a pass: one pass over a hostile text at the cap is not interruptible (about 4 s measured).
- Removed test: `test_the_patterns_that_name_a_placeholder_are_still_these_two` pinned the list of patterns that spell a placeholder (a record of step 1
  of ORDER 012); the design no longer depends on that list (the whole table runs), so the test could only block a harmless new pattern.

## For SECURITY wording (round 2; replaces the list at the end of this ticket where they differ)
- After the first pass and sweep the redactor runs the patterns again over the strings the sweep changed, to a fixed point, at most 4 rounds; a call that
  is still changing then is refused (RedactionError), never returned half masked. A text that needs nothing more pays nothing more.
- Each round is checked against the call's time budget (InputTooLarge past it); a pass in progress is not interrupted.
- A longer credential found only because a shorter known secret inside it was masked first is stored whole and its other copies are masked whole (no `tail`).
- Boundary class: a call may mask a little MORE than a fresh call on the same text would (digits glued to a swept word), never less.
- Unchanged: values and copies the sweep leaves by rule; escaped look-alikes are never credentials; a tool error text is redacted twice (see below).

## Problem (one root cause)
A pattern's result can change once placeholders stand in the text, and the sweep writes placeholders after every pattern ran.
- E3: `BSB: <code>` then `paid <same code>/<account>`: one pass gave `paid <BANKCODE_1>/12345678`; a second pass masked it.
- E5: `password=V` then `Bearer V+xy` (token under 12 chars): one pass gave `Bearer <SECRET_1>xy`; a second gave `<BEARER_1>`.
  The same for `Basic V+ab` (under 8) and `authorization: V+ab` (under 8).
- `redact_many` had the same gap across strings.

## Patterns that name a placeholder (step 1 of ORDER 012, kept as a record)
BANKACCT "account straight after its code" (literal `<BANKCODE_\d+>`); BANKACCT "account after a keyword" (through
`_bank_context`); SECRET cookie header (negative guard only). Beyond those, every value class that admits `<` `>` with a
minimum length (BEARER, BASIC, authorization, cookie forms, flags) can change after the sweep. Telling them apart is not
cheap AND certain, so the whole table runs again (ORDER 013 item 1).

## Design as built (`guard/redact.py` only; no regex changed; no public signature changed)
`_Redactor.settle(originals, swept)`, called by `redact()` (when it sweeps) and `redact_many()`:
1. pattern pass 1 (`find`), 2. sweep 1, 3. pattern pass 2: the WHOLE table once more over each swept string, 4. sweep 2,
only if pass 2 added a value to the map (every string of the call is swept, so the new value's other copies go too).
Exactly what runs how many times: pattern pass at most 2, sweep at most 2, per call. No loop, no round counter, no
second design stacked on it (`_CONTEXT_PATTERNS`, `_CONTEXT_ROUNDS`, `ContextNotSettled` were removed).
Skip, cheap and certain: a string that pass 1 and sweep 1 left unchanged is not scanned again (the same patterns over the
same text with the same state give the same result). A text with nothing to mask costs what it did.
Caps and budget: untouched (they live in runmap); both extra steps are the existing linear ones.

## Invariants
- At most 2 pattern passes and 2 sweeps per `redact()` / `redact_many()` call (tested by counting calls).
- For the E3 and E5 shapes one pass equals two passes of the old path; a second `redact_text` changes neither text nor map.
- A text with no match: one pattern pass, one sweep, byte-identical result.
- `_sweep_copies=False` (find only) unchanged.

## Property test (ORDER 013 item 2): tests/test_redact_idempotent_property.py
Through `runmap.redact_text` with one run map, per input: (a) a second pass changes neither text nor map; (b) no original of
the map stands raw in the output, by the redactor's own copy rule (`redact._sweep`: secret kinds of 4+ chars nowhere
outside a placeholder; other kinds nowhere as their own token; values the rule never sweeps are not checked).
Inputs: 1,835, none dropped (counts pinned by a test):
| Corpus | Source | Inputs |
|---|---|---|
| privacy | tests/warden_port/privacy_corpus.py MASKED + KEPT | 48 + 14 |
| bank | tests/warden_port/test_redaction_bank.py POSITIVE, NEGATIVE, PINNED | 61 + 16 + 18 |
| review2 | tests/warden_port/test_redaction_review2.py LEAKS, FALSE_POSITIVES | 19 + 5 |
| cookies | tests/warden_port/test_redaction_review9.py COOKIES | 16 |
| own-shapes | tests/warden_port/test_redaction.py OWN_SHAPES | 8 |
| spellings | tests/test_k5_round8.py SPELLINGS (the layered spellings rounds 8 and 9 drive) | 3 |
| round12-fuzz | tests/test_k5_round12_fuzz.py `_case`, its seed | 1,200 |
| round-trip | tests/test_runmap_is_masked.py `_random_text` (its seed) + LOOKALIKES | 300 + 6 |
| p1c | handover/core-c/evidence/p1c_probe.py gap1_values, gap2_cases, gap3_cases | 16 + 44 + 43 |
| g7 | tests/test_redact_context_after_sweep.py SHAPES, MUST_KEEP, E5 | 6 + 8 + 3 |
| constructed | built for this file to find what one extra pass misses | 1 |
Not used (not redactor inputs): tests/demo_askdata/fuzzgen.py (SQL), tests/test_peel_run_id.py HOSTILE (run ids),
tests/fixtures/textnorm_corpus.json (name pairs for the fold).
Result: 1,834 pass, 0 refused, 1 strict expected failure. With the extra pass switched off: 8 more fail (5 g7 shapes,
3 g7 E5). HONEST NOTE: no input of the OLDER corpora fails with or without the extra pass; they did not hold this class.

## Strict expected failures = stated limits
1. `constructed:0`, a chain of three: `password=V`, `BSB: <code>V` (code glued to the secret), `paid <code>/<account>`.
   Pass 1 finds V; sweep 1 frees the code; pass 2 finds the code; sweep 2 writes its placeholder before the account; only a
   THIRD pattern pass reads the account. One pass leaves the account readable. Needs planted text.
2. `test_limit_the_tail_of_a_compound_value_found_late_is_not_swept_from_its_other_copies`: `password=V`, `Bearer V+tail`,
   `note V+tail+more`. Pass 2 stores V+tail whole; in the third line sweep 1 already replaced V, so no whole copy is left
   to sweep and `tail` stays readable there (5 characters in the test). Property (a)/(b) cannot see it.

## Cost of the extra pass (measured, CPU seconds, best of 3)
| Text | before G7 (one pass) | narrow design (context patterns) | as built (whole table again) |
|---|---|---|---|
| 100,000 chars, 40 bank codes, ~2,900 accounts | 0.206 | 0.263 | 0.484 |
| 60,000 -> 240,000 chars of the same | - | 0.158 -> 0.640 | 0.283 -> 1.128 (4.0x for 4x: linear) |
| 320,013 chars of code placeholders, no account | 0.699 | 0.716 | 1.434 |
A text with matches costs about 2.0x to 2.4x the old pass; a text with no match costs 1.0x (skip). All 25 perf-marked
redactor tests pass on try 1 of 3 (22 existing + 3 new; serial, 70 s; slowest: the per-pattern super-linear sweep 33 s).

## Tests
- tests/test_redact_context_after_sweep.py (49 non-perf, 3 perf): E3 shapes, redact_many, E5 for BEARER/BASIC/authorization
  (each asserts the old path's result too: `...<SECRET_1>xy`), must-keep, call counts, timing.
- tests/test_redact_idempotent_property.py (1,835 params + 3 tests).
- tests/test_redact_own_output.py (23).
- Fail-before: E3 28 of 42 on the old code; E5 recorded on the old code as `Bearer <SECRET_1>xy` / `Basic <SECRET_1>ab` /
  `authorization: <SECRET_1>ab` (evidence), and the property run with the extra pass off (8 fail).
- No existing test changed outcome in this step (batch: 1 failed, unrelated; 9,663 passed).
- tests/test_runmap_is_masked.py: only my one marker edit (follow-up); its owner rewrote the two recording tests.

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

Verdict: ONE caller can and does: the tool-error path (both loops); an echoing tool does the same. FIXED in the
follow-up (coordinator order after ORDER 012 item 2), in `guard/redact.py` `_Redactor._mask` only:
- Rule: a value that is nothing but ESCAPED look-alikes (`_ESCAPED_LOOKALIKE`: U+2039, letters/digits, `_`, ASCII digits,
  U+203A, exactly what `runmap.escape_placeholders` writes) and genuine placeholders, with nothing else but spaces, `;`
  and `,`, is left alone, as a value of genuine placeholders alone already was. No map entry is made.
- Result (through `tools.error_reason` then `tools.prepare_output`): `password=‹SECRET_1› host ‹IPV4_1›`, run map
  unchanged; `is_masked(out, map, neutralise_untrusted)` True; `redact_untrusted` of that output returns it unchanged.
- The escape of the throwaway `<IPV4_1>` in the second pass is REQUIRED and untouched (it is not the run map's).
- Security, each tested (tests/test_redact_own_output.py, 23 tests): a look-alike PLUS anything else (a secret after,
  before or between, one letter, one digit, non-ASCII letters, punctuation only, a dot between two look-alikes) is masked
  whole as before; a secret beside a look-alike as its own value is masked; only the exact escaped shape qualifies
  (no number, no kind, not closed, a secret inside the brackets: all masked); an escaped token gets no map entry, so
  `restore_text` / `restore` return it as typed and `has_placeholder` is False; a typed genuine placeholder in untrusted
  text is still escaped.
- Gives up: a real credential spelled exactly `‹WORD_1›` is not masked (as a credential spelled `<nil>` is not).
- Fail-before: 8 of the first 20 tests failed on the code before the rule (evidence).
- tests/test_runmap_is_masked.py: the strict xfail marker of `test_round_trip_of_redact_untrusted_with_the_same_hook_and_escaped_lookalikes`
  removed (one exact-string edit, nothing else); it passes.
- CHANGED OUTCOME, NOT EDITED (held file): `tests/test_runmap_is_masked.py::test_recorded_the_untrusted_hook_on_already_redacted_text_escapes_its_real_placeholders`
  now FAILS: it records the old behaviour. Old: `is_masked(out, mapping, neutralise_untrusted) is False` and
  `again == "password=<SECRET_2> at ‹IPV4_1›"`; new: `True` and `"password=‹SECRET_1› at ‹IPV4_1›"`. Its owner must
  rewrite or remove it.
- Still open, tools.py (not mine): `error_reason` redacting before `prepare_output` is a double pattern pass; harmless now.

## Stays out
No pattern regex, no pattern order, no change to `runmap.py`, `tools.py`, the sweep rule or the caps.

## NOT CHECKED
- The whole test suite: only files that mention `redact` (plus warden_port and the held runmap/gate files, read-only).
- Timing on Windows or under load; the 6 s `REDACT_BUDGET_S` against a worst-case text WITH matches at the cap through
  `redact_text` with views (each view is now up to two pattern passes); the existing end-to-end perf tests pass.
- A search for further chain shapes beyond the two limits above was by hand (5 shapes tried), not exhaustive.
- The unrelated red test (test_k5_producers: `guard/model_gate.py` not registered) belongs to another agent.

## For SECURITY wording
- Redaction is two pattern passes and two sweeps at most, not a fixed point: a value that needs a THIRD pass stays
  readable after one call. Known shape: a chain where a value found only by the second pass is the context of another
  (a bank code glued to a secret, then the account after that code elsewhere). Text must be planted to hit it.
- When a longer credential is found only because a shorter known secret inside it was masked first, its other copies
  elsewhere keep the part after the shorter secret readable (`<SECRET_1>tail`).
- A value made only of escaped placeholder look-alikes (`‹KIND_n›`) is never treated as a credential.
- Copies the sweep leaves by rule, unchanged by G7: values under 3 characters; all-digit values under 6; common words
  (`prod`, `admin`, ...); a non-secret identifier where a letter or digit touches it.
- A tool error text is redacted twice (throwaway map, then run map): its placeholders reach the model escaped, not numbered
  in the run's map.
