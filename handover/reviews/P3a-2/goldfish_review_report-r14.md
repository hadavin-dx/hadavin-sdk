Status: resolved

# Goldfish Annotated Review Report (P3a-2 batch 3e, round 14)

**Target:** branch `wip/cloud-p3a2-3e`, head `f1ec83a84f07a7515d674bdf74f90d91eb2ab296` (delta against the 3d head). SECURITY path (migrate least privilege), no round cap. No person was available: recommended option for every item. Reviews (read only, nothing run): `p3a2b3e-design-r14.md` (0 Blocker, 5 Major D1-D5, 3 Nit D6-D8) and `p3a2b3e-codebase-r14.md` (0 Blocker, 7 Major D1-D7, 3 Minor, 1 Nit). Independent evidence: `handover/evidence/P3a-2/f1ec83a8/RESULTS.md`.

**Evidence status (first).** ruff, format, bandit, `scan_repo`, gitleaks exit 0; `stage_mutants` 37 of 37; migrate mutants batches 1-4: 87, 88, 98, 97 killed (V86, V87 killed); `migration_numbers_mutants` 40 of 40. NOT clean: (a) full pytest exit 1: 2 failed, 12125 passed, 1 skipped; both failures are in `tests/demo_askdata/test_validate_harm.py`, outside the diff, caused by the evidence environment (a server not the runner's wrote `/tmp/askdata_p2_copy.csv`; the dblink test connects to the fixed socket of the other server). Not re-run alone: the batch-4 builder re-runs that file under `unshare -m`. (b) PG17: NOT RUN (only PostgreSQL 16.15 here); the CI job pins `postgres:17.10` but has not been observed. (c) the CI install `uv sync --locked --no-build` fails here; installed without `--no-build`. (d) timing flake: head 1 fail 1 fail 1 pass, main fail x3 (known; fix on `core/fix-timing-harness-flake`; not touched). (e) fail-before: 12 tests fail on the old source (X28 x3, 8 lost-connection cells, the file-run lost-connection test, the bug-before-commit test); 433 of 444 new test ids pass on old code (430 in `test_migration_matrix.py`). (f) a marker on `pg_roles` still gives a raw OperationalError (exit 3); the statement was not traced: UNCHECKED, assigned to batch 4 (Issue 7). (g) CLI exit numbers read in `cli.py`, not run. Evidence confirms: only X28 is refused with no role argument; X17, X18, X19, X31, X32, X33, X36 return normally with no roles and give ConfigError (exit 2) with roles; X01t, X11, X12, O24 return in both variants; K8 probes: in the open exit 2, dynamic SQL raw InsufficientPrivilege (exit 3 by the CLI rule), after CREATE exit 2.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`codebase-details` D1 + `design` D3] - Severity: Major
*   **Affected Scope:** `src/hadavin_sdk/store/migrate.py:1205-1215` (`_NOT_A_FILES_OWN_ERROR`, `_is_a_files_own_error`), `:1588-1604`; CHANGELOG "three calls".
*   **Discrepancy Description:** Every SQLSTATE except classes 08, 53, 57, 58, XX is treated as the file's own error and re-raised raw (exit 3). PG17 `transaction_timeout` ends the session with 25P04 and the idle-in-transaction timeout with 25P03 (class 25, not excluded; from the reviewers' memory, unchecked on a server). A long file outlasting a saved short timeout gives exit 3 where the CHANGELOG says exit 2. The PG17 test sets 1 ms so it fires before any file runs.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Fits the class "driver or server ends the session, not the file". Fix at the one classifier.
*   ***Proposed Edit:*** An error counts as the file's own only if the connection is still usable (not closed, transaction status in error); also add class 25 codes 25P03, 25P04 to the excluded set. Add 25P03, 25P04 to the unit pins, a mutant on the tuple and one on the usability check, and a PG17 case where the timeout strikes inside a `pg_sleep` file (written now, marked as PG17-only with a visible skip, and listed UNRUN in CHANGELOG until the CI job runs it). Verify the SQLSTATE from the PG16 `errcodes.txt` shipped in the server install (25P03 exists there) and state what could not be checked.

### [Issue 2] [`codebase-details` D2 + `design` D4] - Severity: Major
*   **Affected Scope:** CHANGELOG baseline bullet; `migration_verify.py:13-27`; `migrate.py:1190-1194, :1280-1290` (`_state_problems`); `tests/test_migration_matrix.py:1667-1687`; ticket 3.3 O8.
*   **Discrepancy Description:** The text says the schema of the run must be owned by the family. The code drops every foreign-owner problem for the schema whose owner equals the owner at the start, so an administrator-owned schema passes steps 2, 6, 8; only a change of owner during the run is refused. The E28-schema no-roles test pins a normal return.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The claim and the code disagree; either may be right. Which one is a product choice: the safe default is to say what the code does.
*   ***Proposed Edit:*** Batch 4 rewrites CHANGELOG, `migration_verify.py` docstring and the test text to "the owner of the schema must not change during the run; a schema owned by a role outside the family at the start is accepted", and keeps the enforcement option behind a clearly named constant, off, with its tests written and marked as the alternative. The choice goes to `questions-for-lead.md` as `q-p3a2-o8-schema-owner` (already open: update it with this finding and the safe default).

### [Issue 3] [`codebase-details` D3 + `design` D1] - Severity: Major
*   **Affected Scope:** CHANGELOG line 29 "Not proven yet" paragraph.
*   **Discrepancy Description:** Stale: "18 kinds ... brought in 6 ways", "nine kinds" of pre-existing states, and a not-covered list that 3e builds (groups with rights, SECURITY DEFINER, role switch, move-and-recreate, extension member, temporary table, foreign servers, languages, tablespaces, parameters, K2-K12). The head builds 27 effects x 10 carriers, 36 pre-existing effects, C6b, C8, C9, C13, K5-K8. No PG17 note by the matrix claim; three limits unstated.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Shipped text contradicts the code and understates coverage.
*   ***Proposed Edit:*** Rewrite from the numbers the count test prints (computed, Issue 4); name what is still not built (Issue 4 list) and the three unstated limits; PG17 labelled UNRUN beside the matrix claim; "every step" softened to the named list (Issue 7).

### [Issue 4] [`codebase-details` D4, D5, D6 + `design` D5] - Severity: Major
*   **Affected Scope:** `tests/test_migration_matrix.py:840-890` (`O_SERVER_REFUSED_EFFECTS`, `O_EMPTY_BY_LOGIC`, `O_NOT_BUILT_CARRIERS = {}`, `O_NOT_BUILT_CONTROLS = {}`, count test), `:1181`, `_WRITTEN_IN_THE_OPEN`; `migrate.py:283-299` (`check_grants`); ticket 7.4 "Counting".
*   **Discrepancy Description:** (D4) Table 1 is wrong for E22 (a plain role can `lo_create` and grant on its own large object; ticket fact 28, 5.6, 7.9 "E22 x C2" must fail on 4d328e3d) and E17, E18, E19, E21, E28-schema are called unbuildable though ticket 7.4 allows variants (O)/(C) ((T)/(U)); only (P) is built. (D5) The three tables hide what is missing: C8, C9, C13 carry 2, 2, 4 cells instead of every effect not empty by logic; both "not built" dicts are `{}`; the 18 no-role cells and the C10 "named + no-roles -> iii" cells (5 effects) are in no table; counts (504, 521) are literals; `O_EMPTY_BY_LOGIC` is a string. (D6) Cells refused at step 0 by the text rules (O13-O22; C3 and C11 added to `_WRITTEN_IN_THE_OPEN`) are counted as cells although nothing ran. The design reviewer's D5 adds: table 1 is checked only by id coverage, subtracted from nothing.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The ticket's count test must compute the numbers from the tables and assert equality; an honest "not built" list is better than a larger number.
*   ***Proposed Edit:*** Real tables as dicts id -> reason (empty by logic, server refuses, not built, pinned/no-roles); the count test computes cells = effects x carriers x variants minus the tables and asserts equality with the printed total (no literals). Build E22 for C2-C7 with `lo_create` inside the file; build E17/E18/E19/E21 under (O) and (C) (and (T)/(U) for E19-E21) or list each as not built with a reason; C8, C9, C13 x remaining effects built or listed. Record which cells end at step 0 and assert a floor on the rest; put the effect for C3 and C11 in a form the text rules cannot read; sensitivity check that C11's temporary table exists when `verify` reads. Print "built / empty by logic / server-refused / not built / step-0 refused" counts in the test output.

### [Issue 5] [`design` D2] - Severity: Major
*   **Affected Scope:** `tests/test_migration_matrix.py:2150-2154, :2365-2366, :856, :352, :686-725`; ticket O1, E01 "third role"; `migration_verify.py:1092-1093`.
*   **Discrepancy Description:** The X01t reason and label misstate the promise. The ticket promises a third-role right on a FAMILY-OWNED object in the schema of the run; X01t creates the table as the superuser, so it is not family-owned. The promised family-owned third-role cell is covered only by a pure `_judge` test (:352), not run against a real server.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Wrong reason plus a promised case not run on a server.
*   ***Proposed Edit:*** Add the real-server cell (family-owned table, third role holds a right, unnamed role) and pin it refused by O1; reword X01t to "a table owned by a role outside the family (ticket 1.4): not judged"; X11 "not judged (3.4 line 3)"; X12 "nobody may call it"; keep O24 under C10 (codebase D9 same fix).

### [Issue 6] [`codebase-details` D7] - Severity: Major
*   **Affected Scope:** `tests/test_migration_matrix.py:947-969` (C6b cells).
*   **Discrepancy Description:** The only assertion is `pytest.raises(AppliedNotVerifiedError)`; ticket 7.1(ii) requires each excess named with its kind in the problem lines; no no-op control (C5 has one). An unrelated finding (the pre-made `hadavin_test_q` table or the trigger function) passes all 54 cells.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A cell that cannot tell a right finding from a wrong one proves nothing.
*   ***Proposed Edit:*** Assert the effect's role, object and kind appear in the error text or the `Problem` list; add a no-op control effect that returns normally; mutant that swaps the named object.

### [Issue 7] [`codebase-details` D10, D8, evidence f, K8] - Severity: Minor
*   **Affected Scope:** `migrate.py:1457, :1524-1526, :1554-1562`; `tests/test_migration_verify_pg.py`; `test_control_k8_...`; evidence item (f).
*   **Discrepancy Description:** No mutant kills removing `running_a_file = False` (an own-class error at step 4, e.g. 42704 from `_apply_grants`, would stay raw); no mutant plants the contents of `_NOT_A_FILES_OWN_ERROR`; a lost connection at `SET CONSTRAINTS` (step 5) gets "a deferred check or trigger failed..." (wrong text; exit 2 and nothing kept hold); "every step" overstated (8 functions covered; not version read, identity read, ledger CREATE/SELECT/INSERT, step 5); `connect()` and its `SET TIME ZONE` outside the `try` (saved `transaction_timeout` 1 ms could still give exit 3); on PG16 the new test only checks the setting is unknown and then passes silently; the `pg_roles` marker raw OperationalError (exit 3) is untraced; K8 "cannot end in (iii)" untested for "group owns the schema of the run" (O8 accepts it when the migration role belongs to the group).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Each is a gap in tests or wording at the same choke point; the pg_roles one may be a real hole.
*   ***Proposed Edit:*** Killers for the reset and the tuple; the step-5 message fixed; cover the remaining steps or name the list; move `connect()` inside the wrapper or pin the outcome; PG16 branch a visible skip/xfail with a name; trace the `pg_roles` statement and fix or give the reason; probe K8 with the group owning the schema, pin (iii) if it returns, else record the measurement.

### [Issue 8] [`codebase-details` D9, D11 + `design` D6-D8 + evidence] - Severity: Nit
*   **Affected Scope:** table-3 wording (`:856, :2363-2374`), B5 pin text (`:2333-2341, :2380-2393, :2436-2443`: "refused for ever" overstated, the 24 "returned" cells of 72 counted as 18), weak guards (`test_direction_2_...` last assert cannot fail; `_forms_missing_from` for `has {right}` satisfied by other sentences; V84 killed by one assert only; direction 2 comment "every object of the database" though tablespaces/parameters are server-wide), PG17 note, 433 tests that pass on old code.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Cheap and in the same files.
*   ***Proposed Edit:*** Fix the wording and counts; make the direction-2 assert able to fail (test it on a planted extra); real planted fault for the `has {right}` forms; state the rule for the 433 (a matrix cell is a control by table, one line per table row, not per test; the 12 that fail on old code and the 11 non-matrix tests get one line each); recompute the 504 and 521 text from the count test.

## Handoff counts
Accepted (PROPOSE FIX): 8 (Issues 1-8, grouping design D1-D8 and codebase D1-D11). Contested: 0. Escalated: 1 (Issue 2, the schema-owner choice, goes to the lead with the safe default; the builder implements the reword now). Declined: 0. Remaining unaddressed: none. Severity unchanged from the reviews. Items not verifiable here: 25P04/25P03 on PG17 (UNRUN, IMPOSSIBLE-NOW until a PG17 CI run), the two environment test failures (not the diff).

## Who fixes it
One batch-4 builder on a new branch `core/p3a2-4b` from `f1ec83a8`, plain push to `wip/cloud-p3a2-4`. Files: `src/hadavin_sdk/store/migrate.py`, `src/hadavin_sdk/store/migration_verify.py`, the oracle test helper, `tests/test_migration_matrix.py`, `tests/test_migration_verify.py`, `tests/test_migration_verify_pg.py`, `tests/migrate_mutants.py`, `CHANGELOG.md`, builder notes. Gates once on the final head as in earlier P3a-2 batches; the dblink and copy-to-file demo tests re-run alone under `unshare -m`.
