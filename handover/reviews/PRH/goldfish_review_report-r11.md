Status: resolved

# Goldfish Annotated Review Report

**Target:** PR H batch 11, branch `wip/cloud-prh-b11`, head `242dfd66` (code head `63525de6`, previous reviewed head `9de76195`), round 11. SECURITY / REDACTION path: no round cap.
**Inputs:** `prhb11-design-r11.md` (0 Blocker, 5 Major F1-F5, F6-F9 Minor, F10 Nits), `prhb11-codebase-r11.md` (0 Blocker, 4 Major F1-F4, 4 Minor F5-F8), previous report `goldfish_review_report-r10.md` (newest numbered one before this), independent evidence `handover/evidence/PRH/242dfd66/RESULTS.md`.
**Mode:** automated; no person available; the recommended option is taken for every item. No severity is changed. No finding is contested: each is checkable in the snapshot or the evidence, or is a stated owner item. Where the two reviewers rate one finding differently, both ratings are kept. Design and codebase findings that are the same defect are merged into one group.

## Evidence summary (recorded by the independent runner, not judged)
- `prh_mutants` 176 of 176 good as root and as user nobody (4 accepted CRASH kills: 22, 24, 143, 158); `stage_mutants` 37 of 37; full pytest 13286 passed, 1 skipped, 63 deselected, exit 0; ruff, format, bandit, `scan_repo`, gitleaks exit 0.
- The builder's pytest numbers (12830 passed, 457 skipped at code head `63525de6`) do not match the runner's (13286 passed, 1 skipped at `242dfd66`). The runner had its own Postgres 16.15 and `HADAVIN_REQUIRE_PINNED_UNIDATA=1` set; neither side found why the counts differ (the 457 skips and 456 extra passes). Recorded, not explained: design F1 stays open until the builder shows it.
- `pytest -m perf` exit 1: 1 failed, 62 passed. The one failure is the known timing test `test_the_timing_harness_flags_a_quadratic_stand_in` (alone on head 2 of 3 passed, on main 3 of 3 passed; the machine was busy). Do not touch it. Perf ratios against main (262,144 characters, median CPU): S1 1.15, S2 1.13, S3 1.31, S4 1.06, S5 1.06, H1 3.01, H2 3.56, H3 5.00 (1.87 s), H4 3.60, P1 1.19, P2 1.83, P3 1.75, P4 1.30, P5 4.38 (1.85 s), P6 1.30; the machine was shared.
- Fail-before on `5c430b6a`: `tests/test_prh_b11.py` 45 failed, 29 passed (matches the builder's claim; the 29 names are in `failbefore-b11-passed-on-old-list.txt`). The other changed test files: 4 failed, 150 passed; 3 of the 4 are `test_prh_b9_docs.py` failing on a missing `handover/evidence/PRH/b11/numbers.txt` (a file the runner did not copy: a runner artefact); the 4th, `test_b10_g5_the_wrapper_list_is_the_one_in_the_code`, was not examined.
- Own fuzz (922 texts per tree): readable 581 on main, 239 on `5c430b6a`, 217 on head. No text is readable on head that is not readable on main or on `5c430b6a`. Classes still readable on head: spaced values with combining marks 36 of 36 (the same on all trees), spaced with wrapper characters 42 of 252 (main 169, old 51), split values with filler words 64 of 80, backslash-e inside a value 10 of 12 (12 of 12 on old and main), visible-gap spaced 2 of 12, ESC in the middle 2 of 30, hidden control in the middle 2 of 26. Run cap: 0 readable, 0 withheld, 0 errors. Redactor crash: on head all six paths raise `RedactorCrash`.
- Not run (impossible now): Python 3.12, Vault tests, a live call. The runner's seeded 6000-text clean corpus withheld 0; the builder's own corpus (21,783 texts) was not rerun, so those numbers are not comparable.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design F4`, `codebase F1`] - Severity: Major (both)
*   **Affected Scope:** `src/hadavin_sdk/runmap.py:56-60, 1211-1223` (`safe_head`); callers `approvals/requests.py:44-51`, `evals.py:62-70`, `guard/injection.py:85-101`, `runtime/tick.py:287-292` (used at :316-317), `extract.py:55-58`, `k1b/loop.py:187,194`; `agent_loop.py:432, 514, 565`.
*   **Discrepancy Description:** "One crash rule at every catcher" stops at the `tools.py`/`runmap.py` border. `safe_head` was documented "never raises" and now raises `RedactorCrash`. `approvals/requests.py:44` catches `RedactionError`: a crash shows "(too large to show here)" and the approval goes on. `evals.py:64` turns a crash into a `ConfigError` "cannot be redacted". `injection_check` promises that a detector error is a flag, never a pass, but calls `safe_head(str(exc), 300)` inside the `except` block, so a crash escapes through `_screen` with no handler. `tick._run_step` calls `_message(exc)` inside `except Exception`, so a crash escapes before `save_tick_state` and stops the remaining steps of the tick. Design: the forged-marker downgrade to a withheld note is not stated in the CHANGELOG or SECURITY.
*   **Rationale:** A crash of the redactor must stop the run at one place by one rule, never look like a size limit and never let an approval card be issued.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Name the class "a crash read as a limit or swallowed by an unrelated handler". Grep every catcher and caller of `RedactionError`, `safe_head`, `error_reason` and `redact_*` in `src` and `demos`, decide one rule per sibling, correct the `safe_head` docstring, and test each with a raising spy: the approval summary, the injection check, the tick step, `extract`, `k1b/loop`, `evals`. One mutant per catcher. State the forged-marker downgrade in the CHANGELOG and SECURITY.
*   ***Proposed Edit:***
    *   Location: the callers listed, `runmap.py` docstring, CHANGELOG, SECURITY.
    *   Change: as above; fail-before measured on `242dfd66`.

### [Issue 2] [`design F2`, `codebase F2`] - Severity: Major (both)
*   **Affected Scope:** `runmap.py` `ESC_E`; `tests/test_prh_b11.py:380-413`; SECURITY paragraph "NOT fixed".
*   **Discrepancy Description:** A spelled-in backslash-e stays readable inside a value. The rule is a length-and-alphabet heuristic (6 or more of `[A-Za-z0-9_-]` on each side, or 12 or more after, or next to another `\e`). Not read: fewer than 6 token characters after (a 15-character prefix plus `\e` plus the last 5); 6-11 after with fewer than 6 before; any symbol (`+`, `/`, `&`) inside the 6-character window; every handed-out secret of 6-11 characters; `\e` every 2-5 characters. The grid only uses 28-character values at offsets 9, front, or every character. The runner measured 10 of 12 readable on head (12 of 12 on old and main). Same class as r10 group 8, narrowed and not closed.
*   **Rationale:** Not a regression against main, but an own claim ("closed") that the evidence does not carry.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decide by held or token-shaped value rather than a length rule: treat `\e` between two non-space characters of one token as escape glue (mask), keep the Windows-path rows as controls (`C:\env`, `C:\Users\err\x`, `D:\tmp\ex\data` unread). Add cells for offsets 1-5 from each end, a short value, `+ / &` in the window, and a 6-11 character handed-out value; a mutant that restores the old thresholds. If a shape cannot be closed, name it under NOT fixed with the number measured.
*   ***Proposed Edit:***
    *   Location: `runmap.py`, `tests/test_prh_b11.py`, `tests/prh_mutants.py`, SECURITY.
    *   Change: as above.

### [Issue 3] [`design F3`, `codebase F3`] - Severity: Major (both)
*   **Affected Scope:** `runmap.py:634` (`_char_reading_wins`), `:657` (`_consuming_wins`), `:694-728`; `tests/test_prh_b11.py` g2 (:227-234).
*   **Discrepancy Description:** Sibling containment sites unchanged: `novel = any(not any(v in k for k in values) ...)` where `values` is every held non-seed value of any kind. A key cut by an escape sequence that is a piece of an identifier held earlier (for example an ARN-like held value) is not "novel", so the reading does not win and the cut copy stays readable; `_refuse_remnant` skips it. Neither reviewer built or ran it.
*   **Rationale:** r10 group 2 asked for siblings; only one site got the fix.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** First reproduce with a made-up held value built from parts and a second cut copy. Then reuse `_only_inside_held` or restrict to secret-kind non-seed holders at both sites; one test and one mutant per site, shown failing on `242dfd66`; or a written proof if a site is not reachable.
*   ***Proposed Edit:***
    *   Location: `runmap.py:634, 657`, tests, mutants.
    *   Change: as above.

### [Issue 4] [`codebase F4`, `design F4(c)`] - Severity: Major
*   **Affected Scope:** `tests/test_prh_b9_docs.py` (`test_b11_every_figure_in_security_is_in_the_numbers_file`, `test_b11_the_numbers_file_is_what_the_raw_files_give`), `tests/prh_mutants.py`, CHANGELOG item 7, `evidence_numbers.py`.
*   **Discrepancy Description:** The figure test searches for figures of 3 or more digits in the concatenation of every `.txt/.log/.md/.jsonl/.py` file under `handover/evidence/PRH/`, so almost any invented figure is found; it fails only on "898"; it reads one paragraph; two-digit figures (50, 23, 75) are excluded. The second test loads a spec it never executes; its docstring is false. The CHANGELOG says "mutants 161 to 185" and tests cite 164, 166, 169, 177 and 179, which do not exist (present: 161-163, 165, 167, 168, 170-176, 178, 180-185). `error_reason` has no mutant (r10 group 4 asked one per catcher).
*   **Rationale:** Tests that cannot fail and mutant numbers that do not exist are a gate that looks closed and is not.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Compare figures only against `numbers.txt` and the b11 raw files; execute `evidence_numbers.py` and compare its output; read every figure of SECURITY and the CHANGELOG (two-digit included, with a list of allowed code numbers); add the `error_reason` mutant; renumber or remove the ghost mutant names; correct the CHANGELOG range. Plant a wrong figure and show the test fails.
*   ***Proposed Edit:***
    *   Location: files above.
    *   Change: as above.

### [Issue 5] [`design F1`, `evidence`] - Severity: Major
*   **Affected Scope:** builder pytest log (no `-rs`), `handover/evidence/PRH/b11/`.
*   **Discrepancy Description:** 457 skipped tests never broken down. The b10 run had 1 skipped (13209 passed); b11 has 457 skipped and 12830 passed (74 new tests, so about 456 tests that ran before now skip). The independent runner got 1 skipped and 13286 passed; the cause of the difference is unexplained (a Postgres service and one environment variable were set on the runner's side). Not shown that no `tests/test_prh_*` is skipped.
*   **Rationale:** A skip count that large can hide a whole group of redaction tests.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** At the final head, run with `-rs`, table the skips by reason and file, and show the environment (Postgres, variables, user) of each full run; any `test_prh_*` skip is a defect to fix. Stamp every log with the head it ran at.
*   ***Proposed Edit:***
    *   Location: `handover/evidence/PRH/b12/`.
    *   Change: as above.

### [Issue 6] [`design F5`, `codebase F5`] - Severity: Major (design) / Minor (codebase)
*   **Affected Scope:** `guard/redact.py:986, 991` (`_NOT_BEFORE`), `_SEP`, `_TOK`, `_IGN`; `tests/test_prh_b11.py:158-173`.
*   **Discrepancy Description:** A glued letter, digit or mark in front of a spaced run starts no run, and a test pins the spaced key as readable. The new lookbehind blocks any L/N/M, while `_SEP` and `_TOK` treat variation selectors, U+034F and the filler letters U+115F, U+1160, U+3164, U+FFA0 as gaps; batch 10 allowed an ignorable character before the first token. Codebase: `key:` plus U+FE0F or U+3164 glued before `A K I A ...` stops the run at the first token (about 90 percent sure, not run): a regression against batch 10, not against main. The runner measured spaced values with combining marks 36 of 36 readable (same on all trees).
*   **Rationale:** Same class as r10 group 1 moved to a letter exception; SECURITY says "no run is read from there" and does not list it under NOT covered.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Subtract `_IGN` from the lookbehind class; also try the run with the glued character split off as a wrapper; rows for U+FE0F, U+3164, a letter and a digit glued at the head and the tail; run before and after on `242dfd66` and main with measured counts. What cannot be closed goes under NOT covered with the owner question.
*   ***Proposed Edit:***
    *   Location: `guard/redact.py`, tests, mutants, SECURITY.
    *   Change: as above.

### [Issue 7] [`design F7`, `codebase F6`] - Severity: Minor (both)
*   **Affected Scope:** `runmap.py:694-728` (`_only_inside_held`), `redact.py:1574-1584`.
*   **Discrepancy Description:** The function is outside the work budget: overlapping `find` plus slice assignment per hit (about 260k hits of 1.7 KB for a 262,144-character text with a held PEM-size value and a held run); the docstring "one search per held value" understates. Multi-line or spaced holders never match `compact` (safe direction, over-refuses). A spaced copy of a holder shorter than 12 characters counts as covered while the sweep masks spaced copies only of 12 or more.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Charge each search in `_Work` (or use a rolling check), require `len(k) >= SPACED_VALUE_MIN_CHARS` for the covered case; a test with a large text and a big holder showing the charge; a mutant. Fix the docstring.
*   ***Proposed Edit:***
    *   Location: `runmap.py`, tests, mutants.
    *   Change: as above.

### [Issue 8] [`design F8`, `codebase F8`] - Severity: Minor (both)
*   **Affected Scope:** `handover/evidence/PRH/b11/`, `HEADS.txt`, `REDACT_BUDGET_S`, perf rows H3 and P5.
*   **Discrepancy Description:** Evidence staleness: the builder's full pytest and gates were at `63525de6`, perf at `784b573f`, the spaced-rate corpus at `5c430b6a`, the snapshot at `242dfd66`; `HEADS.txt` says only `tests/` changed after the full run. Perf H3 5.00x main (1.87 s) and P5 4.38x (1.85 s) against `REDACT_BUDGET_S` 6 s: on a runner 3x slower an ordinary 262,144-character coloured text is refused by the clock. r10 group 5 asked for a reduction and none was made. The call-wide spaced-read budget (200,000 characters over all views) is not measured on large multi-view texts; the perf rows do not say whether P5 and P6 are withheld or processed. The independent runner has now measured all of this at `242dfd66` on a shared machine (load about 3.5).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Re-run and stamp at the final head; decide the budget margin or measure CPU time instead of wall clock with a written number; say in the perf table which rows are withheld; add the per-run load.
*   ***Proposed Edit:***
    *   Location: evidence folder, `redact.py` budget, CHANGELOG.
    *   Change: as above.

### [Issue 9] [`design F6`] - Severity: Minor
*   **Affected Scope:** `handover/evidence/PRH/b11/failbefore-b11-new-tests-on-5c430b6a.txt:978-1121`.
*   **Discrepancy Description:** Made-up `ghp_`-shaped values (23 occurrences) and a 28-character handed-out value are committed in pytest parameter ids. The preamble allows only the AWS example literal. The shipped test ids are now `hand` and `shaped`, so the evidence came from another test version.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Regenerate the file from the shipped tests; replace the committed file (history keeps it, the lead decides about rewriting history: owner item if so); run `tools/scan_repo.py` and gitleaks on every evidence file before commit.
*   ***Proposed Edit:***
    *   Location: that file.
    *   Change: regenerated; no secret-shaped literal.

### [Issue 10] [`design F9`, `codebase earlier r10 G5`] - Severity: Minor
*   **Affected Scope:** `handover/evidence/PRH/b11/NOTES.md` "Group 7"; `runmap.py` (stop later drops once an earlier one found nothing).
*   **Discrepancy Description:** r10 group 5 item "stop later drops once an earlier one found nothing" and "time per view" are parked under an owner-only label. It limits reads per run; it is not piece masking, so it is not owner-only (fix, do not defer).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Build it or measure and show why it cannot happen (with the number); move it out of the owner section.
*   ***Proposed Edit:***
    *   Location: `NOTES.md`, `runmap.py`, tests.
    *   Change: as above.

### [Issue 11] [`codebase F7`, `design F10 (Nits)`] - Severity: Minor / Nit
*   **Affected Scope:** SECURITY.md; `test_prh_b11.py:216-218`; mutant messages 168 and 170; word-class scan in `redact.py`.
*   **Discrepancy Description:** SECURITY overstates "NOT read before P, X, ^ or _ ... before other letters": the code reads `\e` before any run of 12 or more token characters. The word-class scan (`range(0x32400)` and `0xE0000-0xE1000`) misses Unicode 17 CJK Extension J (U+323B0-U+3347F). The docstring at :216-218 says "only before a bracket or a parenthesis" against the inside rule. Mutant 168/170 messages say "mutant 169". 209k `unicodedata.category` calls at import, unmeasured.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Correct each: add "unless 12 or more token characters follow", extend or justify the plane bound with a test over the Unicode data, fix the docstring and messages, measure the import time and state it.
*   ***Proposed Edit:***
    *   Location: files above.
    *   Change: as above.

### [Issue 12] [`owner items`] - Severity: Major (owner question)
*   **Affected Scope:** `q-prh-piece-masking`, `q-prh-spaced-secrets`.
*   **Discrepancy Description:** Owner decisions about masking pieces of a value and spaced-out secrets; the price of piece masking has not been measured (codebase).
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** The evidence is the owner's decision, outside every file the reviewers could read. Stay OWNER-ONLY and unbuilt; do not report closed.
*   ***Proposed Edit:***
    *   Location: `handover/questions-for-lead.md`.
    *   Change: none by the builder.

### [Issue 13] [`evidence gate`] - Severity: Major
*   **Affected Scope:** the batch-12 evidence.
*   **Discrepancy Description:** Runner open points: `test_b10_g5_the_wrapper_list_is_the_one_in_the_code` fails on old code with a cause not examined; the three `test_prh_b9_docs.py` failures are a runner artefact (a missing copied file); the known timing test flaked on head (2 of 3 passed) and not on main (a busy machine); the runner's fuzz does not cover the Issue 1 catchers, Issue 3 or the glued-mark shape.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Batch 12 explains the b10 test (cause stated), measures fail-before with the whole delta test set and its data files, and a full independent evidence run on the batch-12 head is a gate: it must include a raising-spy probe per catcher, a held-identifier sibling probe, and the glued-mark shapes, with the timing test run alone and idle.
*   ***Proposed Edit:***
    *   Location: `handover/evidence/PRH/b12/`, the runner brief.
    *   Change: as above.

## Handoff
- PROPOSE FIX: 12 groups (Issues 1-11 and 13), 0 contested, 0 declined.
- ESCALATE: 1 (Issue 12, the two owner items).
- Contested: 0. Declined: 0.
- Remaining unaddressed: all fixes are unbuilt until batch 12. Blockers: 0. Majors: Issues 1-5 and 13 (Issue 6 is Major by design, Minor by codebase; Issue 12 is the owner question).
- Gate: the independent full evidence run on the batch-12 head. No claim of "done" before it.

## Who fixes it
One batch-12 builder on `core/prh-b12` from `242dfd66`, pushing to `wip/cloud-prh-b12`. Order: Majors first (Issues 1, 2, 3, 4, 5, 13), then 6, 7, 8, 9, 10, 11. Method per bug: name the class, cite the standard, fix at the shared choke point, grep siblings, new tests shown failing on `242dfd66` with measured counts, one mutant per fix killed for the named reason, full suite and all mutant sets (`prh_mutants` as root and as nobody, `stage_mutants`) on the final head, a written reason for every test that passes on old code, CHANGELOG counts recomputed. Never touch the known timing test. Then: snapshot, independent evidence runner, two `egm:*` reviewers, `egm:egm-resolve`. Security path: no round cap.
