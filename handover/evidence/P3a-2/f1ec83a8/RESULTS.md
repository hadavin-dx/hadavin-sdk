# EVIDENCE RUNNER results: P3a-2 batch 3e, head f1ec83a84f07a7515d674bdf74f90d91eb2ab296 (tag P3a2-3e)

Recorded only; nothing was fixed or judged. Previous reviewed head 7bc65cdc. Raw logs: /home/user/build/evidence-raw/P3a2-3e-f1ec83a8/.
Setup checked: detached worktree at the exact head, `git status` clean (0 lines). Postgres 16.15 on three own servers (one per job, never two jobs on one server), prepared transactions on.

## What failed or was not run (first)
1. Full pytest FAILED: 2 failed, 12125 passed, 1 skipped, 29 deselected (exit 1, 9 min 7 s). The two failures are `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[copy-to-file]` (the server may not write `/tmp/askdata_p2_copy.csv`: the file already exists, owned by another account, made 06:11 UTC by a server that is not mine) and `[dblink-connect]` (the attack connects to the default socket `/var/run/postgresql/.s.PGSQL.5432`; my server listens on its own socket). Both are outside the diff. I did not rerun them (the run had a summary line). The skip is `tests/contracts/test_llm.py:95`.
2. Setup deviation: `uv sync --locked --no-build ...` as written FAILS (`hadavin-sdk==0.1.0 @ editable+.` has no binary distribution). I ran the same command without `--no-build` (exit 0).
3. PG17 step of ci.yml: NOT RUN (only PostgreSQL 16 is available here). Branches that need 17 were not exercised.
4. Timing flake (item 9): on the head the test now lives in `tests/test_migration_numbers_perf.py`; on main it is in `tests/test_migration_numbers.py`. Head: fail, fail, pass. Main: fail, fail, fail. Same assertion each time ("a quadratic function must be flagged"). Run alone, with all three heavy slots held.
5. Fail-before (item 7): 12 tests fail on old source (listed below), 433 of the 444 new test ids pass on old source.
6. Heavy-queue wait: fail-before waited about 22 min and the timing runs about 25 min in the shared queue (other agents' jobs held the slots).

## Table
| Item | Command (summary) | Exit | Last line |
|---|---|---|---|
| 1 changed files | `git diff --name-only origin/main...HEAD` | 0 | 41 files (changed-files.txt) |
| 2 ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2 ruff format | `ruff format --check src tests demos tools` | 0 | 334 files already formatted |
| 3 bandit | `bandit -q -r src demos tools -ll` | 0 | only two nosec warnings for src/hadavin_sdk/tools.py:389 |
| 4 scan_repo | `python tools/scan_repo.py` | 0 | no output besides a uv warning |
| 4 stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| 4 gitleaks | `gitleaks git --log-opts origin/main..HEAD` | 0 | no leaks found |
| 5 full pytest | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh | 1 | 2 failed, 12125 passed, 1 skipped, 29 deselected |
| 6 migrate_mutants batch 1 | ids from `--list-batch 1` | 0 | 87 of 87 killed |
| 6 batch 2 | idem | 0 | 88 of 88 killed |
| 6 batch 3 | idem | 0 | 98 of 98 killed |
| 6 batch 4 | idem | 0 | 97 of 97 killed |
| 6 V86, V87 | inside batch 1 | 0 | both KILLED (V86 by test_direction_2_sees_an_extra_right_on_an_object_outside_the_schema_of_the_run; V87 by the test_c8 cells) |
| 6 migration_numbers_mutants | `python tests/migration_numbers_mutants.py` | 0 | 40 of 40 good; problems: [] |
| 6 stage_mutants (ci.yml step) | see item 4 | 0 | 37 of 37 good |
| 6 PG17 step | n/a | not run | no PostgreSQL 17 here |
| 7 fail-before | 3 changed test files + oracle.py + migrate_mutants.py copied onto a detached 7bc65cdc | 1 | 12 failed, 1078 passed (3 min 13 s) |
| 9 timing flake | alone, 3 slots held | head 1,1,0; main 1,1,1 | see above |

Batches were run one after the other, one at a time per server. No "baseline not green" appeared.

## Item 7: fail-before
Run: 1090 tests in the three changed test files; 646 ids exist at 7bc65cdc, 444 are new at the head (new-test-ids.txt). The head's tests ran against the old source.
Failed on old source (fail-before-failed.txt): X28-named-role-owns-a-table (no-roles and with-roles), the 8 cells of `test_a_connection_lost_at_any_step_before_the_commit_gives_exit_2_and_keeps_nothing` (_take_the_lock, _refuse_privileged_role, _refuse_foreign_owned, _read_back, _check_read_back, _recheck_roles, _apply_grants, _revoke_default_execute), `test_a_connection_lost_while_a_file_runs_is_refused_with_exit_2`, `test_a_bug_before_the_commit_stays_loud_and_a_files_own_error_stays_its_own`.
New tests that pass on old source: 433 ids (fail-before-new-tests-that-pass-on-old-code.txt); 430 of them are in test_migration_matrix.py.

## Item 8: my own probes (probe*.py; typed from the 3d report and the matrix names, not the builder's tests)
Method: a fresh scratch schema, one first run (5 files applied), the administrator makes the state, a second run, with and without `runtime_role`. Raw: probe-A-B-C-D.txt, probe-commit-step.txt, probe-lock-step.txt.
Second run result by state (no-roles / with-roles):
- X17 create on schema public: returned / ConfigError exit 2
- X18 create on database: returned / ConfigError exit 2
- X19 temporary on database: returned / ConfigError exit 2
- X28 role owns a package table: ConfigError exit 2 / ConfigError exit 2
- X31 member of pg_read_all_data: returned / ConfigError exit 2
- X32 member of a role with CREATEROLE: returned / ConfigError exit 2
- X33 CREATEDB on the named role: returned / ConfigError exit 2
- X36 default right set by another role: returned / ConfigError exit 2
So of the eight, only X28 is refused without role arguments; the other seven return normally (0 applied), as the builder said.
Not promised states (second run, both variants): X01t returned; X11 returned; X12 returned. O24 as a function of the family left callable in ANOTHER schema owned by the migration role: returned in both variants; my first O24 form (hand the package function to another owner) was refused by the owner rule (ConfigError exit 2), which is a different state.
Driver error (psycopg.OperationalError, no SQLSTATE) injected at the first matching statement, fresh schema, first run, nothing kept in every pre-commit case (0 tables, no ledger table):
- lock step, version read, ledger read, file apply (INSERT), grants (GRANT and REVOKE with a runtime role), SET CONSTRAINTS: ConfigError exit 2.
- Two markers first gave exit 3 (OperationalError) because the injection hit the TEST helper's own connection setup (`pg_advisory_xact_lock`, `pg_roles`), not `migrate`. Re-run skipping the helper's first use: the lock marker gives ConfigError exit 2; the `pg_roles` marker still gives a raw OperationalError exit 3 (a `pg_roles` read at migrate's second use; not traced further: UNCHECKED which statement it is).
- COMMIT lost before reaching the server (no SQLSTATE): AppliedNotVerifiedError exit 5; 0 tables kept. COMMIT ran, reply lost: exit 5; 16 tables and 5 ledger rows kept. COMMIT refused 40001 after rollback: ConfigError exit 2, nothing kept. 40003: exit 5 (nothing was in fact kept). 23505: ConfigError exit 2.
- Step 8 connect fails: AppliedNotVerifiedError exit 5; tables kept.
K8 (a file hands a map table to a group the migration role belongs to): (1) in the open: ConfigError exit 2 "may not be handed to another role"; (2) dynamic SQL: raw InsufficientPrivilege (exit 3 by the CLI rule) "permission denied for schema"; (3) after CREATE on the schema is given to the group: ConfigError exit 2 "before any migration file ran". Table `spend` stayed with the migration role.

## Not checked
PG17 behaviour; whether the CLI maps each exception to the exit number (I used the documented mapping: ConfigError 2, AppliedNotVerifiedError 5, other 3; read in cli.py, not run through the CLI); the two askdata failures were not repaired or rerun; no perf marker run (the ticket names none).

## Hygiene
Three own Postgres servers stopped and their folders removed at the end; worktrees removed. No secret-shaped text written; gitleaks on this folder run below.
