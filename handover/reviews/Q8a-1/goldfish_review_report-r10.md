Status: resolved

# Goldfish Annotated Review Report (Q8a-1, round 10)

**Target:** branch `wip/cloud-q8a1-b10`, head `f4acee28`. SECURITY path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `q8a1b10-design-r10.md` (0 Blocker, 0 Major, 1 Minor, 2 Nit) and `q8a1b10-codebase-r10.md` (0 Blocker, 0 Major, 5 Nit). Independent evidence: `handover/evidence/Q8a-1/f4acee28/RESULTS.md` and its probe files. Key facts: ruff, format, bandit, `scan_repo`, gitleaks exit 0; `stage_mutants` 176 of 176; full pytest 11043 passed, 1 skipped (it needed four runs; runs 1 and 2 failed only on the runner's own database set-up, which the runner says but did not prove beyond run 3); fail-before on `f0febfb6` src: 3 failed, 406 passed, and 2 of 5 new or changed test functions PASS on old code; on main src 63 new-test-name instances pass; timing test flaked 6 of 6 (known; fix lives on `core/fix-timing-harness-flake`, do not touch).

**Verification of the round 9 C1 Major (configured Kubernetes namespace printed): VERIFIED FIXED by probe on `f4acee28`.** A made-up secret-shaped marker in 12 positions and settings forms, 6 rule kinds and 5 answer shapes (196 direct rows plus 100 `scope_problems` rows): on head the marker appears in no returned message, exception text or traceback; on `f0febfb6` 112 of 196 and 72 of 100 rows held it. The ledger row for round 9 C1 can be marked FIXED-VERIFIED (verifying artifact: the probe files in the evidence folder). Both reviewers also closed it by reading.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` G1] - Severity: Minor
*   **Affected Scope:** `tests/test_stage_names.py:3216-3226, 3293-3324, 3333-3365` (guard lists and `_config_derived`, `_message_nodes`); `KubernetesSettings` empty-string entry.
*   **Discrepancy Description:** The guard is a list of known spellings, not a class-level control. Not flagged: a renamed variable (scope, entry, value, item), plural attributes (`self.namespaces`, `*_secret_name`), `", ".join(names)` / `sorted(names)` (a Call that is not str/repr/format/.get returns False), `msg += name`, `%` or `.format` with a variable template, a logger not named `*log`, and a pass-through `f"{exc}"` of a library error that quotes a value. Example: `raise ConfigError(f"source {entry} refused")` with `entry` from options passes the guard and prints the password. Third time this class returned (round 8 Issue 4, round 9 C1, now namespace/ns). The evidence also shows settings accept an empty-string entry (the same shape).
*   ***AI Suggestion:*** PROPOSE FIX (cheap shape-widening)
*   ***Justification:*** Security path; a class that keeps returning is fixed at the choke point as far as is cheap, with the type-level fix left to the owner.
*   ***Proposed Edit:*** (a) Flag any interpolation of a loop variable or settings attribute in a message unless it goes through `shown_name`/`_named`; default "an unknown value in a message needs an allowance"; add `join`, `sorted`, `AugAssign`, `%`/`.format` with a variable template and non-`log`-named loggers; plant one fault per shape to prove the guard fails on each. Make settings refuse an empty-string namespace entry. (b) The class-level `ConfigName(str)` whose `__str__`/`__format__` return "<not shown>" is a larger design change: ESCALATE as the already open owner question `q-q8a1-hide-ids` (safe default stays: no new type); record it, do not decide it.

### [Issue 2] [`evidence` and lead instruction: trace the 11 f-string hits] - Severity: Minor
*   **Affected Scope:** `secrets_gcp.py:39`, `llm/anthropic.py:32-33`, `sources/kubernetes.py:237, :251` (API paths), `store/migration_numbers.py:251`, `store/migrate.py:212`, `backends/table.py:367, 379, 380, 394`.
*   **Discrepancy Description:** A scan of `src` for configured names in f-strings found 11 hits, not traced to messages by the evidence runner.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** On a security path a hit that was not traced is not cleared; the same class has come back three times.
*   ***Proposed Edit:*** The fix builder traces each hit: either prove by test that it never reaches a message, log or exception text (request path only), or route it through `shown_name`. Result as a table in the PR notes; the new guard of Issue 1 must cover these files so a future hit fails it.

### [Issue 3] [`design` G2] - Severity: Nit
*   **Affected Scope:** `rules_problems(where, ...)` public; `tests/test_k5_round9b.py:292`.
*   **Discrepancy Description:** The public function prints any label it is given.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Make it private, or take an index; update the one caller. (Also covers `codebase` N4: the renamed parameter and message prefix break keyword callers with `TypeError`; add one CHANGELOG sentence.)

### [Issue 4] [`design` G3] - Severity: Nit
*   **Affected Scope:** `KubernetesSettings.namespaces` (`kubernetes.py:62`).
*   **Discrepancy Description:** No DNS-1123 pattern.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Add the pattern with a fixed-sentence refusal that does not echo the value; test with the marker.

### [Issue 5] [`codebase` N1] - Severity: Nit
*   **Affected Scope:** CHANGELOG bullet "Names from files go through `errors.shown_name`".
*   **Discrepancy Description:** It lists method and host names in `tools.py`, but `tools.py` prints neither (method refusal names `op` via `shown_name`, host refusal is a fixed sentence); hosts are printed only in `guard/http.py`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Name what is really printed and where; use another example for the "identical text" remark.

### [Issue 6] [`codebase` N2] - Severity: Nit
*   **Affected Scope:** `kubernetes.py:331-332` (start=1), `tools.py:229-237` (from 0); pinned 1-based at `test_stage_names.py:3134`.
*   **Discrepancy Description:** Position labels use two bases.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Make all labels one base (1) with the test pinning it, or say it once in the CHANGELOG; prefer one base (a person reading "entry 0" is confused).

### [Issue 7] [`codebase` N3] - Severity: Nit
*   **Affected Scope:** `test_stage_names.py:3095-3098`.
*   **Discrepancy Description:** Docstring claims "in the message, the cause or the traceback"; the test asserts only the problem strings.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Drop the claim, or extend the assertions (the evidence probe already checked cause and traceback: cite it, or add them to the test).

### [Issue 8] [`codebase` N5] - Severity: Nit
*   **Affected Scope:** guard allowance reason `test_stage_names.py:3274-3275`; evidence ids `kubernetes.py:244, 259, 271, 298, 303, 315` carry `{scope}`.
*   **Discrepancy Description:** The reason hides that evidence ids carry the namespace the caller asked for; not a leak (scope must equal a configured namespace the model supplied) but "never printed" is true only of messages and logs.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** State it in the allowance reason and CHANGELOG, and keep it named in the owner question `q-q8a1-hide-ids` notes.

### [Issue 9] [`design` tools.load_tool_module direct read] - Severity: Nit (checked fine)
*   **Affected Scope:** `tools.py:387`.
*   **Discrepancy Description:** Reviewer found it acceptable; no change.
*   ***AI Suggestion:*** DECLINE (no finding)
*   ***Justification:*** Nothing to fix; recorded.

### [Issue 10] [`evidence`: tests that pass on old code] - Severity: Minor
*   **Affected Scope:** `test_the_platform_secret_probe_names_a_secret_by_position_and_never_by_name` (renamed); `test_every_secret_provider_says_no_name_for_a_plain_word_and_imports_no_name_filter` (body changed); 63 new-test-name instances pass on main: 44 in `tests/test_q8a_live_overrides.py`, 18 in `tests/test_stage_names.py`, 1 in `tests/test_k3_pilot_env.py` (full list `new-tests-pass-on-main.txt`).
*   **Discrepancy Description:** A new or changed test that passes on old code either guards something unchanged (a control) or cannot fail for the case it names.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Class of Q8c-1 round 6 Issue 7: every such test needs a killing mutant or a stated control reason.
*   ***Proposed Edit:*** The builder adds one line per test (2 plus 63), saying which are control tests (they test behaviour that already holds on main and on the old head) and giving the mutant that kills each non-control one. Tests that exist only to pin text already on main may stay with the reason. Any with neither reason is rewritten so it fails on old code.

### [Issue 11] [`evidence`: set-up and timing] - Severity: Nit
*   **Affected Scope:** full pytest runs 1-2; timing test.
*   **Discrepancy Description:** The runner's database set-up failed twice and the pass came on run 3; the timing test failed 6 of 6.
*   ***AI Suggestion:*** DECLINE (not a head defect)
*   ***Justification:*** The set-up slips are recorded in the evidence file; the timing test is the known flake with its fix on `core/fix-timing-harness-flake`, which this package must not touch. The next evidence run starts its own database with the server environment set (as the common brief now says).

## Handoff counts
Accepted (PROPOSE FIX): 8 (Issues 1-8 and 10; Issue 1 type-level part ESCALATEd). Declined: 2 (Issues 9, 11). Contested: 0. Escalated: 1 (the `ConfigName` type, already open as `q-q8a1-hide-ids`, safe default stays). Round 9 C1 Major: verified fixed (ledger FIXED-VERIFIED by the planted-namespace probe on `f4acee28`). Remaining unaddressed: none beyond the owner question. Because the path is security with no cap, a batch-11 builder fixes Issues 1-8 and 10, then a fresh evidence run and two `egm:*` reviewers read the new head; the 11 f-string hits (Issue 2) must be traced before it is called clean.
