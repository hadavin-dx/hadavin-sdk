Status: resolved

# Goldfish Annotated Review Report: P3a-2 batch 5 (round 16 of the resolve series)

**Target:** branch `wip/cloud-p3a2-b5`, head `989c02a3` (reviewed against previous head `c3b2efdb`). Security and least-privilege path: no round cap.
**Inputs read in full:** `p3a2b5-design-r15.md` (0 Blocker, 2 Major, 4 Minor, 2 Nit, 1 escalation), `p3a2b5-codebase-r15.md` (0 Blocker, 0 Major, 7 Minor M1-M7, 6 Nit), `handover/evidence/P3a-2/989c02a3/RESULTS.md`, previous report `goldfish_review_report-r15.md`.
**Mode:** automated, recommended option for every item, nobody to ask. Severities are the reviewers' and are not changed.

## Evidence on head 989c02a3 (independent run; nothing here is the builder's word)
- Full pytest, run alone: 12363 passed, 4 skipped, 29 deselected, exit 0. The runner's first two full runs were invalid (shared server; wrong folder) and are not counted.
- migrate_mutants: 112, 88, 98 and 97 killed; V102 to V112 all killed. migration_numbers_mutants 40 of 40. stage_mutants 37 of 37.
- ruff check, ruff format --check, bandit -ll, tools/scan_repo.py, gitleaks: all exit 0.
- Fail-before (old code c3b2efdb): 3 failed, 1490 passed. 18 new test ids: 16 pass on old code, 2 fail (the two CHANGELOG tests). The third old-code failure (prepared-transaction test) fails only on a server with `max_prepared_transactions=0`; ci.yml sets no such option.
- Not run, IMPOSSIBLE-NOW: the 3 PostgreSQL 17-only tests (this box has Postgres 16 only; CI is configured for 17.10).
- Probes of migrate's own results: O8 switch OFF with an outsider-owned schema RETURNS (5 or 1 versions), ON REFUSES. O13 and O14 with no roles argument RETURN 6 versions (with a runtime role they raise). O15 and O16 raise. A third role with SELECT, INSERT or UPDATE on `runs` raises. A lost session before `_apply_grants` RETURNS 5 versions; lost before the lock, or inside a file, raises (57P01).
- Both reviewers read without this file, so their "found fine" lines rest on reading; the evidence confirms the counts (580 cells, 32 empty, 548 built, 32 stop at step 0, 516 reach the data checks) and the kills.

## Prioritized findings (one issue per root cause; ids are group numbers)

### [Group 1] [`design Major A`] - Severity: Major - O17 is not empty by logic
* **Scope:** `tests/test_migration_matrix.py:878` and `:722`, `CHANGELOG.md:29`.
* **Discrepancy:** the reason "this default right names no schema" is false. `ALTER DEFAULT PRIVILEGES IN SCHEMA {o} GRANT USAGE ON SEQUENCES TO PUBLIC` is valid: the PUBLIC twin of the O16 cell. CHANGELOG says "cannot exist by logic". Same false-reason class as r15-report Issue 4.
* ***AI Suggestion:*** PROPOSE FIX
* ***Justification:*** Checked: the reasoning needs no run, the statement is standard PostgreSQL. A false empty-by-logic reason hides an untested route for a least-privilege hole (PUBLIC can use every sequence created later in the schema).
* ***Proposed Edit:*** Build O17 under C10 with the IN SCHEMA form (kind default_for_everyone, new schema `<schema>_o`, real connection, both variants), check what verify says, make migrate refuse it if it returns. Fix the empty counts (32 and 548) and the CHANGELOG sentence from the measured numbers. One mutant that removes the refusal. Grep the sibling effects O1-O29 for the same "names no schema" reasoning and re-examine every empty-by-logic reason with a real server statement, not by thought.

### [Group 2] [`design Major B`, `codebase M1`] - Severity: Major - O13-O15 under C8 declared impossible; a schema can be an extension member
* **Scope:** `tests/test_migration_matrix.py:1660-1671` (C8_EMPTY_BY_LOGIC), V106, ticket line 400.
* **Discrepancy:** reason "none of them is an object that can be an extension member" is false: `ALTER EXTENSION x ADD SCHEMA s` is valid. C8 exists to test "make the object an extension member so verify skips it"; V106 shows verify skips extension rows. CREATE on the run schema with the schema made a member is that evasion, unbuilt.
* ***AI Suggestion:*** PROPOSE FIX
* ***Justification:*** Same class as Group 1; the ticket says membership is computed for every kind except columns.
* ***Proposed Edit:*** Build O13, O14, O15 x C8 on a real server (made-up extension; if creating one is impossible in CI, say so with the measured error, never by reasoning). Record the outcome (returns or refuses) as the other cells do; if it returns, fix at the choke point in migration_verify (an extension row must not hide a CREATE right on the run schema). Mutant per fix. Large objects and default rights stay empty (reviewer agrees). Re-derive every C8 and C13 empty reason the same way.

### [Group 3] [`design Minor`, `codebase M7`] - Severity: Minor - connect() hole stated, not closed; CHANGELOG claims more than the pin shows
* **Scope:** `store/postgres.py:147-151`, `store/migrate.py:1485` and `:1637`, `CHANGELOG.md:18` and `:25`.
* **Discrepancy:** both `connect(...)` calls are the `with` expression outside the inner `except psycopg.Error` (`:1620`), so a driver error from `SET TIME ZONE` at the first connect probably surfaces raw (the crash exit the CHANGELOG says "never" happens). "At whichever step after the connection is made" claims more than the single connect test pins. Related evidence: a lost session before `_apply_grants` RETURNS 5 versions (not a refusal), where other points raise.
* ***AI Suggestion:*** PROPOSE FIX
* ***Justification:*** A stated-but-open hole is a defect under the fix-don't-defer rule; the lost-session return needs a measured explanation or a fix.
* ***Proposed Edit:*** Wrap both connect calls at the shared place (one helper that turns a driver error during connect into the same refusal with nothing kept); measure by a test that makes `SET TIME ZONE` fail at the first and the eighth connect; show it failing on 989c02a3. For the lost session before `_apply_grants`: decide by reading `_apply_grants` whether returning is correct (the grants may be already applied) and write the true sentence, or refuse. Reword CHANGELOG lines 18 and 25 to what the tests pin.

### [Group 4] [`design Minor`] - Severity: Minor - one-statement pin is mock-level
* **Scope:** `tests/test_migration_verify.py` about 1409-1431; V112.
* **Discrepancy:** the pin monkeypatches `pg.psycopg.connect` and counts `conn.execute`; it misses `conn.cursor()`, connection options such as `-c`, and the IAM branch. V112 plants only the visible form.
* ***AI Suggestion:*** PROPOSE FIX
* ***Proposed Edit:*** Add a real-server pin (read the statements the server logged, or count with a connection-level hook) plus pins for `cursor()`, the options string and the IAM branch; one mutant per form.

### [Group 5] [`codebase M4`, `M5`, `design Minor`, Nit] - Severity: Minor - timing and sqlstate assertions
* **Scope:** `tests/test_migration_verify_pg.py` about 958-966 and the 25P03 test; docstring `:716`.
* **Discrepancy:** the 25P04 assertion accepts "25P04", "TransactionTimeout" or "OperationalError" (any lost connection matches); the 25P03 test fails if a pause over the 200 ms limit hits between two statements inside the transaction; one docstring is stale.
* ***AI Suggestion:*** PROPOSE FIX
* ***Justification:*** The 25P04 narrowing needs a PG17 observation: IMPOSSIBLE-NOW on this box (CI only). Stated, with the next step.
* ***Proposed Edit:*** 25P03: assert on the outcome only, or raise limit and sleep together. 25P04: keep the tests as visible skips, narrow to "25P04" now (it is the sqlstate the server sends; the reviewer says the other two words are nearly dead) and write in the ledger that the first CI run on 17.10 must confirm. Fix the stale docstring.

### [Group 6] [`codebase M2`] - Severity: Minor - false V101 kill claim
* **Scope:** docstring of `test_o8_a_schema_owned_outside_the_family_...`.
* **Discrepancy:** it says "Killed by V101 (switch ON by default)" but the test patches the switch, so it cannot detect V101; V101's only killer is `test_the_strict_reading_of_rule_o8_is_off_by_default`.
* ***AI Suggestion:*** PROPOSE FIX
* ***Proposed Edit:*** Remove the V101 mention. Grep every docstring and comment in the delta for a "killed by Vnnn" claim and check each against the mutant runner's killer list (the runner logs the killing test).

### [Group 7] [`codebase M3`, Nits, `design Nits`] - Severity: Minor (Nit parts declined or folded)
* **Scope:** `tests/test_migration_rules.py` about 1213 and 1250-1256, `tests/test_migration_matrix.py` about 801-805 and 822-838, `CHANGELOG.md`.
* **Discrepancy:** `_O8_CONDITIONS` accepts any sentence with "during the run"; PG17 test is one literal regex; `len(why) > 40` and `len(set(values)) > 1` check that reasons exist, not that they are true; stale comments; `C10_EVERYONE` never read, O16 in neither set; wording "the new error class 25P04"; the ON assertion pins an odd wording.
* ***AI Suggestion:*** PROPOSE FIX for M3, the dead set, the stale comments and the 25P04 wording; DECLINE (Nit) the ON-wording pin and the psycopg class-name remark unless one line fixes them.
* ***Proposed Edit:*** Make the O8 guard check the conditions the code keeps (owner outside the family, at the start, switch name) with a planted wrong sentence per condition; allow a PG17 phrase in more than one wording or read it from ci.yml; use `C10_EVERYONE` (O17 uses it in Group 1) or delete it.

### [Group 8] [`codebase M6`, `design Minor`] - Severity: Minor - questions-for-lead still says "built and tested but OFF"
* **Scope:** `handover/questions-for-lead.md` about line 1831.
* ***AI Suggestion:*** PROPOSE FIX (a lead step, not a builder step: the builder is not allowed to edit this file)
* ***Proposed Edit:*** The lead applies the replacement text in `/home/user/build/B-P3a2-5/BUILDER-notes.md`; ledger row stays OPEN until applied.

### [Group 9] [`design escalation`] - Severity: Major - O8 default OFF is a least-privilege gap (OWNER-ONLY)
* **Scope:** `migrate.py:1271-1279`, the ticket line 598, `PLAIN_MIGRATION_ROLE_SQL`.
* **Discrepancy:** with the switch OFF, a non-superuser role outside the family that owns the run schema can drop or alter the package's tables and the run returns (the independent probes confirm: OFF returns, ON refuses).
* ***AI Suggestion:*** ESCALATE
* ***Justification:*** The ticket-line edit and the flip are the owner's decision (q-p3a2-o8-schema-owner). The reviewers' proposed fix (change the printed setup so the migration role owns the schema, then turn ON; or the middle option refusing only a non-superuser outsider) is recorded for that decision. Do not merge as "O8 done". Row `P3a24b-r15-owner-o8` already exists; this adds the batch-5 evidence.

### [Group 10] [evidence] - Severity: Minor - evidence deviations and items the runner could not run
* **Items:** (a) 16 of 18 new test ids pass on old code; the builder's per-test reasons must be checked and given one by one; (b) the 3 PG17 tests did not run: IMPOSSIBLE-NOW, next step the CI run on 17.10 before merge; (c) the prepared-transaction test needs `max_prepared_transactions` above 0: ci.yml sets none, so on CI it fails unless the service default allows it; check and set it in ci.yml (a builder step, tested on the runner's server settings); (d) runner left `/tmp/migrate-mutants-*` and `/tmp/mutants_*` folders it could not attribute; not a defect of the code.
* ***AI Suggestion:*** PROPOSE FIX for (a) and (c); IMPOSSIBLE-NOW for (b).

## Handoff
- Findings: 14 reviewer items merged into 10 groups. PROPOSE FIX: 9 groups (1-8, 10 partly). ESCALATE: 1 (group 9, OWNER-ONLY, row exists). CONTEST: 0. DECLINE: 2 Nits inside group 7. IMPOSSIBLE-NOW: PG17 tests, 25P04 final narrowing (group 5, 10b).
- Unaddressed after this resolve: all fix groups are OPEN until batch 6.
- **Who fixes it:** one batch-6 builder on a new branch `core/p3a2-b6` from `989c02a3`, pushing to `wip/cloud-p3a2-b6`. Files: `tests/test_migration_matrix.py`, `tests/test_migration_verify.py`, `tests/test_migration_verify_pg.py`, `tests/test_migration_rules.py`, `src/hadavin_sdk/store/migrate.py`, `store/postgres.py`, `store/migration_verify.py`, `.github/workflows/ci.yml` (item 10c only), `tests/migration/mutants`, `CHANGELOG.md`, builder notes. Order: 1, 2, 3, 4, 6, 5, 7, 10. Method per bug: name the class, fix at the shared choke point, grep siblings, show each new test failing on `989c02a3`, one mutant per fix, gate lines naming the commit they ran on, final-head full suite and full migrate mutants.
- Lead steps: apply the questions-for-lead text (group 8); keep group 9 for the owner.
