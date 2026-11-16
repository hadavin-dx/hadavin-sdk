Status: resolved

# Goldfish Annotated Review Report (round 19)

**Target:** P3a-2 batch 8, branch `wip/cloud-p3a2-b8`, head `6a25ae5d` (previous reviewed head `aac26d60`). Files: `handover/reviews/P3a-2/p3a2b8-design-r19.md` (0 Blocker, 0 Major, Minor D1-D3, Nits D4-D6) and `p3a2b8-codebase-r19.md` (0 Blocker, 0 Major, Minor C1-C3, Nits C4-C5); full files.
**Path:** SECURITY / least privilege (no round cap). Automated mode, recommended option for every item, nothing yielded.
**Evidence read:** `handover/evidence/P3a-2/6a25ae5d/RESULTS.md` (independent runner). Facts:
- ruff check, ruff format --check, bandit -ll, `tools/scan_repo.py` and gitleaks exit 0.
- migrate mutants 148, 88, 98 and 97 all killed; number mutants 40 of 40; stage mutants 37 of 37; V130-V148 plus V116, V117, V122 and V125 (23 rows) all KILLED. The CHANGELOG matrix numbers equal the brief.
- Full pytest final run: 1 failed, 12480 passed, 4 skipped, 29 deselected, exit 1. The one failure is `tests/demo_askdata/test_validate_harm.py` `[dblink-connect]`: it needs the fixed socket `/var/run/postgresql/.s.PGSQL.5432`, which the runner's own Postgres does not provide. Run alone three times: 1 failed, 252 passed every time. This is a runner environment effect, not a change of this batch, but it is not yet proven so (see group 6).
- First full run: 3 failed. Two were the runner's own slip (its first Postgres lacked `max_prepared_transactions`); fixed, those tests passed 3 of 3 afterwards.
- Timing test `test_the_timing_harness_flags_a_quadratic_stand_in`: failed 3 of 3 on the head and 3 of 3 on main `2a8c2aac` (about 0.6 s). Recorded only. Do not touch it.
- Fail-before on `aac26d60`: of the 47 ids 38 failed and 9 passed; the three whole files gave 39 failed, 221 passed, 3 skipped. The 9 passing are the same nine as the builder's table. Open: which test is the 39th old-source failure (not examined).
- Skipped (4): `tests/contracts/test_llm.py:95` and three PostgreSQL 17 tests (`tests/test_migration_verify_pg.py` 908, 961, 1144). Not run (impossible now): PostgreSQL 17, Python 3.12, Semgrep, zizmor, Trivy, pip-audit.
**Reviewer result:** no Blocker, no Major; no readable secret, no regression against main. Reviewer severities unchanged. No finding is contested. Duplicates merged: C1 = D1, C2 = D2, C3 = D3, C4 = D6.

## Prioritized Findings & AI Suggestions

### Group 1 [codebase C1, design D1] - Severity: Minor
*   **Affected Scope:** `src/hadavin_sdk/store/migrate.py:1668-1685` (step 8), `cli.py:84-85`; CHANGELOG sentence "after the connection exists".
*   **Discrepancy Description:** Step 8 opens a new connection (sign-in included) inside the `try`; `raise _after_commit(...) from e` keeps the driver error (host and user words) as `__cause__`. Printed text is class name only, but `HADAVIN_DEBUG=1` prints the chain and a log handler sees it. The CHANGELOG scope is wrong for this site.
*   **Rationale:** Same class as r18 group 1: a claim stronger than the proof, one channel left open.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Close it at the choke point: hold the class name, leave the `except`, raise outside, so `__cause__` and `__context__` are empty for a connection-time failure. Test with an injected OperationalError on the second connection, checking both channels and the formatted traceback; one mutant; correct the CHANGELOG.
*   ***Proposed Edit:***
    *   Location: `store/migrate.py`, `tests/test_migration_verify_pg.py` or `test_sign_in_channels.py`, `tests/migrate_mutants.py`, CHANGELOG.
    *   Change: as above.

### Group 2 [codebase C2, design D2] - Severity: Minor
*   **Affected Scope:** the about 11 later `raise ... from e` sites in `migrate.py` (1295, 1301, 1619, 1622, 1626, 1657, 1662, 1663, 1667; older 380, 507, 1124); `:1625` and `:1661` print `e.diag.message_primary`; test `tests/test_migration_postgres.py:1256`.
*   **Discrepancy Description:** The sites keep `__cause__`, which can hold a DETAIL line with row values. It is not printed, but the CHANGELOG must not say "never kept". No written policy says which sites may chain.
*   **Rationale:** An unwritten rule lets the next change chain a connection-time error.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Write the rule once in the CHANGELOG: statement-time errors after the connection exists may keep `__cause__` (kept for debugging, never printed, `HADAVIN_DEBUG=1` prints it); connection-time errors never chain. Check each of the 11 sites against it, drop the chain at 1622, 1657 and 1662 if they can carry row values, read `_label`, and add a test that walks every `raise ... from` in `migrate.py` against the list.
*   ***Proposed Edit:***
    *   Location: `store/migrate.py`, CHANGELOG, one new test.
    *   Change: as above.

### Group 3 [codebase C3, design D3] - Severity: Minor
*   **Affected Scope:** `cli.py:202-217` and `:311-319`; the widened `except Exception` in `store/auth_aws.py`.
*   **Discrepancy Description:** A transient credential failure (token request OSError, throttle, IMDS or STS timeout) is now a `SignInError` (ConfigError): the kill-switch stop/reset prints "refused" with exit 2 instead of "NOT set, nothing changed, run again" with exit 4, and `tick` exits 2 instead of 4. A widening, not a regression against main.
*   **Rationale:** A retryable fault must stay retryable; exit 2 tells an operator the config is wrong.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Map timeout and connection-class names to `StoreUnavailable` at `build()` (class name only, no library text), keep the rest as `SignInError`; or at minimum print the "NOT set" sentence for `SignInError` on the kill-switch path. Test both exits with injected `OSError` and `RuntimeError`; one mutant; CHANGELOG states the mapping.
*   ***Proposed Edit:***
    *   Location: `store/auth_aws.py` or `store/postgres.py` build, `cli.py`, tests, mutants, CHANGELOG.
    *   Change: as above.

### Group 4 [design D4] - Severity: Nit
*   **Affected Scope:** `tests/test_migration_verify_pg.py`, docstring of `test_a_refused_connection_keeps_no_driver_error_on_either_channel`.
*   **Discrepancy Description:** The docstring names V131; the test is the killer of V133.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** One-word fix, worth it because the batch's rule is "killed for the named reason". Check the other docstrings against the runner's table (V130-V148).
*   ***Proposed Edit:***
    *   Location: that docstring.
    *   Change: V131 to V133; recheck all mutant names in docstrings.

### Group 5 [design D5] - Severity: Nit
*   **Affected Scope:** killers of V132, V133, V146 (need a server).
*   **Discrepancy Description:** Read, not run, by the reviewer.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Now answered by the independent run: V130-V148 plus V116, V117, V122 and V125, 23 rows, all KILLED (`evidence/P3a-2/6a25ae5d/RESULTS.md`). The builder records that closure in the batch-9 notes; the batch-9 evidence run repeats it.
*   ***Proposed Edit:***
    *   Location: batch-9 notes.
    *   Change: cite the evidence file.

### Group 6 [codebase C4, design D6, evidence] - Severity: Nit
*   **Affected Scope:** `tests/demo_askdata/test_validate_harm.py` `[copy-program]` "Broken pipe" and `[dblink-connect]`.
*   **Discrepancy Description:** The builder saw a "Broken pipe" in `[copy-program]`; the runner saw none in any log, but the full run failed `[dblink-connect]` (fixed socket missing). Neither is tied to the delta; neither is explained or proven unrelated.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Fix, do not defer: run the file on a Postgres that listens on the fixed socket, and on main at `2a8c2aac` under the same conditions; show it passes or fails identically on both; repeat the copy-program case at least 10 times on head and main and report counts; if a real flake exists, write its cause. Do not touch the timing test.
*   ***Proposed Edit:***
    *   Location: batch-9 evidence notes.
    *   Change: measured counts on head and main, written reason.

### Group 7 [codebase C5] - Severity: Nit
*   **Affected Scope:** `tests/test_sign_in_channels.py:30`.
*   **Discrepancy Description:** Imports a helper from another test module.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Move it to `tests/fixtures/` (or a shared helper module the repo already uses), as other tests do; the move is cheap and removes a hidden coupling.
*   ***Proposed Edit:***
    *   Location: that file and the helper's origin.
    *   Change: move, update imports.

### Group 8 [design "not checked" note] - Severity: Nit
*   **Affected Scope:** `store/postgres.py:236` (`conninfo_to_dict` at build, before the `try`).
*   **Discrepancy Description:** A malformed DSN can raise a raw ProgrammingError that quotes part of the DSN. Unchanged from main; flagged for the next reviewer.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Same class as the sign-in channel (library text with config words). Reproduce with a made-up malformed DSN; if the text is printed, convert at that choke point with the class name only; else write the proof.
*   ***Proposed Edit:***
    *   Location: `store/postgres.py:236`, test, mutant.
    *   Change: as above.

### Group 9 [evidence] - Severity: Minor
*   **Affected Scope:** the independent evidence for batch 8.
*   **Discrepancy Description:** Open points: the 39th old-source failure over the three whole files is not identified; the timing test fails on both heads; the Postgres 17 tests and Python 3.12 cannot run here.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Batch 9 names the 39th failing test and says why it fails on old source; the independent runner repeats full pytest on the batch-9 head with `max_prepared_transactions` set and the fixed socket available. Python 3.12 and PG17 stay IMPOSSIBLE-NOW and are listed as such.
*   ***Proposed Edit:***
    *   Location: batch-9 notes, evidence folder.
    *   Change: as above.

### Group 10 [owner item O8] - Severity: Minor (owner decision)
*   **Affected Scope:** `q-p3a2-o8-schema-owner`.
*   **Discrepancy Description:** Untouched and OFF by owner decision; both reviewers confirm.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** The decision is the owner's, outside every file the reviewers could read.
*   ***Proposed Edit:***
    *   Location: none.
    *   Change: stays OFF and OWNER-ONLY.

## Handoff

*   Accepted fixes (PROPOSE FIX): 9 groups (Minor groups 1, 2, 3 and 9; Nit groups 4 to 8), covering all 3 Minor and 3 Nit items of the design review and all 3 Minor and 2 Nit items of the codebase review.
*   Contested: 0.
*   Escalated: 1 (group 10, O8, OWNER-ONLY).
*   Declined: 0.
*   Remaining unaddressed: all of the above until batch 9 lands. No Blocker or Major is open; the batch-8 gates are green except one fixed-socket failure that the batch-9 builder must prove unrelated. Last round only if a fresh pass after batch 9 finds nothing real.

## Who fixes it

One batch-9 builder on a new branch `core/p3a2-b9` from `6a25ae5d`, pushing to `wip/cloud-p3a2-b9`. Order: groups 1, 2, 3, then 8, 6, 9, 4, 5, 7. Method per bug: name the class, fix at the shared choke point, grep siblings, show each new test failing on `6a25ae5d`, one mutant per fix with a killer that fails for the named reason, final-head full suite with the fixed socket and all four migrate mutant sets plus the number and stage mutants, CHANGELOG counts recomputed, one written reason per test that passes on old code. An independent evidence run on the batch-9 head is a gate. O8 stays OFF. The builder does not touch `test_the_timing_harness_flags_a_quadratic_stand_in`.
