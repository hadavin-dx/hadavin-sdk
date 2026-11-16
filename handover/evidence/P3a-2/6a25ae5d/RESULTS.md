# EVIDENCE RUNNER results: P3a-2 batch 8 (round 18), head 6a25ae5d (origin/wip/cloud-p3a2-b8), tag P3a2-8
Recorded only; nothing judged, nothing fixed, nothing committed or pushed. Raw logs: /home/user/build/evidence-raw/P3a2-8-6a25ae5d/. Own Postgres 16 (3 servers, now stopped and deleted), worktrees and venv deleted.

## Failed or not run (first)
1. Full pytest, run 2 (final, `max_prepared_transactions=10`): 1 failed, 12480 passed, 4 skipped, 29 deselected, exit 1. The failure: `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]` (cannot connect to the fixed socket /var/run/postgresql/.s.PGSQL.5432: no server there). Rerun of that file alone 3 times: 1 failed, 252 passed each time (same test). No "Broken pipe" appears in any log.
2. Full pytest, run 1: 3 failed, 12478 passed, 4 skipped, exit 1. Two extra failures (`..._prepared_transaction_that_holds_the_migration_lock...`, `test_the_lock_queries_tell_a_live_session_from_a_prepared_transaction`) were MY setup slip: my first server had no `max_prepared_transactions`. After restarting with 10, `-k prepared_transaction` gave 6 passed, 3 runs of 3; run 2 above has no such failure.
3. Timing test `test_the_timing_harness_flags_a_quadratic_stand_in` (all 3 slots held, run alone): head 3 of 3 FAILED ("a quadratic function must be flagged", 0.6 s); origin/main 2a8c2aac 3 of 3 FAILED, same message. (On the head it lives in tests/test_migration_numbers_perf.py, perf-marked; on main in tests/test_migration_numbers.py.) Not touched.
4. Skipped (4): tests/contracts/test_llm.py:95 (Stubber refuses a malformed Converse shape); tests/test_migration_verify_pg.py lines 908, 961, 1144 (PostgreSQL 17 only: `transaction_timeout`). Not run (impossible here): PG17 tests, Python 3.12, semgrep, zizmor, trivy, pip-audit. `uv sync --locked --no-build` not used (fails here); used `uv sync --locked --all-extras --group test` without `--no-build`, exit 0.
5. Not run: the full CI step list beyond the items in the brief (only the runners named in the brief were run).

## Results
| item | command (all on head 6a25ae5d, clean worktree) | exit | last line |
|---|---|---|---|
| changed files vs main | `git diff --name-only origin/main...HEAD` | 0 | 43 files (changed-files-vs-main.txt) |
| ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| ruff format | `ruff format --check src tests demos tools` | 0 | 335 files already formatted |
| bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only warnings (nosec tools.py:389), no findings |
| scan_repo | `python tools/scan_repo.py` | 0 | no output lines of findings |
| gitleaks | `gitleaks git --redact --log-opts=origin/main..HEAD` | 0 | no leaks found |
| full pytest 1 | heavy.sh pytest -m "not live and not perf" -rs | 1 | 3 failed, 12478 passed, 4 skipped, 29 deselected (669 s) |
| full pytest 2 | same | 1 | 1 failed, 12480 passed, 4 skipped, 29 deselected (821 s) |
| migrate mutants b1 | `migrate_mutants.py $(--list-batch 1)` | 0 | 148 of 148 killed (not killed: []) |
| b2 / b3 / b4 | same, batches 2-4 | 0 | 88 of 88; 98 of 98; 97 of 97 killed |
| migration_numbers_mutants | heavy.sh | 0 | 40 of 40 good; problems: [] |
| stage_mutants | heavy.sh | 0 | 37 of 37 good; problems: [] |
| V130-V148 + V116/V117/V122/V125 | read from batch 1 log | | 23 rows, all KILLED |
| CHANGELOG numbers | `pytest tests/test_migration_matrix.py -s -k planned_cells` | 0 | 2 passed |

## CHANGELOG numbers against the matrix test's own printout
Printed: 29 x 10 x 2 = 580; empty by logic 30; generated 550; ended at step 0: 32; reach data checks 518; expected refused 525; expected to return 25; C8 44+12, C13 36, C9 58, C6b 58, variant (O) 20, pre-existing 72, controls 21, compositions 200; total 871. Every number in the brief's list (580, 30, 550, 32, 518, 525, 25, 871) equals the printout.

## Fail-before (aac26d60 source, with the 3 changed test files and tests/migrate_mutants.py copied in; `PYTHONPATH` on its src, import path confirmed to be the old worktree)
47 ids (the 44 new: 39 in tests/test_sign_in_channels.py + 5 others, plus the 3 tightened ids taken from the builder's list): 38 failed, 9 passed. All three files whole on the old source: 39 failed, 221 passed, 3 skipped (the 39th failure is an old test that is not one of the 47). The 9 that pass on old code (same 9 as the builder's table):
- test_a_close_that_fails_with_any_error_does_not_hide_the_first_error[OperationalError]
- test_an_iam_address_with_a_host_a_user_and_a_plain_port_asks_for_the_sign_in[default-port], [port-1], [port-65535]
- test_an_interrupt_during_the_sign_in_is_not_turned_into_a_refusal[KeyboardInterrupt-client-is-built], [KeyboardInterrupt-token-is-asked-for], [SystemExit-client-is-built], [SystemExit-token-is-asked-for]
- test_the_ast_scan_finds_a_raise_inside_a_handler_and_ignores_a_bare_raise
(all in tests/test_sign_in_channels.py). Per-id outcomes: fail-before-47-ids.txt.
Id counts: head files 263 ids (tests/test_migration_verify.py, test_migration_verify_pg.py, test_sign_in_channels.py); at aac26d60 the two older files had 221; new 5 + 39; gone 2.

## Not checked
Whether the 39th old-source failure is related to this batch; why the timing test fails on both heads; PG17 behaviour. Builder's "Broken pipe" failure did not occur in either of my full runs.
