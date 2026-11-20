# G7: the table again after the sweep, to a capped fixed point (ORDERS 012 and 013, escalations E3 and E5)

Status: BUILT as ordered in ORDER 013 (one extra pass); FIX ROUND 2 (ORDER 020 MJ-B) replaced it by a capped fixed-point loop; FIX ROUND 3 (G7 result
review 2, fresh reviewers, 2026-11-20) made it a real fixed point and fixed what the review found. READ "Design as built, ROUND 3" FIRST. Every section
marked ROUND 1 or ROUND 2 below is the record of an earlier design and is not the code.
Evidence: evidence/G7-1.md (parts in order of work; "G7 fix round 3" is the last). Review: tickets/G7-result-review-2.md.
The first design (context patterns only, bounded rounds) is GONE from the code.

## Design as built, ROUND 3 (supersedes every other design section of this ticket)
`_Redactor.settle(originals, swept)` (guard/redact.py), called by `redact()` and `redact_many()` after pattern pass 1 (`find`) and sweep 1:
1. `todo` = the strings that pass 1 or sweep 1 changed.
2. A ROUND: check the call's deadline; the whole table over every string of `todo`; if that found a NEW value (the map grew) sweep EVERY string
   (the value's other copies go), else sweep only the strings the table changed (a placeholder written beside text can complete a spelled form).
   The next `todo` is the UNION of the strings the table changed and the strings the sweep changed in that round (round 2 had only the sweep's: a
   string the table rewrote and the sweep left alone was never read again, and the loop ended on "the map did not grow", not on "no text changed").
3. The loop ENDS on the first round that changes no text (no map growth is possible then). It is a fixed point of "table, then sweep" over the call's
   strings, not "the map stopped growing".
4. ACCEPTANCE RULE, exactly: the call is settled when some round r, 1 <= r <= `_SETTLE_ROUNDS` (4), changes no text. A chain whose last change is made
   in round 3 is accepted (round 4 confirms). A chain that still changes a text in round 4 is REFUSED: `RedactionError("NotSettled")`, nothing shown,
   because no round has read that text since. (Round 2 coded "a fourth growing round is accepted if its sweep changes nothing"; that is gone.)
5. The cap is a FAIL-CLOSED MARGIN, not a derived bound. Measured depth (tests/test_redact_settle_loop.py; evidence G7-1.md, round 3): over 8,000
   generated compositions of 4 to 8 lines (half from a pre-seeded run map; the test's own generator, seed 20261121) the rounds run were: 1 round 604,
   2 rounds 6,879, 3 rounds 517, none more (a second seed, 99: 567 / 6,925 / 508). The maximum, 3, is pinned in the test (`MAX_ROUNDS_SEEN`). The reference
   loop (every string re-read every pass) needed a third pass for 12%, a fourth for 3.7% and a fifth for 0.2% of the same inputs (the test asserts the
   fourth is reached: > 0). The real chain of three takes 3 rounds (two that change, one that confirms). No
   natural chain of 4 rounds was found (generated, a 20,000-input random search over 21 bank/secret lines, hand search), so the cap stays at 4 (one round
   of headroom); the tests for exactly 4 rounds (settled) and 5 rounds (refused) use a pass that changes its text for exactly that many rounds (a stub of
   `find` only; the real cap, never patched): an off-by-one in the loop (3 or 5 rounds) fails them. A chain planted on purpose that needs 5 rounds
   forces a refusal: a whole document or tool result is lost (availability), never a leak. That is the stated price of the margin.
6. Callers on `NotSettled`: it is a `RedactionError` and every caller already treats that as "nothing is shown". `runmap.redact_text` now re-raises a
   RedactionError as it is, so the text `NotSettled` reaches the caller's log (before: `RedactionError("RedactionError")`). The DOCUMENT path
   (agent_loop, the trigger document) abstains as "redaction failed", not as "too large"; a tool result is refused with the same reason as any
   redaction failure; a deadline `InputTooLarge` is a different subclass and keeps its own reason. A document planted to need 5 rounds therefore
   makes the run abstain: that is the intended fail-closed behaviour.
7. Deadline: `settle` checks the call's deadline before every round, and passes it into every sweep of a round and (through them) into `_build`
   (`InputTooLarge`, never a skipped pass). The deadline is `time.thread_time()` based (CPU time of the creating thread) and valid only in that
   thread. HONEST BOUND: budget + ONE UNINTERRUPTIBLE UNIT, per `redact()` call, where the unit is one pattern pass over the biggest string (or one
   `str.replace` / finder pass over one segment). Measured on the Linux test machine (one pass + one sweep of the text at the cap): 0.4 s for `password=`
   repeated, 1.9 s for `curl -u ` repeated (7.2 s end to end for `curl -u ` on the earlier Windows laptop, so its unit is larger). It is CPU time, not a
   wall bound (GIL waits and blocked time do not advance it): a caller that needs a wall-clock bound adds its own guard. The gate (`runmap.enforce_map`)
   converts its monotonic deadline to this clock in its own lane. T4 asserts the claim: at the cap with a planted chain of three, redacted under the real
   budget and REFUSED under a budget of 0.5 s, each within budget + twice the measured unit + 0.5 s.
8. Compound tail (dz-2, round 3 M3/M4): when `_place` stores a compound SECRET entry whose written form held placeholders (`<SECRET_1>xy`), that
   form is registered under the FIRST placeholder token it contains, with (placeholder, full value) at the end of a character trie. `sweep` looks the
   placeholder tokens of the text up and walks the trie: linear in the text, not entries x text (the old loop searched every form in the whole text on
   every sweep: 5,000 forms in 250,000 characters 0.17 s per sweep, up to 5 sweeps per call; now 0.002 s). An entry whose placeholder no longer maps to
   its full value (a rolled-back line, or the number reissued to another value) is ignored when read, so a ghost never writes a wrong placeholder that
   would restore to the wrong value (round 3 M3). Label change, noted (design N3): honest text spelled like a swept compound (`<SECRET_1>xy`) is
   relabelled with the compound's placeholder; the restore round trip is exact, only the label differs.
9. Cost (measured, evidence G7-1.md round 3): a clean text 1 pass 1 sweep; one planted secret 2 passes 1 sweep (unchanged); the chain of three 4 passes
   (one more than round 2: the confirming round over the one string it changed) and 3 sweeps. A string that the table rewrote in the last changing
   round is read once more: that is the price of ending on "no text changed". Texts that need no more passes pay nothing extra.
Fixed by the loop: the chain of three (`password=V`, `BSB: <code>V`, `paid <code>/<account>`) and the compound tail (BEARER up to 7 characters, BASIC /
authorization / `"auth":` about 3, `sig=` up to 11).

## Limits that remain after round 3
- A chain that needs a changing round 4 (5 rounds with the confirming one) is REFUSED, not masked. No natural chain found needs more than 3 rounds.
- NOT REPRODUCED (round 3 M1): a concrete string that round 2 left readable because it ended on map growth. 6,000 + 8,000 + 4,000 generated and
  corpus-mixed compositions gave identical results on the round 2 and round 3 loops, and a fixed-point check of every output (`sweep(find(t)) == t`) was
  clean on both. The union rule is kept as the safety net, and tested with a pass that rewrites a text without growing the map (the stub fails on the round 2 loop).
- Boundary class, fail safe (pinned in tests/test_redact_settle_loop.py): a boundary pattern (SSN, PHONE, EMAIL, IBAN, UUID, IPV4, APIKEY) can match where
  pass 1 saw a word character and the sweep then left a placeholder: `password=hunter` then `ref hunter123-45-6789` gives `ref <SECRET_1><SSN_1>`.
  More is masked, never less.
- Compounds inside compounds: a secret that contains a known compound plus more (`V+xq` known, then a `sig=` value `V+xq+xxqv` under 16 characters after the
  sweep) keeps the part after the known compound readable (the generator avoids it by giving every tail a different first letter). Planted text only.
- The sweep's own rule for short or common values (under 3 characters; all-digit under 6; common words; an identifier where a letter or digit touches it) is unchanged.
- A secret that no pattern matches and no known value contains is not found (the patterns are the control).
- The time bound is budget + one uninterruptible unit, CPU time of one thread (item 7).
- The test generator and the reference loop cover the shapes listed in the evidence, not every chain. The reference shares `find` and `sweep` with the code.

## Guards that replaced the deleted test (round 3 M7, N2)
Round 2 deleted `test_the_patterns_that_name_a_placeholder_are_still_these_two`. It guarded something real: the fold scan (`_mask_in_place`)
takes a full round for the labels in `_CONTEXT_LABELS` (`{"BANKACCT", "BANKCODE"}`). Now in tests/test_redact_context_after_sweep.py:
(a) every pattern whose regex source reads a placeholder shape is known (`BANKACCT`, and `SECRET` as a negative guard only) and the non-guard ones are in
`_CONTEXT_LABELS`; (b) `_decide` does not read the map (source check and the same decisions with an empty and a full map): the loop assumes a pattern
pass is a function of the text; (c) `_PLACEHOLDER`, `kind_of` and the `<BANKCODE_n>` reader agree with what `_place` writes, for every label.

## For SECURITY wording (round 3; replaces the lists below where they differ)
- After the first pass and sweep the redactor runs the patterns again over the strings that changed, round after round until a round changes no text, at
  most 4 rounds; a call that is still changing in round 4 is refused (RedactionError "NotSettled"), never returned half masked. A text that needs nothing
  more pays nothing more.
- Each round, each sweep of a round and the build of the sweep rules are checked against the call's time budget (InputTooLarge past it; CPU time of the
  calling thread, not wall time). A pattern pass in progress is not interrupted: the bound is the budget plus one pass.
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

## ROUND 1 design, SUPERSEDED (kept as the record; the code is the round 3 design above)
(`guard/redact.py` only; no regex changed; no public signature changed)
`_Redactor.settle(originals, swept)`, called by `redact()` (when it sweeps) and `redact_many()`:
1. pattern pass 1 (`find`), 2. sweep 1, 3. pattern pass 2: the WHOLE table once more over each swept string, 4. sweep 2,
only if pass 2 added a value to the map (every string of the call is swept, so the new value's other copies go too).
Round 1 ran a pattern pass at most 2 times and a sweep at most 2 times per call, no loop (that is NOT the code: see ROUND 3). (`_CONTEXT_PATTERNS`, `_CONTEXT_ROUNDS`, `ContextNotSettled` were removed).
Skip, cheap and certain: a string that pass 1 and sweep 1 left unchanged is not scanned again (the same patterns over the
same text with the same state give the same result). A text with nothing to mask costs what it did.
Caps and budget: untouched (they live in runmap); both extra steps are the existing linear ones.

## Invariants (ROUND 3; the round 1 list, "at most 2 passes", is gone)
- A call is settled on the first round (1 to 4) that changes no text, else refused (RedactionError "NotSettled"); asserted by counting rounds.
- A clean text: 1 pattern pass, 1 sweep, byte-identical result. One planted secret: 2 passes, 1 sweep. The chain of three: 4 passes, 3 sweeps.
- For the E3 and E5 shapes one call equals two calls of the old path; a second `redact_text` changes neither text nor map (property test).
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
Result (round 3, measured): 1,835 pass, 0 refused, 0 fail. With settle switched off 9 fail (5 g7 shapes, 3 g7 E5, `constructed:0`); with ONE extra pass only `constructed:0` fails. HONEST NOTE: no input of the OLDER corpora fails with or without the extra pass; they did not hold this class.

## Former strict expected failures (round 1; both are ordinary passing tests since round 2)
1. `constructed:0`, the chain of three: `password=V`, `BSB: <code>V`, `paid <code>/<account>`: masked in one call by the loop (3 rounds).
2. The compound tail (`password=V`, `Bearer V+tail`, `note V+tail+more`): masked by the spelled-form sweep (`note <BEARER_1>vw end`).

## ROUND 1 cost of the extra pass (measured, CPU seconds, best of 3; the round 3 numbers are in evidence G7-1.md)
| Text | before G7 (one pass) | narrow design (context patterns) | as built (whole table again) |
|---|---|---|---|
| 100,000 chars, 40 bank codes, ~2,900 accounts | 0.206 | 0.263 | 0.484 |
| 60,000 -> 240,000 chars of the same | - | 0.158 -> 0.640 | 0.283 -> 1.128 (4.0x for 4x: linear) |
| 320,013 chars of code placeholders, no account | 0.699 | 0.716 | 1.434 |
A text with matches costs about 2.0x to 2.4x the old pass; a text with no match costs 1.0x (skip). All 25 perf-marked
redactor tests pass on try 1 of 3 (22 existing + 3 new; serial, 70 s; slowest: the per-pattern super-linear sweep 33 s).

## Tests (ROUND 3 counts; collect-only numbers are in evidence G7-1.md)
- tests/test_redact_settle_loop.py: the cap at its real value (hop chains of 1 to 4 rounds settled, 5 refused, no monkeypatch of the cap; NotSettled text
  asserted through `redact_text`), the real chain of three (3 rounds), the fixed-point and union tests, the rolled-back and reissued spelled forms, the
  5,000-form scan at the size cap (ratio test), deadline tests (value loop with a stepping clock, `_build`, settle passes the deadline), the generator of
  4 to 8 lines with a pre-seeded map against the reference loop plus the depth distribution, T4 with budget 6.0 and 0.5.
- tests/test_redact_context_after_sweep.py: E3 shapes, redact_many, E5, must-keep, call counts, timing, and the three guards of "Guards that replaced the
  deleted test".
- tests/test_redact_idempotent_property.py: 1,835 params + 5 tests.
- tests/test_redact_own_output.py (23).
- Fail-before (round 3, new files on the round 2 redact.py and runmap.py swapped in for a few seconds): 14 of the new tests failed; the ones that fail
  for the reason of a finding: the hop chains (the loop ended on map growth), the union test, the reissue ghost, the 5,000-form ratio, the `_build` deadline,
  the settle deadline, the NotSettled text. The three guards (M7) and the generator pass on the old code too: they guard what the design relies on.

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
No pattern regex, no pattern order, no change to `tools.py`, the sweep rule or the caps. `runmap.py`: only `redact_text` re-raises a RedactionError as it is (round 3 N8); `enforce_map`, `snapshot` and `EnforceBudget` are another lane.

## NOT CHECKED (ROUND 3)
- The whole test suite: only the files named in evidence G7-1.md (redact, runmap, stage names, hard-coded values).
- A natural chain of 4 rounds: none found (generated, random search, by hand); the 4 and 5 round tests use a stub pass.
- Timing on Windows or under load. The wall-clock behaviour of the budget (it is CPU time of one thread).
- The gate's conversion of its monotonic deadline to the `thread_time` clock (another agent's lane, `runmap.enforce_map`).
- tools.py `error_reason` redacting before `prepare_output` (a double pass, harmless; not mine).

## For SECURITY wording (ROUND 3, END)
See "For SECURITY wording (round 3...)" near the top: it is the list. Older lists ("two passes at most, not a fixed point", "a THIRD pattern pass leaves
the account readable", "`tail` stays readable") were round 1 and are false for the code.
- Also unchanged since the follow-up: a value made only of escaped placeholder look-alikes (`‹KIND_n›`) is never treated as a credential; a tool error
  text is redacted twice (throwaway map, then run map): its placeholders reach the model escaped, not numbered in the run's map.
- Copies the sweep leaves by rule: values under 3 characters; all-digit values under 6; common words (`prod`, `admin`, ...); a non-secret identifier where a
  letter or digit touches it.
