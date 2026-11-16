Status: resolved

# Goldfish Annotated Review Report (PR H, round b3)

**Target:** branch `core/prh-strip-hidden-controls`, head `e852b577` (snapshot `/home/user/build/snap/prhb3-e852b577`; delta base `f09c6825`). Hidden-control stripping is a redaction/security path: no round cap. No person was available: recommended option for every item. Reviews: `/home/user/build/reports/prhb3-design.md` (2 Blocker, Nits) and `prhb3-codebase.md` (1 Blocker, 4 Major, 2 Nit); both read-only, hand traces only.
**Evidence:** none independent for this head. Only the builder's own evidence exists (`handover/evidence/PRH/b3/`). The independent evidence run is deliberately deferred to the fixed head (load above 4); the full suite was not rerun at this head even by the builder after a docs-only commit. Nothing here is verified by a run.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` B1, `codebase` B1] - Severity: Blocker
*   **Affected Scope:** `src/hadavin_sdk/guard/runmap.py:452-475` (`_swallowed_pieces`), `:478-500` (`_char_reading_wins`, rules 1 and 4 at `:492`, `:499`), `:750-757`, `:796-802`.
*   **Discrepancy Description:** the consuming reading (the `tput sgr0` fix) is passed through a gate written for the longer character reading. It is shorter, so after the cut every later character counts as "swallowed", the tail 5-grams enter `pieces`, rule 4 rejects it; a tail over 20,000 characters gives `pieces=None` and rule 1 rejects it; any other value masked in pass 1 also fails rule 1 (placeholder not in the caller's map). The key stays readable whenever text follows it or a second value was masked. T5 rows t_L9/r7c_M4a/M4b have the cut key alone; mutant 44 is killed only by them.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** two independent reviewers reached the same trace. It breaks the promise in CHANGELOG line 6 and `hidden.py:275-279`. Not a regression against main (main did not mask these either), but a shipped claim that is false.
*   ***Proposed Edit:*** First reproduce by running `redact_untrusted` on `"id " + AKIA + ESC + "(B" + ESC + "[m" + IOSFODNN7EXAMPLE + " and more text"` (and with an email before it); show the failing output. Then give the consuming reading its own acceptance rule (accept when it finds a value the joined reading did not; merge masks as `again_map != current` does for ordinary views), no `_swallowed_pieces`/rule 4 for it. Rows: trailing text, leading text, following line, a second masked value, tail over 20,000 characters, in t_L9 and a contract case. Mutants for `_swallowed_pieces`, `_char_reading_wins`; pin mutant 44 to a specific row with a tail.

### [Issue 2] [`design` B2] - Severity: Blocker
*   **Affected Scope:** `src/hadavin_sdk/tools.py:904-941` (`_scrub`: `hidden.strip` at 914, `strip_characters` at 921; `strip_consuming` unused).
*   **Discrepancy Description:** a handed-out tool secret (exact string, no pattern) cut by `ESC ( B ESC [ m` keeps `(B` in both readings used there, so it is not masked; `prepare_output` and `error_reason` can return it. No T5 row cuts the handed secret with `ESC(B`. Whether main removed `ESC(B` whole there (a regression) was not checked.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** least-privilege/redaction path; exact-string secrets have no later choke point.
*   ***Proposed Edit:*** Reproduce first. Add `hidden.strip_consuming(raw)` as one more search reading in `_scrub` (same shape as the `chars` branch at 921-925). Rows for a handed secret cut by `ESC(B ESC[m` in tool output, error text and URL position. Compare with main and say plainly whether it is a regression.

### [Issue 3] [`design` D-029 judgement] - Severity: Major
*   **Affected Scope:** `runmap.py:753` (consuming reading built from `text` only); decoded views (`%1B%28B`, `\u001b(B`); `tools.py:729` `undo(strip_hidden=True)`.
*   **Discrepancy Description:** the two-reading idea is sound but only works if every searcher uses both; the consuming reading is not applied to decoded views, so an encoded cut combined with `ESC(B` can need a reading that does not exist.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** same class as Issues 1 and 2; fix at the choke point, not per site.
*   ***Proposed Edit:*** One shared helper that returns all readings (joined, spaced, characters, consuming) for any text; `redact_text` views and `_scrub` both call it, and decoded views get the same set. Rows: encoded (`%1B%28B`, `\u001b(B`, entity) cut plus `ESC(B`. If a combination cannot be covered, refuse (`InputTooLarge`-style) rather than leave it; state which.

### [Issue 4] [`codebase` M2, `design` pass-bound Nit] - Severity: Major
*   **Affected Scope:** `runmap.py:676-679`, CHANGELOG line 6, `tests/test_prh_perf.py:128-133`.
*   **Discrepancy Description:** "at most 10, 12 with ESC(B" has no counter in code; the test asserts `<= 10` on shape W without `ESC(B`; hand-adding the worst branches exceeds 12. There is no fixed-point loop, so no "13th pass" leak, but the number is unsupported. Real bound: the 6 s budget, which fails closed.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** a stated number must be enforced or removed.
*   ***Proposed Edit:*** Count `redact` calls in `redact_text` and raise `InputTooLarge` past a named constant (value from a measured worst case with `ESC(B`, placeholder look-alike, percent and non-ASCII together), test that worst case, and add an `ESC(B` shape to the timing test. Fix docstring and CHANGELOG to the code. Check a legitimate large colourised log near the 262,144 cap (2.7x/3.2x slower than main; design accepts it) is not refused wrongly; report the measured time.

### [Issue 5] [`codebase` M1] - Severity: Major
*   **Affected Scope:** `CHANGELOG.md:6`, `SECURITY.md:20`, `tests/test_prh_contract.py:421-463`, `tests/fixtures/prh_accidental_pairs.json` (82 plain_not_masked + 10 no_whole_plain_reading).
*   **Discrepancy Description:** CHANGELOG says no value masked before is shown now; 92 (input, path) pairs are masked on main and not on the branch (excused because the plain reading is not masked either). SECURITY.md does not list the OSC/ST class.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** an absolute claim that is false. `test_no_step_back` pins the list (sound).
*   ***Proposed Edit:*** State the class in CHANGELOG and SECURITY.md ("a value that main removed only as the body of an unterminated string sequence is now kept, and is masked only if the plain value would be"); add the accidental-92 evidence file to the review inputs of the next snapshot.

### [Issue 6] [`codebase` M3, `design` N1] - Severity: Major
*   **Affected Scope:** `tests/test_prh_regressions.py:190-238` (pin rows excluded at 236; 32 pinned rows; no converse check).
*   **Discrepancy Description:** an unmasked, unlisted secret row with `pin` need not be named; a listed NOT_PROMISED row that is actually masked also passes; `shape:` verdicts are output hashes.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** the NOT_PROMISED list is the claim of what is not promised; it must be checkable both ways.
*   ***Proposed Edit:*** Apply the named-reason rule to pinned secret rows; assert each listed id is not masked; list which of the 32 pinned rows carry a secret. For `t_M2c` (entity cut by a hidden item) add a rule or an explicit refusal; for backslash line end confirm ticket PRH-b-line-continuation-matching exists (write the ticket text into the ledger) or fix it.

### [Issue 7] [`codebase` M4] - Severity: Major
*   **Affected Scope:** `tests/test_prh_contract.py:467-490`, `tests/record_prh_main.py:71`, `hidden_oracle.py:295`.
*   **Discrepancy Description:** 4,000+ contract cases are `not_promised` with only counts pinned; `value_not_whole_in_the_joined_reading` is judged against the oracle's joined reading where `ESC(B` keeps its letter, so the `nF`+`ESC[m` cut the consuming reading must mask lands there; the suite never checks the consuming reading across positions (how Issue 1 survived).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** the contract suite is the class-level guard.
*   ***Proposed Edit:*** Classify `nF`+`ESC[m` cuts as promised (or give them their own reason) and assert them masked; report how many of the 1,610 are that case.

### [Issue 8] [`codebase` N1] - Severity: Nit (PROPOSE FIX, cheap)
*   **Affected Scope:** `tests/prh_mutants.py:14-16`, `:42`; mutants 1-11, 16-18, 27-29, 31, 32, 39, 40, 44.
*   **Discrepancy Description:** default `expect="AssertionError"` is generic (runner wants a distinctive fragment).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** message fragments for the table killers; mutant 44 pinned to `test_regression_row[mf_t_L9]` with a tail case; fix the header wording.

### [Issue 9] [`codebase` N2] - Severity: Nit
*   **Affected Scope:** `hidden.py:100-117` (Cf via `unicodedata.category`), CI job `tests-py312`.
*   ***AI Suggestion:*** PROPOSE FIX (cheap)
*   ***Proposed Edit:*** set `HADAVIN_REQUIRE_PINNED_UNIDATA=1` in the 3.12 job as well, or state in docs that the class follows the running Python's Unicode version.

### Items recorded, judged not holes (design)
*   Tab/form feed/U+2028 inside a value (16 rows), glued word plus cut (3 rows), look-alike/encoded spellings (7 rows, pull request 77 scope): accepted as not promised, reasons stay in NOT_PROMISED. G4 colour-code ratios 2.70/3.21: acceptable (refusal, not leak), checked under Issue 4.

## Builder instructions for the fix batch
Reproduce Issues 1 and 2 by running the two inputs before fixing (the reviewers only traced by hand); one fix batch for all items; full suite once at the final head; do not reuse the stray remote branch `core/prh-b3-local` (work on `core/prh-strip-hidden-controls` only); report once.

## Handoff counts
Accepted (PROPOSE FIX): 9 (Issues 1-9). Contested: 0. Escalated: 0. Declined: 0. Round b4 review needed after the fix batch (security/redaction path, no round cap), with independent evidence on the fixed head.
