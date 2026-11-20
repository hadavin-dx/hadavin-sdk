# FINDINGS: core-c's G7 redaction fix, property tests by core-a

Written 2026-11-20 by the findings writer of core-a. Test file: tests/test_redact_idempotence_property.py (core-a). Ticket: handover/core-c/tickets/G7-context-after-sweep.md; evidence evidence/G7-1.md (on origin/cloud/core-c).

## What was NOT run or checked (read first)
- The whole test suite: not run. Only our file (and stage-name, repo-rule, hard-coded-value tests in the checkout).
- After our final edit of the test file the run on main's redactor (G7 absent) was NOT repeated; only the checkout run (which has no G7) was: 238 passed, 1 skipped, 75 xfailed, same 75 as before.
- The corpus tests/fixtures/textnorm_corpus.json is not on our branch nor core-c's archive, so that corpus does not run (1 skip).
- Timing and the 6 s redaction budget: not measured. Core-c rewrote its G7 design at 06:23 UTC (commit 486498470), so ticket text and old evidence partly describe a design that is gone.
- Findings F3 and F4 were reduced by hand with one probe each (raw/G7-smallest-examples-on-core-c.log); other kinds of the same classes were not tried.
- No live model call; no network.

## What we ran against
- core-c commit 17f4534a4 (origin/cloud/core-c, 2026-11-20 06:36 UTC), scratch folder .../scratchpad/corec-g7b (import confirmed from the folder). The earlier run was on 93f7f24e4.
- core-c changed src/hadavin_sdk/guard/redact.py between the two (the first G7 with `_CONTEXT_PATTERNS`, rounds and `ContextNotSettled` was replaced by "the whole table once more, then one more sweep": `_Redactor.settle(originals, swept)`).

## Result lines
| Run | Tree | Result |
|---|---|---|
| raw/G7-property-on-main.log | main's redactor (no G7) | 86 passed, 1 skipped, 75 xfailed (those 75 are what G7 fixes) |
| raw/G7-property-on-core-c.log | core-c 93f7f24e4 | 144 passed, 18 xfailed |
| raw/G7-property-on-core-c-run2.log | core-c 17f4534a4, old test file | 37 failed (all strict XPASS), 116 passed, 9 xfailed. Reading: core-c fixed things, and our file's markers were stale |
| raw/G7-property-on-core-c-run3-corrected-test.log | 17f4534a4, test corrected once | 1 failed (our test called a helper core-c removed), 153 passed, 8 xfailed |
| raw/G7-property-on-core-c-run4-bankfuzz-only.log | 17f4534a4 | 3 passed (that helper test repaired) |
| raw/G7-property-on-core-c-run5-final-test.log | 17f4534a4, final test file | 154 passed, 8 xfailed |
| our checkout (no G7) | cloud/core-a | 238 passed, 1 skipped, 75 xfailed (with the stage-names, repo-rules, hard-coded-values files) |

## The 18 xfails of the first core-c run, grouped
| Finding | Count | Status on 17f4534a4 |
|---|---|---|
| G7-F1 (ticket's own RELATED, NOT FIXED): a short token after Bearer / Basic / authorization that starts with a known secret is masked whole only by a second pass | 3 | FIXED by core-c's new design (strict XPASS). Marker removed; assertion kept |
| G7-F2: an identifier (SSN, IPv4, email, MAC, phone, tenant id) glued to a copy of a known secret stays readable after one pass | 7 (glue fuzz, 5 kinds, tenant id) | FIXED (strict XPASS). Marker removed; assertion kept |
| G7-F3: a phone number directly followed by a full stop is not masked | 5 | STILL A FINDING |
| G7-F4: a secret in a look-alike spelling and again plainly in one text: one copy stays readable | 3 | STILL A FINDING |
Also 37 XPASS in run2 were not findings but a wrong assumption of our test: `HAS_G7` looked for `_CONTEXT_PATTERNS`, which core-c deleted, so tests that need G7 were wrongly expected to fail. Corrected to look for `_Redactor.settle`.

## Remaining findings, smallest example (values built from parts)
| id | smallest example | what the redactor does | what the invariant says | test id |
|---|---|---|---|---|
| G7-F3 | `"call " + "+1 415 555 " + "0142" + "."` | masks the number when nothing follows it or a comma follows (`call <PHONE_1>,`), leaves it readable when a full stop follows: `call +1 415 555 0142.` (the PHONE pattern ends with `(?![\w.])`, so a final full stop blocks the match) | P5 concatenation/context and the redactor's own privacy rule: a phone number at the end of a sentence is a phone number; whatever is found in A and in B alone is found in A then B | test_P5_a_phone_number_at_the_end_of_a_sentence_is_masked[call {}.] and three more forms; test_P5_whatever_is_found_in_a_and_in_b_alone_is_found_in_a_then_b['. '] |
| G7-F4 | `password=` + secret with its 6th character written as full-width letter U+FF58, then `, ` and the same secret plainly (secret = "Zq7" + "pLm2xQ9") | first spelling masked (`password=<SECRET_1> Zq7pLm2xQ9`), the plain copy stays readable; for the three-part token form the middle part stays readable after one pass | P6 look-alike spellings: every copy of a value that was found is masked in one pass (ticket: the sweep masks other copies) | test_P6_a_secret_written_in_a_look_alike_spelling_and_plainly_is_masked_in_both_places[password-then-comma], [token-in-three-parts]; test_P6_P1_generated_a_value_in_a_look_alike_spelling_and_again_plainly |
Note for F4: the comma after the first value disappears from the output (the mask swallowed `, `?): seen in the probe, not followed up.

## Which properties G7 fixed (fail on main's redactor, pass on core-c)
The 75 xfails on main that pass on core-c: bank code on one line then the account beside the code elsewhere (the ticket grid: 7 keywords x links x separators x layouts), account keyword whose only bank context is a swept code, bank fuzz (one pass equals two), second text of a run, and the own-output rule (untrusted redaction over its own output adds no map entry; typed-unknown-kind and zero-width cases). On 17f4534a4 additionally F1 and F2 above (not part of the ticket's claim, a side effect of running the whole table again).

## Properties the code does not claim and the tests do not assert
- A fixed point in general: the ticket says two pattern passes and two sweeps at most, not a loop. The ticket's own stated limits (a chain of three where a third pattern pass is needed; a longer credential found late whose other copies keep the tail readable) are NOT asserted either way here; the old design's "rounds bound / ContextNotSettled" test now only checks that nothing raises.
- Values the sweep leaves by rule: under 3 characters, all-digit under 6, common words (prod, admin), identifiers with a letter or digit touching them.
- A real credential spelled exactly like an escaped placeholder is not masked (ticket "Gives up").
- Timing and cost (ticket: about 2x for texts with matches).

## Our corrections to our own test file
1. `HAS_G7` now checks `_Redactor.settle` only (core-c removed `_CONTEXT_PATTERNS`).
2. The F1 and F2 strict xfail markers removed (core-c fixed them); those tests carry `needs_g7` instead, so on a redactor without G7 (our branch) they remain expected failures. No assertion changed.
3. The bank-fuzz test no longer calls the removed `_find_context`; it now runs the BANKACCT patterns directly on the output.
4. ruff check and ruff format clean.

## Update after the newest heads (core-c c511a71b9; run 2026-11-20, log raw/MAINT-core-c.log)
- G7-F3 (4 P5 phone ids, a phone number before a full stop) and G7-F4 (P5 ". " id, 3 P6 ids): STILL OPEN, 8 strict expected-failures unchanged. No marker removed.
- NOT a finding: 29 XPASS in test_P7_I6 (ids controls-around ... zero-width-in-values). The marker `needs_own_output_rule` read `hasattr(R, "_ESCAPED_LOOKALIKE")`; core-c replaced that name by `_OWN_OUTPUT` in ab6ff2f61 (G7 fix round 1), so the marker turned on although the rule is present. The detection is now `hasattr(R, "_OWN_OUTPUT") or hasattr(R, "_ESCAPED_LOOKALIKE")`. On our branch (neither name, no G7) the marker stays active and the 29 cases stay expected failures: green there too (checkout run: 86 passed, 455 skipped, 75 xfailed over the six files).
- Gate contract file (tests/contracts/test_model_gate_contract.py), not G7 but the same head: INTERFACE CHANGES decided by core-c in ORDER 017 and handover/core-c/requests/3-bind-mapping-required.md, adapted without weakening the meaning: (1) `bind` needs `mapping=`; "no map" is `NO_MAP` (a helper `_bind` passes NO_MAP where the old tests passed None or nothing); (2) every failure before the provider call that is not a SpendRefused is a code-only `GateRefused` (reserve errors: reserve_refused; a raising worst case or max_attempts <= 0: worst_case_failed; a worst case that is no finite Decimal >= 0: worst_case_invalid, refused by the gate before the meter, so the row code is worst_case_invalid, not bad_amount): the tests now assert the code, `args == (code,)`, no cause, no context, no inner call, nothing booked; SpendRefused and a BaseException still pass as the same object; (3) the source guards: `raise GateRefused(failure)` is allowed only if every assignment to `failure` is a CODE_ constant or None; a module-level `re.compile(...)` and the stateless `NO_MAP = _NoMap()` (`__slots__ = ()`) are allowed; every other raise and module-level call is still refused.
- Result on c511a71b9: 355 passed, 1 skipped (point 10: no worst-case formula), 8 xfailed. Before the update: 165 failed in the gate file, 29 XPASS in the redaction file.
