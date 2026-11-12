# Evidence run, P3a-2 batch 5 (round 15), head 989c02a3d21103036183b762e4c8b6209bfe2f81
Evidence runner. Records only; no judgement, no fixes. Server: own PostgreSQL 16.15, `max_prepared_transactions=10`, trust auth, superuser `postgres`. PostgreSQL 17 is not installed here. Raw logs: /home/user/build/evidence-raw/P3a2-5-989c02a3/. Time used about 60 minutes of real clock, most of it waiting for a heavy slot (all 3 busy 10:01 to 10:25).

## What failed, was not run, or went wrong in the run itself (first)
1. **My own two invalid full-suite runs (not the head's fault).** Run 1 shared one server with my fail-before run and the mutant runner (the suite reported "test leftovers" errors: 6 failed, 1119 errors). Run 2 was started from the wrong folder (main repo tests, collection error). Both logs are kept (`full-pytest-run1-INVALID-concurrent-runs.log`, `full-pytest-run2-wrong-cwd.log`) and not counted. Run 3, alone on a fresh server and started from the head worktree, is the result below.
2. First server had `max_prepared_transactions=0`: `test_the_lock_queries_tell_a_live_session_from_a_prepared_transaction` fails there ("prepared transactions are disabled") on the old code and the head alike. With 10 it passes. CI's server setting for this is not set in ci.yml (no "prepared" in the file).
3. PostgreSQL 17 tests: **not run** (3 visible skips, listed below).
4. The three real-server probe cells for "C10 O13-O16" first hit the static text guard because I wrote the statements in the open (`probe-h5.py`); I redid them inside a split dynamic-SQL function (`probe-h6.py`). Both outputs are kept.
5. Not run: perf tests (ticket names none), timing flake test (brief says note only).
6. Left on the machine: /tmp/migrate-mutants-96lnva5p and two /tmp/mutants_* folders; at least one may be mine from the killed mutant chain (I killed my own chain at 10:14 after run 1), I did not delete folders I could not tell were mine.

## Table
| # | Item | Command (short) | Exit | Result line |
|---|---|---|---|---|
| 1 | changed files | `git diff --name-only origin/main...HEAD` | 0 | 41 files (`changed-files.txt`) |
| 2 | ruff | `ruff check` / `ruff format --check` over src tests demos tools | 0 / 0 | All checks passed; 334 files already formatted |
| 3 | bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | no findings (2 nosec warnings for tools.py:389) |
| 4 | scan_repo | `python tools/scan_repo.py` | 0 | no output lines beyond the uv warning |
| 4 | gitleaks origin/main..HEAD | `gitleaks git --log-opts=origin/main..HEAD` | 0 | no leaks found |
| 5 | full pytest (run 3) | `heavy.sh pytest -m "not live and not perf" -p no:cacheprovider -q -rs` | 0 | 12363 passed, 4 skipped, 29 deselected in 607.12s |
| 6 | migrate_mutants batch 1 | `tests/migrate_mutants.py $(--list-batch 1)` | 0 | 112 of 112 killed |
| 6 | batch 2 | same | 0 | 88 of 88 killed |
| 6 | batch 3 | same | 0 | 98 of 98 killed |
| 6 | batch 4 | same | 0 | 97 of 97 killed (V104-V112 each KILLED; V102, V103 KILLED) |
| 6 | migration_numbers_mutants | `python tests/migration_numbers_mutants.py` | 0 | 40 of 40 good; problems: [] |
| 6 | stage_mutants (also CI step) | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 3 | fail-before | 4 changed test files (+ migrate_mutants.py, test_migration_rules.py etc. all 5 copied) into worktree of c3b2efdb, old src (import path printed: .../old/src/hadavin_sdk) | 1 | 3 failed, 1490 passed, 3 skipped, 1 deselected (`failbefore-old.log`) |
| 6 | matrix count test | `pytest -k test_the_matrix_has_exactly_the_planned_cells -s` | 0 | see below |

Skips on the head (full run), by name:
- tests/contracts/test_llm.py (line 95): test_a_malformed_answer_is_a_provider_error, "Stubber refuses a malformed Converse shape before the kind sees it"
- tests/test_migration_verify_pg.py::test_a_saved_transaction_timeout_stops_the_check_and_migrate_refuses_with_exit_2 (UNRUN: PostgreSQL 17 only)
- tests/test_migration_verify_pg.py::test_a_role_saved_transaction_timeout_gives_exit_2_wherever_it_strikes (UNRUN: PostgreSQL 17 only)
- tests/test_migration_verify_pg.py::test_pg17_a_role_saved_transaction_timeout_that_strikes_inside_a_file_gives_exit_2 (UNRUN: PostgreSQL 17 only)
Counts agree with the builder's: 12363 / 4 / 29, and 112, 88, 98, 97, 40 of 40, 37.

## Fail-before (item 3)
The old-code run covered all 1496 tests of the four changed test files (matrix, rules, verify, verify_pg). Failed on old code: test_the_changelog_does_not_state_rule_o8_more_strictly_than_the_code_keeps_it, test_the_changelog_does_not_state_a_postgresql_17_run_as_fact (both new), and test_the_lock_queries_tell_a_live_session_from_a_prepared_transaction (existing test; server setting, see failure 2; rerun with setting 10: 1 passed, `failbefore-old-prepared-mpt10.log`). The head has 18 test ids that the old files did not have; on old code 16 passed and 2 failed (list in `new-tests-on-old.txt`). New tests that PASS on old code: the 8 matrix cells O13-O16 under C10 (each with/without roles), the two O8 switch cells (on/off), test_o8_switch_on_the_public_schema_..., test_c9_a_table_owned_by_the_login_..., test_c13_every_effect_has_a_table_to_move_or_a_reason_it_has_none, test_the_o8_wording_check_sees_a_planted_unconditional_sentence, test_connect_runs_exactly_one_statement_..., test_the_server_version_decides_whether_a_role_can_save_a_transaction_timeout.

## Matrix count test (item 6)
580 cells = 29 effects x 10 carriers x 2 variants; empty by logic 32 (16 pairs x 2); generated 548; stop at step 0 by the text rules 32; reach the data checks 516; expected refused 523; expected to return 25. Other carriers: C6b 58, C8 44, C9 58, C13 24, variant (O) 20, pre-existing 72, controls 21, compositions 200 (seed 20261112), total 845. Full text: `matrix-count.log`.

## Hostile inputs (item 5), what migrate returned (own scripts; outputs in hostile5.log, hostile6.log)
Rule O8, real plain login (not the test helper), schema made by the superuser, an outsider role `evo_*`:
- switch OFF, outsider owns schema from the start: RETURNED 5 versions, ledger 5.
- switch OFF, run clean first, then owner changed to the outsider, one pending file (create table): RETURNED 1 version, ledger 6.
- switch ON, outsider owns from the start: RAISED ConfigError "before any migration file ran ... evo_x is owned by evo_x, which is not the migration role or a role it belongs to ... Nothing was changed. No file ran."
- switch ON, "clean first" run (schema made by the superuser, so owned by postgres): RAISED ConfigError, schema owned by postgres refused at the start; ledger not reached. Then outsider+pending file: same refusal text with the outsider name.
C10 cells (statement inside a split dynamic-SQL function, schema `<run>_o` owned by the plain role, named role `evrt_*`), `hostile6.log`:
- O13 no roles argument: RETURNED 6 versions (ledger 6); with runtime_role: RAISED ConfigError "NOT THIS PACKAGE'S OBJECT: schema ..._o: evrt has CREATE. To remove: REVOKE CREATE ...".
- O14 no roles argument: RETURNED 6; with runtime_role: RAISED "evrt may pass USAGE on to others. To remove: REVOKE GRANT OPTION FOR USAGE ...".
- O15 (CREATE for PUBLIC) both variants: RAISED "everyone (PUBLIC) has CREATE. To remove: REVOKE CREATE ON SCHEMA ... FROM PUBLIC".
- O16 (default right SELECT on tables for named role) both variants: RAISED "evrt gets SELECT on every new table that <migration role> makes in the schema ..._o. To remove: ALTER DEFAULT PRIVILEGES ... REVOKE SELECT".
Written in the open (hostile5.log) the same statements were refused by the static text guard ("the guard does not read rights there", "ALTER DEFAULT PRIVILEGES: the guard cannot read ...") with ledger 0.
Third role right on a family table (`runs`): SELECT, INSERT, UPDATE named to a third role, with and without a runtime role argument: all six RAISED ConfigError "before any migration file ran ... <third> has <RIGHT>; only the owner, the migration role and the grant map's roles may hold rights here". Baselines RETURNED 5.
Lost session: pg_terminate_backend before `_take_the_lock`, `_read_back`, `_check_read_back`: RAISED ConfigError "migrate stopped and kept nothing ... (57P01) ... Run migrate again." (ledger 0); before `_apply_grants`: RETURNED 5 versions (ledger 5); a file that kills its own backend: RAISED "... while applying 0006_kill.sql ... (57P01)", ledger 0; second pending file kills its backend after the first pending file ran in the same run: RAISED (57P01), ledger 0.
Class 25: classifier `_is_a_files_own_error` on a usable connection: True for 25000-25008, 25P01, 25P02, 40001, 23505; False for 25P03, 25P04, 08006, 57P01; on a closed connection False for all. Live 25P03 (role idle_in_transaction_session_timeout 150 ms): RAISED "migrate stopped and kept nothing ... (25P03)".
PG17-only tests: not run (PostgreSQL 16 only).

## CHANGELOG sentences about O8 and PG17 (item 8), file CHANGELOG.md at 989c02a3
O8 (full sentences in `changelog-o8.txt`; line numbers are CHANGELOG.md lines):
- line 29: "The strict reading of rule O8 is built behind a switch that is OFF, with one real-server cell for each value of the switch (see the next paragraph)."
- line 30: "Rule O8 of the ticket (refuse a schema of the run that a role outside the family owns) is enforced only for a change of owner during the run; a schema that another role outside the family already owned at the start is NOT refused, and that role can then drop or change the package's tables. This is looser than the ticket and stays so until the lead answers question q-p3a2-o8-schema-owner: the stricter reading is behind the switch `ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START` in `store/migrate.py`..."
- line 31: "... the schema of the run must not change owner during the run (a schema that a role outside the family owned from the start is refused only when the switch `ENFORCE_O8_...` is ON, and it is OFF); this is judged in the schema of the run only."
Code: src/hadavin_sdk/store/migrate.py line 1279 `ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START = False`; the filter at lines 1305-1316 drops a `foreign_owner` problem of kind schema, in the schema of the run, whose owner equals the schema owner at the start, unless the switch is True. The probes above match: OFF returned, ON refused.
PG17 (`changelog-pg17.txt`):
- line 15: "The whole suite is configured to run in CI on PostgreSQL 17.10 (not yet seen: no run on 17 has been observed)."
- line 29: "PostgreSQL 17 is UNRUN here: three tests need it (...), and each shows a visible skip on PostgreSQL 16 (`UNRUN: PostgreSQL 17 only`). ... The package must not be called done without the PostgreSQL 17 run."
- line 32: "The PostgreSQL 17 case (a role-saved value) has not been run on any server here ... the three tests that need 17 are visible skips ..."
- line 58: "PostgreSQL 17 is UNRUN on the build machine (the three tests that need it are visible skips; the CI run on 17.10 is configured and is the lead's step); PostgreSQL 18 has not been run."
Code: skips at tests/test_migration_verify_pg.py lines 720-722, 773-775, 940-942 (`mrun_server_version() < 170000`). On 16 the run showed exactly 3 such skips (plus the one test_llm skip). ci.yml at 989c02a3 (git show) lines 40-41 and 121-122: service image `postgres:17.10@sha256:<digest>` in two jobs (read after the run, only these lines).
