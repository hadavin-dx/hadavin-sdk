# Evidence results, P3a-2 batch 4b (round 14), head c3b2efdb (EVIDENCE RUNNER: recorded, not judged)

Head checked: `git rev-parse HEAD` = c3b2efdbd3f91fce726a105bdd23abc635d77d2b in a detached worktree, tree clean after every run (git status empty). Previous reviewed head f1ec83a8. Own PostgreSQL 16.15, own folder, port 56747. Raw logs: /home/user/build/evidence-raw/P3a2-4b-c3b2efdb/. Time: about 08:06 to 09:15 UTC (13:36 to 14:45 IST).

## What failed or was not run (first)
1. First full pytest run FAILED (exit 1: 1 failed, 12346 passed, 2 skipped): `tests/demo_askdata/test_validate_harm.py::...[dblink-connect]`. Cause as recorded: I had not put PGHOST/PGPORT into the SERVER's environment, so `dblink_connect('dbname=postgres')` looked at the default socket path. I restarted my own server with PGHOST/PGPORT in its environment; the test file alone then gave 253 passed, and a second whole run gave exit 0 (below). Both logs are kept (full-pytest-run1-tail.txt, full-pytest-run2-tail.txt).
2. `uv sync --locked --no-build` (brief's command) failed ("hadavin-sdk editable has no binary distribution"); I used `uv sync --locked --all-extras --group test` (no `--no-build`). Locked versions, nothing else changed.
3. PG17 case (SQLSTATE 25P04, `transaction_timeout`): NOT RUN, PostgreSQL 17 not available. The test is the visible skip below.
4. Known flaky `test_the_timing_harness_flags_a_quadratic_stand_in`: not run (brief: note, do not touch). It is in the "not live and not perf" selection; it passed in run 2 and was not in run 1's failure list.
5. Not run: gitleaks on this RESULTS folder is below; CI steps of ci.yml other than those listed here (perf job `-m perf`, the Docker/Linux job) were not run; the ticket names no perf item in my brief.
6. My probe 1 `_apply_grants` row returned normally only because no role argument was given, so that step never ran; I re-probed it with a runtime role (probe 2). My first O8 mid-run attempts hit other errors (42P01, 42501) before the O8 check; probe 3 shows the O8 line. All rows kept.

## Table
| Item | Command | Exit | Last line |
|---|---|---|---|
| Changed files (41 vs origin/main) | git diff --name-only origin/main...HEAD | 0 | changed-files.txt in raw dir |
| ruff check | ruff check src tests demos tools | 0 | All checks passed! |
| ruff format | ruff format --check src tests demos tools | 0 | 334 files already formatted |
| bandit | uv run --with bandit bandit -q -r src demos tools -ll | 0 | only two nosec warnings (tools.py:389), no findings |
| scan_repo | python tools/scan_repo.py | 0 | no output besides the uv TLS warning |
| gitleaks | gitleaks git ... --log-opts origin/main..HEAD | 0 | no leaks found |
| full pytest, run 1 | heavy.sh pytest -m "not live and not perf" -rs | 1 | 1 failed, 12346 passed, 2 skipped, 29 deselected in 688.01s (server env fault, item 1) |
| full pytest, run 2 | same, server restarted with PGHOST/PGPORT | 0 | 12347 passed, 2 skipped, 29 deselected in 641.02s |
| the 2 skips | -rs | | tests/contracts/test_llm.py:95 (Stubber refuses a malformed Converse shape before the kind sees it); tests/test_migration_verify_pg.py:922 (UNRUN: PostgreSQL 17 only) |
| mutants batch 1 | migrate_mutants.py (ids of --list-batch 1), alone | 0 | 103 of 103 killed |
| mutants batch 2 | same, batch 2 | 0 | 88 of 88 killed |
| mutants batch 3 | same, batch 3 | 0 | 98 of 98 killed |
| mutants batch 4 | same, batch 4 | 0 | 97 of 97 killed (test-helper: 39 of 39 killed) |
| migration numbers mutants | tests/migration_numbers_mutants.py | 0 | 40 of 40 good; problems: [] |
| stage mutants | tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| fail-before, verify + verify_pg + rules | old src f1ec83a8 (import path checked: old/src), the 6 changed test files and mutant list of the delta copied in | 1 | 26 failed, 349 passed, 1 skipped |
| fail-before, matrix file | same | 0 | 1103 passed (on old code) |
| fail-before, steps + wiring | same | 0 | 163 passed (on old code) |
| matrix count test | pytest -s test_the_matrix_has_exactly_the_planned_cells | 0 | printed output in matrix-count-output.txt |

Mutant batches: no BROKEN, ERROR or SURVIVED line in any of the four logs (grep count 0). Batch 2 count is 88 ids by `--list-batch 2` (the builder said "all killed"; he gave no number).

## Fail-before detail
- The 26 failures on old code are listed in failbefore-a-failed.txt (rules 2, verify 5 [O8 switch], verify_pg 19). The 2 rules failures occur even with the new mutant list copied in (the new mutants' old text is not in the old src).
- New test functions in the delta (19, by name, new-tests-vs-old.txt): 7 fail on old code, 12 pass on old code. Those 12: matrix `test_a_third_role_right_on_a_table_the_family_owns_is_refused_with_no_role_argument`, `test_c13_every_right_on_a_moved_table_is_judged_like_one_outside_the_map`, `test_c6b_control_a_trigger_that_defers_itself_again_and_changes_nothing_returns`, `test_c8_every_effect_has_an_object_or_a_reason_it_has_none`, `test_c9_control_a_clean_run_under_a_login_that_differs_from_the_role_returns`, `test_control_k8_fourth_form_the_group_owns_the_schema_of_the_run_and_the_run_returns`, `test_control_k8_the_hand_over_is_refused_in_three_forms`, `test_variant_o_the_database_owner_gives_a_right_on_the_database_or_a_new_schema`; verify_pg `test_a_connection_lost_at_any_read_of_pg_roles_gives_exit_2_and_keeps_nothing`, `test_a_failure_to_connect_at_the_start_is_the_one_exit_3_before_any_step`, `test_an_error_of_the_runner_after_the_last_file_is_never_taken_as_the_files_own`, `test_pg17_a_role_saved_transaction_timeout_that_strikes_inside_a_file_gives_exit_2` (skips). Matching is by function name; the existing-test parametrisations may differ.

## Hostile inputs: what `migrate()` returned (my own scripts, hostile-probe-*.txt and hostile*.py)
Each run on a fresh scratch schema as a plain migration role (the repo's test helper swaps the superuser login).
- Backend killed with pg_terminate_backend before the lock, the first read, the first file's check, a file's own statement, and (role argument given) the grants and the revoke: always `ConfigError` "migrate stopped and kept nothing: while <step>, the database returned an error (57P01)... Run migrate again.", ledger count 0.
- Client closed the connection before the first read / the first file check: `ConfigError` with label `OperationalError`, ledger 0.
- A migration file that kills its own backend: `ConfigError` (57P01) while applying that file, ledger 0.
- 25P03 live (role idle_in_transaction_session_timeout 150 ms): `ConfigError` (25P03), ledger 0, no "failed:".
- Classifier on made-up errors with a usable connection: 25000-25008, 25P01, 25P02 are the file's own (True); 25P03, 25P04, 08006, 57P01, 53100, XX000 are not (False); 23505, 42601, 40001, 22012, P0001 are the file's own; 23505 on a closed connection is not.
- O8 owner of the run schema changed just before the last state read: `ConfigError` "after the migration files and the grants, rights ... schema ... is owned by <role>, which is not the migration role or a role it belongs to", ledger 0, with ENFORCE_O8... False and True alike. Owner changed after the files, before the revoke step: `ConfigError` 42501, ledger 0 (both settings). Schema owned outside the family at the start: False: returned 5 versions, ledger 5; True: refused before any file ran with the same schema-owner line, ledger 0.
- Third-role SELECT on a family table, no role argument (second run after a clean first run): refused, "before any migration file ran, this database already holds rights that the grant map does not give: table ...: <role> has SELECT ... Nothing was changed. No file ran." Same for PUBLIC. Ledger unchanged (5).

## Not checked
Nothing was run on PostgreSQL 17. No perf jobs. Flaky timing test not repeated. Review claims in goldfish_review_report-r14.md were not read against these results (I judge nothing).

## Housekeeping
Own server stopped and own data folder deleted at the end; own worktrees kept under /home/user/build/EV-P3a2-4b-c3b2efdb. No process of another agent was touched. No commit, no push.
