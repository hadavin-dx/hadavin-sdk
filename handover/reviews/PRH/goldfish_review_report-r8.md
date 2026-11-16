Status: resolved

# Goldfish Annotated Review Report

**Target:** PR H batch 8, handover head `b8fbf659`, code head `ea6dbdaf`, round 8 (REDACTION path: a secret must not stay readable before a model, a log or the audit trail; no round cap).
**Inputs:** `prhb8-design-r8.md` (1 Blocker, 6 Major, 1 Minor, 1 Nit), `prhb8-codebase-r8.md` (2 Blocker, 7 Major, 2 Nit), independent evidence `handover/evidence/PRH/ea6dbdaf/RESULTS.md`.
**Mode:** automated, recommended option for every item. No severity changed. Nothing contested: the evidence runner reproduced the red mutant gate and the readable stretches, so the findings stand. Two Blockers in the codebase review and one in the design review are open at this head. Nothing may be called review-clean.

## What the independent evidence shows (recorded, not judged)
- Full pytest 13106 passed, 1 skipped, 62 deselected, exit 0; `stage_mutants` 37 of 37; ruff, format, bandit -ll, scan_repo, gitleaks exit 0.
- **Mutant gate RED:** `prh_mutants` 109 of 114 good as user nobody and as root: 54, 84, 93 SURVIVED, 59 WRONG_REASON, 111 SURVIVED (survived in 4 of 4 runs, never seen killed).
- Disabling the `(fj, fs)` append changes no test (2616 passed on both) and the same five mutants: the builder's claim reproduces on the sample.
- Builder's "17 failed, 29 passed" does not reproduce as written: `tests/test_prh_b8.py` cannot be collected on `5f9df48e` (ImportError `spaced_unknown`); with a shim 19 failed, 29 passed.
- Own fuzz (4691 made-up texts per tree): readable leaks main 2999, `5f9df48e` 477, head 458. Head groups: 55 are the backslash-plus-letter-e spelling of ESC; 63 random multi-cut; 270 split texts (277 on main); 15 of 21 spaced values with a separator other than one space; an unknown 17-character value matching no pattern, single spaces, is not masked on any tree (40 of 40); a key with tabs is not masked.
- Clean corpus (7896 texts): withheld or error main 57 (0.72%), `5f9df48e` and head 121 (1.53%).
- Spaced-run measure with the final 6-distinct rule: repository text 83,184 lines, 2 hold a run, 0 changed; Python 3.13 library 1,933,591 lines, 64 hold a run, 0 changed; positive control found 1 run; seven ordinary spaced texts 0 changed. The builder's 83,589 comes from another tree state.
- Perf head / main at 262,144 characters: S rows 0.91-1.04; H1 2.88, H2 3.36, H3 4.85, H4 3.34; W 2.2 (head 3.5 s). The official compare has no spaced-run shape.
- The known flaky `test_the_timing_harness_flags_a_quadratic_stand_in` failed alone 3 of 3 on head and on main: not touched.

## Prioritized Findings & AI Suggestions (all PROPOSE FIX unless stated)

### [Issue 1] [design D1, codebase B1, M2] - Blocker
Scope: `tests/prh_mutants.py` mutants 54, 59, 84, 93, 111; `tools._scrub` (consuming reading), `_decoded_readings` (character reading), direct `redact()` (ignorable reading), `mixed_keys` soft rule.
Gap: each survivor is a live guard in `src/` that no test needs. 54 survives because the new `mixed_held` check turns the same input into a withheld note and the test only asserts the secret does not stand, so masked and withheld look the same. 111 is killed only by an unrelated b4 row, which means it is killed by accident or by load. 59 is killed for the wrong reason. "Made redundant by b8" is no resolution.
Fix: one test per survivor that fails when its guard is removed, or delete the guard with a constructed proof (never on the sample). 54's test requires the MASKED output. 111 gets a purpose-built killer (a spaced run whose collapsed reading leaves a remnant, text not refused). 93 is killed by the probe `"ghp_" + ESC M + ESC e + "abcdefghijklmnop" + BEL + "qrstuv"` (built from parts). The gate must be green as nobody AND as root, with the killer message naming the planted fault.

### [Issue 2] [design D2] - Major
Scope: `redact.py` `Redactor.find` `(fj, fs)` fold (~1048, 1092-1097, 1135).
Gap: neither proven dead nor justified; random texts cannot show it dead.
Fix: KEEP the fold. Build the input that needs it (a lone ESC plus a letter-final nF sequence in one text, e.g. ESC K together with ESC ( B, with the character reading skipped because `leaves_text` is true), pin it with a mutant, and write the reason in the docstring. Never delete on the sample.

### [Issue 3] [design D3, codebase M7] - Major
Scope: `defaults.py:54-61`, Issue 9 (`check_only`), the passes hill-climb.
Gap: a value only inside an unterminated string body still withholds the whole text; the 60-second hill-climb was not repeated; seeded worst passes now 16 against cap 24 (the comment says 14 before); "time box" is not an allowed exception. Perf multipliers on hostile shapes are 2.9 to 4.9.
Fix: narrow `check_only` and repeat the hill-climb, or send the exact blocker to the owner; state the real multipliers and the real worst-pass number in the docs.

### [Issue 4] [design D4] - Major
Scope: `defaults.py:86`, `redact.py:888`, CHANGELOG batch 8 item 3, SECURITY spaced-out bullet, `tests/test_prh_b8.py:165-172`.
Gap: `SPACED_RUN_MIN_DISTINCT = 6` has no written claim; the "no change" figure predates the rule; no rows for a spaced alphabet, digit table, spaced hex, CJK list; the ordinary-text test has no single-character tokens; the `"x " * 400` test only checks the letter count.
Fix: add the rows with exact outputs, fix the test at 165, document the rule, and use the re-measured numbers above.

### [Issue 5] [design D5, codebase M1] - Major
Scope: `redact.py:228-247` (`_SPACED_RUN`), SECURITY bullet 3.
Gap: bypasses: two spaces, tab, newline; a value glued to its key (`key=A K I A ...`: first character lost); trailing punctuation; a keyed value (collapsed token tested without the keyword); five or fewer distinct characters; prefix and separator bypasses. Evidence: 15 of 21 other-separator values leak; an unknown 17-character spaced value leaks on every tree.
Fix: test the collapsed token with its keyword context; accept any whitespace run; strip trailing punctuation from the last token; separate a glued key. Either cover an unknown-shape run or state plainly, in SECURITY, CHANGELOG and a test that pins the statement, that only shape-based values are covered. Every leak group in the evidence is fixed or classified: the backslash-e spelling (55) and the split texts (270, 277 on main) get a named class, fixed if one choke point serves, else the exact reason and the next step. Nothing is filed as a "known limitation".

### [Issue 6] [design D6, codebase B2] - Blocker (highest in group)
Scope: CHANGELOG line 8; `tools.py:1041` `_scrub` docstring; `prh_mutants.py:1136`; `defaults.py:57`; `hidden.py:122-128` `strip_keeping` and the `Readings` docstring.
Gap: text says what the code does not keep: "spaced-out secrets ... not masked on any path"; "`redact.compare_readings` shared with `runmap._consuming_wins`" (false now); `_scrub` says "not read (LIMITS)" while `_scrub_layers` calls `_mask_spaced_out`; "13 new mutants, 102 to 114" (115 exists); "most redact passes ... is now 8" (seeded worst is 16); `strip_keeping` says it never shows a swallowed body while with `keep is True` ESC followed by an nF sequence leaves `(B` as text.
Fix: correct each, and add a test that reads every documented number against its live constant.

### [Issue 7] [design D7, codebase M3] - Major
Scope: `redact.py:228-247`, `runmap.py` ~1019-1030, `_sweep`, `spaced_spans`.
Gap: cost of a spaced run is unbounded and unmeasured: each run of 10+ tokens with 6+ distinct characters builds a `_Redactor` and runs every pattern; no cap on runs; a hostile 262,144-character text gives about 13,000 runs; `_sweep` is quadratic with many values; `spaced_spans` can give one span per position.
Fix: a spaced-run shape in the perf compare, a cap on runs per text with a withhold (not a skip) outcome, a linear `_sweep`, and a perf re-run on the final head.

### [Issue 8] [codebase M4, design D8] - Major
Scope: `redact.py` `_stands_in` (~1140-1148, `width=8`).
Gap: the soft-reading conflict check skips values shorter than 8 characters; no leak constructed, unproven.
Fix: a row with a short secret and a conflicting second value; fix it or prove it.

### [Issue 9] [codebase M5] - Major
Scope: `runmap.py` ~603-609 (`mixed_keys` drop).
Fix: fix at the choke point with a test that fails on the old code.

### [Issue 10] [codebase M6, design D9 Nit] - Major
Scope: `tests/test_prh_b8.py:242, :293`.
Gap: the 3,096-text generator runs twice (LCG and `random.Random(777)`), with an S311 `noqa`.
Fix: one generator, remove the `noqa` where possible.

### [Issue 11] [evidence deviations] - Minor
Gap: the notes' "17 failed, 29 passed" does not reproduce (collection error on the old code). 29 tests pass on the old code: 20 `test_b8_i4_runner_rows_leave_no_readable_stretch` rows, 3 `test_b8_i3_direct_redact_masks_or_withholds_every_copy` rows, and six named tests (short_known_value_with_spaces_is_not_touched, ordinary_spaced_text_is_unchanged, a_soft_conflict_is_not_a_refusal, one_key_cut_twice_is_one_placeholder, a_handed_out_value_cut_by_a_charset_sequence_and_a_kept_letter, the_withheld_share_is_bounded). The withheld-share bound (155) passes with the old 143 too; the ordinary-text test does not test what it says. The clean-corpus withheld share rose from 0.72% to 1.53%.
Fix: notes state the real counts (19 failed, 29 passed with a shim); one stated reason or killing mutant per passing test; tighten the withheld-share bound to the measured value; state the 1.53% and why it is accepted (it is the cost of withholding instead of leaking), with the number, in CHANGELOG and SECURITY.

### [Issue 12] [evidence] - closed
Full pytest, stage_mutants, ruff, format, bandit, scan_repo and gitleaks are green as listed above. The builder's claim about the `(fj, fs)` append reproduces (see group 2).

## Handoff
- Findings in: design 1 Blocker, 6 Major, 1 Minor, 1 Nit; codebase 2 Blocker, 7 Major, 2 Nit; merged into 12 groups.
- PROPOSE FIX: 11 groups (Blocker 1 and 6; Major 2-5, 7-10; Minor 11). CONTEST 0. ESCALATE 0 (an owner question only if group 3 cannot be done). DECLINE 0 (the Nits are folded into groups 10 and 11 and the builder fixes those in files it edits). Closed by evidence: 1.
- Applied edits: none to code by this skill. Remaining unaddressed: groups 1-11 (OPEN). Two Blockers stand.
- **Who fixes it:** one batch-9 builder (general-purpose, Sonnet) on `core/prh-b9` from `b8fbf659`, pushing to `wip/cloud-prh-b9`. Files: `src/hadavin_sdk/{redact.py,tools.py,runmap.py,hidden.py,defaults.py}`, `tests/prh_mutants.py`, `tests/test_prh_b8.py` or a b9 file, `CHANGELOG.md`, `SECURITY.md`, builder notes. Order: group 1 (green gate first), 2, 9, 8, 5, 4, 7, 3, then 6, 10, 11. Method per bug: name the class, fix at the shared choke point, grep for siblings, property or fuzz tests, show each new test failing on `ea6dbdaf`, one mutant per fix and guard branch. Gates once on the final head, mutant gate as nobody and as root, perf alone. Redaction path: no round cap.
