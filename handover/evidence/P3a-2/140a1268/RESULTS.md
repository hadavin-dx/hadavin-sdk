# EVIDENCE RUNNER results: P3a-2 batch 6 (round 16), head 140a1268b8f45f47ae914391379bc6b272f883e7 (origin/wip/cloud-p3a2-b6)
Run 2026-11-12, 12:08 to 12:55 UTC (17:38 to 18:25 IST). I ran and recorded; I judged nothing and changed no source or test of the head. Raw logs: /home/user/build/evidence-raw/P3a2-6-140a1268/ (outside the repo). Detached worktree head confirmed equal to the sha, tree clean before and after the mutant runs.

## Failed or not run (first)
1. Full pytest: 1 failed, 12408 passed, 4 skipped, 29 deselected (13m20s). The one failure: `tests/demo_askdata/test_validate_harm.py` (line 179, via `prove_harm` line 133): psycopg "could not establish connection ... socket /var/run/postgresql/.s.PGSQL.5432 ... No such file or directory". My server's socket is in my own folder, so the fixed path does not exist (the cause the brief predicted). Not rerun, not changed.
2. Timing test `test_the_timing_harness_flags_a_quadratic_stand_in`: on the head it is no longer in `tests/test_migration_numbers.py`; it is in `tests/test_migration_numbers_perf.py`. Run alone (all three heavy slots held) 3 times on the head in that file: fail, pass, fail (1 of 3 passed). On origin/main (2a8c2aac) in `tests/test_migration_numbers.py`: fail, fail, fail (0 of 3 passed). (My first attempt used the old file name on the head: "not found", rc 4, 3 times; recorded in raw logs timing-wt-*.log.)
3. Not run (impossible now, as the brief says): PostgreSQL 17 tests (3 tests skipped, listed below), Python 3.12 (venv is Python 3.13), semgrep, zizmor, trivy, pip-audit. Also not run: the perf marker suite (`-m perf`) as a whole (the ticket names no perf item here); item 8 hostile probes (this brief lists none).
4. Setup: `uv sync --locked --no-build` not used; I ran `uv sync --locked --all-extras --group test` (without --no-build), rc 0.

## Table
| Item | Command (short) | Exit code | Result line |
|---|---|---|---|
| ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| ruff format | `ruff format --check src tests demos tools` | 0 | 334 files already formatted |
| bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | no issues printed (only 3 warning lines: nosec B102 at tools.py:389 twice, and "bytes is not a test name") |
| scan_repo | `python tools/scan_repo.py` | 0 | no output |
| gitleaks | `gitleaks git --redact --config .gitleaks.toml --log-opts=origin/main..HEAD` | 0 | no leaks found |
| full pytest | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh, own PG16.15, max_prepared_transactions=10 | 1 | 1 failed, 12408 passed, 4 skipped, 29 deselected |
| mutants batch 1 | `tests/migrate_mutants.py <ids of --list-batch 1>` | 0 | 121 of 121 killed; not killed: [] |
| mutants batch 2 | same, batch 2 | 0 | 88 of 88 killed; not killed: [] |
| mutants batch 3 | same, batch 3 | 0 | 98 of 98 killed; not killed: [] |
| mutants batch 4 | same, batch 4 | 0 | 97 of 97 killed; not killed: [] |
| number mutants | `tests/migration_numbers_mutants.py` | 0 | 40 of 40 good; problems: [] |
| stage mutants | `tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| fail-before | the 5 changed test files of DELTA-FILES.txt (whole files) copied into a detached worktree of 989c02a3 with its own src (import path checked: old/src) | 1 | 5 failed, 1534 passed, 3 skipped, 1 deselected |
| matrix numbers | `test_the_matrix_has_exactly_the_planned_cells` and `test_the_pre_existing_cells_are_counted` with -s | 0 | 2 passed |
| timing test | see item 2 above | see above | head 1 of 3 passed; main 0 of 3 passed |

Mutant batches ran one at a time on one Postgres (the second of my three servers; the full suite and the fail-before run each had their own server, so nothing shared a server).

## Item 1: changed files
41 files in `git diff --name-only origin/main...HEAD` (list: raw folder changed-files.txt). The batch-6 delta (DELTA-FILES.txt): CHANGELOG.md, src/hadavin_sdk/store/migrate.py, src/hadavin_sdk/store/postgres.py, tests/migrate_mutants.py, tests/test_migration_matrix.py, tests/test_migration_rules.py, tests/test_migration_verify.py, tests/test_migration_verify_pg.py.

## Skips of the full run, by name
- tests/contracts/test_llm.py:95 (Stubber refuses a malformed Converse shape before the kind sees it)
- tests/test_migration_verify_pg.py:805, :858, :1029 (each "UNRUN: PostgreSQL 17 only", `transaction_timeout` does not exist below 17)

## Item 3: fail-before detail
Files copied from the head into the old worktree: tests/migrate_mutants.py, tests/test_migration_matrix.py, tests/test_migration_rules.py, tests/test_migration_verify.py, tests/test_migration_verify_pg.py (CHANGELOG is not a test file).
Failed on old code (5):
- tests/test_migration_rules.py::test_every_migrate_mutant_still_applies_to_the_source (the list check reports 4 problems, the first: V112's old text is in src/hadavin_sdk/store/postgres.py 0 times)
- tests/test_migration_rules.py::test_the_list_check_finds_a_mutant_id_that_a_docstring_or_a_parametrize_id_names_but_no_mutant_has
- tests/test_migration_verify_pg.py::test_a_failure_to_connect_at_the_start_is_refused_with_exit_2_and_keeps_nothing
- tests/test_migration_verify_pg.py::test_a_setup_statement_that_fails_on_the_first_connection_is_refused_with_exit_2_and_closed
- tests/test_migration_verify_pg.py::test_a_setup_statement_that_fails_on_the_connection_of_step_8_gives_exit_5
The builder's figure (3 failed, 47 passed) was for a smaller selection; the 3 tests of test_migration_verify_pg.py are the same 3 it named. Test names present in the head's five test files but not in the old ones: 18 (collection by name, parametrize ids folded). Of those 18, 3 fail on old code (the three above) and 15 pass on old code; the list is in new-tests-on-old.txt.

## Item 5: CHANGELOG numbers against the run of the matrix (printed by the count test)
580 cells (29 x 10 x 2): matches. Empty by logic 30 (15 pairs x 2): matches. Built 550: matches. Ended at step 0 by the text rules: 32: matches. Reach the data checks 518: matches. Expected refused 525: matches. Expected to return 25: matches. Total cells and controls 871: matches. Other lines printed: C6b 58; C8 44 + 12; C9 58; C13 36; variant (O) 20; pre-existing 72 (48 refused, 24 return normally); controls 21; compositions 200. Full printout: matrix-count.txt.

## Files here
RESULTS.md, matrix-count.txt, new-tests-on-old.txt, full-pytest-tail.txt, failbefore-summary.txt, mutants-summary.txt.
