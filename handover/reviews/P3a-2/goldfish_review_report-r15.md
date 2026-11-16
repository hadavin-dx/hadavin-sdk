Status: resolved

# Goldfish Annotated Review Report

**Target:** P3a-2 batch 4b, head `c3b2efdb`, round 15 (SECURITY path, no round cap), branch `wip/cloud-p3a2-4b`.
**Inputs:** `p3a24b-design-r15.md` (0 Blocker, 4 Major, 4 Minor), `p3a24b-codebase-r15.md` (0 Blocker, 3 Major, 3 Minor, 1 Nit), previous report `goldfish_review_report-r14.md`, independent evidence `handover/evidence/P3a-2/c3b2efdb/RESULTS.md`.
**Mode:** automated, recommended option for every item. No severity changed. Nothing contested: each finding is checkable against the snapshot. Both reviewers agree no case remains where a lost session is reported as a file's own error.

## Prioritized Findings & AI Suggestions

### [Issue 1] [design D1, codebase C1] - Severity: Major
*   **Affected Scope:** `CHANGELOG.md:31` against `src/hadavin_sdk/store/migrate.py:1271-1275, 1303-1314`.
*   **Discrepancy:** line 31 says the schema of the run "must be owned by a role of the migration role family"; the default (switch OFF) accepts a schema owned outside the family at the start and refuses only an owner change during the run. Lines 29, 30, 41 are true. Same claim-versus-code gap as r14 Issue 2, fixed in one paragraph only.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** a rule an operator reads that the code does not keep is a defect; checkable at the two places.
*   ***Proposed Edit:*** rewrite line 31: managed objects must be family-owned; the schema of the run must not change owner during the run; the strict wording only beside the switch name. Add a test that reads every CHANGELOG sentence containing "must be owned" or "owned by a role of the migration role family" and compares it with the switch value (fails if the sentence is unconditional while the switch is OFF).

### [Issue 2] [design D2, codebase C2] - Severity: Major
*   **Affected Scope:** `migrate.py:1271-1275` (switch, comment), `tests/test_migration_verify.py:1368-1408`, `tests/test_migration_matrix.py:985`, `handover/questions-for-lead.md:1831`.
*   **Discrepancy:** OFF is the permissive default and a recorded deviation from the ticket's O8: a schema owned by non-family role X is accepted and X can drop the package's tables. The question file calls it "safe" and the strict reading "built and tested"; the only ON test replaces `verify` with a stub and calls `_state_problems(None, ...)`; the matrix says NOT BUILT for the strict cell; the comment "a plain switch ... with the tests that already cover it" overclaims; the switch is a source constant. OFF is the only value consistent with `PLAIN_MIGRATION_ROLE_SQL` (an administrator-owned schema with `GRANT CREATE` to the migration role), so ON would refuse the documented setup.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** the wording fix and a real-server cell are buildable now; the choice itself is not ours.
*   ***Proposed Edit:*** one real-server cell with the switch ON and a schema owned by a non-family role (exit 2, nothing kept) and a matching OFF cell (returns, ledger kept); reword `questions-for-lead.md:1831` to "permissive default; ticket line O8 unmet until edited"; correct the `migrate.py:1274` comment. Flipping the switch or editing the ticket line stays OWNER/LEAD-ONLY (`q-p3a2-o8-schema-owner`).

### [Issue 3] [design D3, D8; codebase C6, C7] - Severity: Major
*   **Affected Scope:** `tests/test_migration_verify_pg.py:712-733, :752-771, :913-946`, `store/postgres.py:146-148`, `CHANGELOG.md:15` and "Not proven yet", `ci.yml:41, :122`.
*   **Discrepancy:** the "visible skip" claim is false for two tests (a PG16 branch asserts `UndefinedObject` and returns, "UNRUN" only in the docstring; the full run's two skips are `tests/contracts/test_llm.py:95` and `tests/test_migration_verify_pg.py:922`). "Whichever step" is not shown for `connect()`: `SET TIME ZONE` runs under autocommit outside every wrapper and no test pins a saved 1 ms timeout at connect. CHANGELOG line 15 states a PG17 CI run as fact (only configured). The 25P04 text and the 3 s / 8 s timing are first-observation unknowns; the PG16 test uses a 150 ms timeout and a 0.6 s sleep.
*   ***AI Suggestion:*** PROPOSE FIX (the PG17 run itself is IMPOSSIBLE-NOW)
*   ***Justification:*** wording, skips and a connect statement are buildable; no PostgreSQL 17 exists here.
*   ***Proposed Edit:*** both PG16 branches become visible skips "UNRUN: PostgreSQL 17 only"; say "three tests need PostgreSQL 17"; state the exit-2 promise starts after connect, or move the connect statements inside the wrapper and pin it; line 15 becomes "is configured to run in CI on 17.10 (not yet seen)"; the 25P04 assertion matches the code with a message naming the observed text; widen the PG16 timing margin or assert on the outcome only.

### [Issue 4] [design D4, D5; codebase C3] - Severity: Major
*   **Affected Scope:** `tests/test_migration_matrix.py:855-862, 802-812, :1029, :1076, :1081-1091, :1613-1624, :1794`; `CHANGELOG.md:29`.
*   **Discrepancy:** one reason ("a map table lives in the schema of the run only") covers 40 empty cells; it is false for O13-O16 (CREATE on a schema, USAGE with grant option, default rights, `ALTER DEFAULT PRIVILEGES IN SCHEMA other`: writable against another schema) while O17 and O28/O29 are empty for different true reasons. The guard at `:1076` compares the table with the set it was derived from, so it cannot fail. `C8_EMPTY_BY_LOGIC` and `C13_EMPTY_BY_LOGIC` are checked by length only; C13 is a plain string. The CHANGELOG example "a table right cannot sit on a function" does not match.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** a wrong reason hides an unbuilt cell; the derived-equality guard proves nothing.
*   ***Proposed Edit:*** build O13-O16 under C10 or list them NOT BUILT with a true reason; own reason per pair; replace the derived-equality assert with an explicit list of empty effect ids; assert `set(C8_OBJECT) | set(C8_EMPTY_BY_LOGIC)` equals all effects, same for C13 with a dict of reasons; the count test asserts a reason text per group; correct the CHANGELOG example and counts.

### [Issue 5] [design D6, codebase C4] - Severity: Minor
*   **Affected Scope:** `tests/test_migration_verify_pg.py:862-893`, the 25P03 real-server test docstring, `tests/test_migration_verify.py:1404-1408`, mutants V88, V92-V99, V101, V102.
*   **Discrepancy:** killers are bare asserts showing a parameter id ("assert True is False"); V102 prints a tuple only. The 25P03 real-server test docstring says "Killed by V88 and V89" but kills neither (the usable-connection check catches it); only the unit stand-ins kill them.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** a kill that does not name its fault proves little; the docstring claim is false.
*   ***Proposed Edit:*** messages naming the planted fault (`f"{code} must not be a file's own error"`); correct the docstring; the mutant text states which tests discriminate.

### [Issue 6] [design D7, codebase C5] - Severity: Minor
*   **Affected Scope:** `tests/test_migration_matrix.py:3044-3073` (third-role cell), C8, C9, C13, variant O cells; `tests/migrate_mutants.py` (V100 only for C6b); `BUILDER-notes.md:15-16`.
*   **Discrepancy:** "rows are controls" holds for the C6b strengthening only; the new third-role-on-a-family-table real-server cell, C8, C9, C13 and variant O have no mutant; none plants a wrong role or right; the third-role test ends in the weak substring `"runs" in text`; the test at `:3045` says it has a paired X01t control that is not in it. 12 of 19 new tests pass on old code and each needs a reason or killer.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** a test that cannot fail on its own regression is not a check.
*   ***Proposed Edit:*** one mutant each (remove the O1 third-role refusal; C13; C8; C9; variant O) with the real test as killer; quote `f"{schema}.runs"`; fix the docstring; one line per new-test-passes-on-old-code naming its killing mutant or true reason.

### [Issue 7] [evidence] - closed by evidence
*   Full pytest 12347 passed, 2 skipped, 29 deselected, exit 0 (the first run's single dblink failure came from the runner's own server settings and did not recur); `migrate_mutants` batches 103 + 88 + 98 + 97 all killed; `migration_numbers_mutants` 40 of 40; `stage_mutants` 37 of 37; ruff, format, bandit, scan_repo, gitleaks exit 0. Fail-before: 26 failed on old source (rules 2, verify 5, verify_pg 19); of 19 new test functions 7 fail on old code and 12 pass (reasons owed: groups 5 and 6). Hostile inputs: backend killed at every step gives exit-2 "kept nothing", ledger 0; 25P03 live gives ConfigError, ledger 0; classifier verified; O8 owner change refused in all calls.
*   ***AI Suggestion:*** none (recorded)

## Escalated / not fixable here
- **OWNER/LEAD: `q-p3a2-o8-schema-owner`** (flip the O8 switch or edit the ticket line). Already in the question file; this round adds an OWNER-ONLY ledger row, since earlier it was only mentioned inside a Major row.
- **IMPOSSIBLE-NOW: the PostgreSQL 17 run** (25P04, saved `transaction_timeout` at connect, three tests). No PG17 here. Next step: a CI run on postgres 17.10 before the lead merges.

## Handoff
- Findings in: design 4 Major + 4 Minor; codebase 3 Major + 3 Minor + 1 Nit; merged into 7 groups.
- PROPOSE FIX: 6 groups (Major 1-4, Minor 5-6). CONTEST 0. ESCALATE 1 (owner), IMPOSSIBLE-NOW 1 (PG17). DECLINE 0 (the Nit C7 is folded into group 3). Closed by evidence: 1.
- Applied edits: none to code by this skill. Remaining unaddressed: groups 1-6 (OPEN) until batch 5 is built, evidenced and reviewed. No Blocker.
- **Who fixes it:** one batch-5 builder (general-purpose, Sonnet) on `core/p3a2-b5` from `c3b2efdb`, pushing to `wip/cloud-p3a2-5`. Files: `CHANGELOG.md`, `src/hadavin_sdk/store/migrate.py` (comment, switch note), `src/hadavin_sdk/store/postgres.py` (connect wording or wrapper), `tests/test_migration_verify.py`, `tests/test_migration_verify_pg.py`, `tests/test_migration_matrix.py`, `tests/migrate_mutants.py`, `handover/questions-for-lead.md`, builder notes. Order: 4 (decides the cell list), 2, 3, 1, 6, 5. Gates once on the final head; own Postgres 16 with PGHOST and PGPORT in the server environment. Security path: no round cap.
