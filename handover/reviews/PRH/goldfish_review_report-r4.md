Status: resolved

# Goldfish Annotated Review Report (PR H, round 4)

**Target:** branch `core/prh-strip-hidden-controls`, head `d08ec151`. Strip hidden controls before redaction (redaction path, no round cap). No person was available: recommended option for every item. Reviews (both read-only, nothing run, findings are hand traces): `handover/reviews/PRH/prhb4-design-r4.md` (1 Blocker, 1 Major, 4 Nit) and `prhb4-codebase-r4.md` (1 Blocker, 1 Major, 3 Nit). The two Blockers are the same defect (design F1 = codebase C1); design F3 = codebase C2. Evidence (independent, head confirmed, tree clean): `handover/evidence/PRH/d08ec151/RESULTS.md`: full pytest 12897 passed, 1 skipped, 62 deselected; `prh_mutants` 55 of 55; perf 62 passed; `stage_mutants` 37 of 37; ruff, format, bandit, scan_repo, gitleaks exit 0; fail-before on `e852b577` 54 failed (3 new tests pass on old code). Evidence did NOT probe the C1 input, so C1 is unconfirmed by running. Not run: Python 3.12, full suite on main, semgrep, zizmor, trivy, pip-audit.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` F1 = `codebase` C1] - Severity: Blocker
*   **Affected Scope:** `src/hadavin_sdk/tools.py:938-947` (`_scrub`, `return alt`); callers `prepare_output` (`:1031`) and `error_reason` (`:1069`).
*   **Discrepancy Description:** When the character reading or the consuming reading holds a handed-out secret the grammar reading does not, `_scrub` returns that reading with every hidden item deleted and no gap, not the spaced copy. Hidden items that were a word boundary on main are gone. Input: handed secret HAND; text `"a " + ESC + HAND + " ; user" + BEL + KEY`. Main masks KEY (BEL separates `user` from the key). Head returns `user<KEY glued on>`, which the redactor does not mask (ticket 2.4, pinned row `t_plain_user_key`), so an AWS-style key is readable on the tool and error paths where main masked it. Same through `consuming_joined` with `ESC ( B ESC [ m` cutting HAND. No test covers it (D1a/D1b never reach the `other` branch). Evidence runner did not run this input.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Breaks promise 2 (no step back from main, also when the text holds a handed-out secret). Redaction path, uncapped. Reproduce first, then fix at the choke point.
*   ***Proposed Edit:*** (1) Reproduce by running the input on head and on `origin/main` through `prepare_output` and `error_reason`; record both outputs. (2) Do not return `alt`. Take the found set from the other reading and mask it in a spaced copy, using the same gap-pattern step as the main path (needs a spaced character reading and `rd.consuming_spaced`); where no spaced equivalent exists, fail closed (MARKER + TRUNCATED). (3) Class check: search every place a joined reading is returned or handed on (`redact.py:940-941`, `957-958`, `963-964`, `runmap.py` readings callers) for the same step back. (4) New rows on tool and error paths: boundary text (G1/G2 shapes) plus a handed secret found only by the character reading, and the same for the consuming reading (SGR-0 variant); a mutant that restores `return alt`; prove the rows fail on `d08ec151`.

### [Issue 2] [`design` F2] - Severity: Major
*   **Affected Scope:** `tools.py:938-947` (loop over `(rd.characters, rd.consuming_joined)`).
*   **Discrepancy Description:** The loop returns at the first reading with a novel find and never checks whether the second reading holds a secret that neither the joined text nor the first reading holds. Input: HAND1 and a 15-character HAND2, `ESC+HAND1+" "+HAND2[:9]+ESC+"(B"+ESC+"[m"+HAND2[9:]`: characters reading finds HAND1 only; consuming reading would find HAND2 but is never reached. Same on main (not a regression), but the claim "the scrub holds for escape spellings" is wrong and the test only combines grammar and consuming.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Same defect class as Issue 1 (reading selection in `_scrub`); fix both at the same place. Uncapped path.
*   ***Proposed Edit:*** Compute found sets over all readings once; mask the union in the spaced copy (preferred), or if the union is larger than any single reading's set and no spaced copy covers it, return MARKER + TRUNCATED. Add a characters + consuming test with two handed secrets and a mutant that checks only the first reading.

### [Issue 3] [`codebase` C2 = `design` F3] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/defaults.py:53-58`; `tests/prh_mutants.py:569-577`; `tests/test_prh_steps.py:142-145`; CHANGELOG and `runmap.py:783` docstring (17/16/7 figures).
*   **Discrepancy Description:** The comment says `tests/test_prh_perf.py` repeats the search and fails if it passes the bound, and that every regression row needs 7 or fewer passes. No such search or assertion exists; the tests only assert `17 < 24 <= 32` on the constant. The figures come from outside the repository.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A comment that names a check that does not exist is a false safety claim. Fix, do not defer.
*   ***Proposed Edit:*** Add the seeded search as a test (reuse the seeded generator in `test_prh_spans.py`) asserting the worst pass count found stays within the bound, and a test that every regression row needs at most 7 passes; or delete the sentence and write in the CHANGELOG that the figures are one-time measurements. Recommended: add the tests, then reword to what they assert. Prove the new test fails if the bound is lowered below the measured worst case.

### [Issue 4] [`design` F4] - Severity: Nit
*   **Affected Scope:** `runmap.py:149-170` (`control_refs`, `_CONTROL_REF`).
*   **Discrepancy Description:** An unterminated numeric reference (`&#27[m`, `&#x1b(B`, no semicolon) reaches `html.unescape`, which deletes ESC and leaves `[m` / `(B` as letters; no reading holds a cut key whole. Pinned as "left to the decoder" but not in the NOT_PROMISED list.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Cheap, and it is a redaction path.
*   ***Proposed Edit:*** Treat unterminated `&#27` / `&#x1b` (any case, leading zeros) followed by `[ ( ]` as ESC in `control_refs`; add rows and a mutant. If the fix turns out larger than a few lines, add a NOT_PROMISED row with the reason instead.

### [Issue 5] [`design` F5] - Severity: Nit
*   **Affected Scope:** CHANGELOG delta line 22; `SECURITY.md`; `hidden.py:163-176` (`_string_end`).
*   **Discrepancy Description:** Text says the new code "keeps" the body of an unterminated string; `_string_end` still removes it to the end of line or text (shown only when the character reading wins).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Overclaim; one sentence.
*   ***Proposed Edit:*** Reword to what the code does.

### [Issue 6] [`codebase` C3] - Severity: Nit
*   **Affected Scope:** `hidden.py:307-310` (`Readings` docstring); `tests/test_prh_hidden_unit.py:341-344`; `tools.py:955`; `runmap.py:918`; `redact.py:942`.
*   **Discrepancy Description:** "Readings is the only place that decides which readings exist" is true only for the original text and each decoded view; `tools.py:955` and `runmap.py:918` call `hidden.strip` directly and `Redactor.find` has its own two-reading helper. Consistent today (same `_scan`), duplicated work.
*   ***AI Suggestion:*** PROPOSE FIX (wording)
*   ***Justification:*** Narrow the docstrings; merging the helpers waits for Issue 1, whose fix touches the same code.
*   ***Proposed Edit:*** Reword the two docstrings to name the exceptions; if Issue 1 adds a spaced character reading, take it from `Readings` so `tools.py:955` uses it.

### [Issue 7] [`codebase` C4] - Severity: Nit
*   **Affected Scope:** `redact.py:940-941`, `957-958`, `963-964`; `tests/test_prh_contract.py:438-442`.
*   **Discrepancy Description:** Public `redact()` keeps the joined-result fallback when a found value cannot be located in the spaced reading or more than 256 values are needed. Unreachable inside `redact_text`; a direct caller gets the joined result. Promise 2 is true for `redact_text` only.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Same class as Issue 1 (a joined reading handed back). Fail closed is the safe direction.
*   ***Proposed Edit:*** Make the fallbacks fail closed (refuse) and test them; if a direct caller is found that relies on the fallback, say so in the docstring instead.

### [Issue 8] [`codebase` C5] - Severity: Nit (mutant strength)
*   **Affected Scope:** `tests/prh_mutants.py:245-253` (mutant 21), `:452-461` (mutant 44), rows `b4_1_trail`, `b4_1_nextline`, `b4_1_longtail` (`prh_regressions.json:5853` on).
*   **Discrepancy Description:** No mutant reverts the entity-branch strip point of `undo` alone; mutant 44 is pinned to `mf_t_L9` (no tail); the tail rows are pinned by no mutant; a refusal returns None and `leaked(None)` is False, so it shows as masked; only `test_cut_key_with_a_tail_is_masked_by_the_consuming_reading` sees it.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Each is cheap and the fail-before gap (Issue 11) shows the same weakness.
*   ***Proposed Edit:*** Split mutant 21 into the entity-branch strip point and the other; pin a tail row to mutant 44 or add a mutant that drops the tail; make `leaked(None)` an error for rows expected masked.

### [Issue 9] [`evidence`] - Severity: Major (ticket gate, two failures)
*   **Affected Scope:** Ticket 6.1 items 1 and 2; `src/hadavin_sdk/defaults.py`, `tests/fixtures/prh_accidental_pairs.json`, `tests/fixtures/prh_main_passes.json`, `tests/test_k5_fixes3.py`; `tests/test_prh_perf.py` (`# type: ignore[assignment]`, `# noqa: S603`).
*   **Discrepancy Description:** Four changed files are outside the ticket's allowed list; two added suppression lines break the "no suppressions" rule (CLAUDE.md quality gates: no suppressions).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** CLAUDE.md forbids suppressions; out-of-list files need a written reason or must go.
*   ***Proposed Edit:*** Remove both suppression lines (use `pytest = None` through a typed import guard or `importlib.util.find_spec`, and a fixed-argv call that satisfies S603 without a noqa, or move the subprocess call behind a helper the linter accepts). For each of the four files record one line in the builder notes (why needed; or revert). `defaults.py` and the two fixtures are probably required by the bound and the pairs; `test_k5_fixes3.py` follows the `_decoded_readings` rename. Update the ticket's allowed list in the same push if kept.

### [Issue 10] [`evidence`] - Severity: Minor
*   **Affected Scope:** Evidence RESULTS.md items F3, F4.
*   **Discrepancy Description:** The timing test failed 3 of 3 on head and main on that machine (known flaky; fix on `core/fix-timing-harness-flake`); the cost table printed only the 262,144-character rows (no 65,536, no W row, no passes column); H rows ratio to main 2.70, 3.22, 4.65, 3.22.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The cost ratios of 3 to 4.7 times main on H rows need a stated ticket bound; the missing rows mean the cost gate was not fully run.
*   ***Proposed Edit:*** Next evidence run executes the full cost table (all sizes, W row, passes) and states each ratio against the ticket's bound; do not wait on the timing fix, and cite it as known flaky with the three runs.

### [Issue 11] [`evidence`] - Severity: Minor
*   **Affected Scope:** Evidence fail-before: `test_named_ids_exist_and_the_converse_holds`, `test_pinned_secret_rows_count`, `test_regression_row[b4_ctl_colour]` pass on old code.
*   **Discrepancy Description:** Three new tests pass on `e852b577` and on main src.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Per class-level-fixes each new test needs a killer or a stated control reason.
*   ***Proposed Edit:*** One line each in the next evidence table: a mutant that fails it, or "control: pins the count / the row masks on old code as well". The Issue 1 and Issue 2 rows are the new fail-before rows.

### [Issue 12] [`evidence`] - Severity: Nit (recorded)
*   **Affected Scope:** Evidence F5, F6.
*   **Discrepancy Description:** `uv sync --locked --no-build` fails here (editable install); Python 3.12 suite and the security CI steps not run.
*   ***AI Suggestion:*** DECLINE (environment, not a code defect)
*   ***Justification:*** Python 3.12 is run in CI (`ci.yml` tests-py312, with `HADAVIN_REQUIRE_PINNED_UNIDATA=1`); the next evidence run adds a 3.12 full run if the machine has the interpreter.
*   ***Proposed Edit:*** None.

## Handoff counts
Accepted (PROPOSE FIX): 11 (Issues 1-11; Issue 6 wording only). Declined: 1 (Issue 12). Contested: 0. Escalated: 0. Redaction path, no round cap: Blocker (Issue 1) and Majors (Issues 2, 3, 9) need a fix builder (b5) and a fresh round 5 on the fixed head. The builder reproduces Issue 1 by running first, adds the rows and mutants named, and runs the full suite once on the final head. Ledger: PR H round 4 Blocker and Majors OPEN until the fix is verified by independent evidence including the Issue 1 input on both trees.
