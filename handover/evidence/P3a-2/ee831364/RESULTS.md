# EVIDENCE RUNNER results, P3a-2, head ee831364d83d4fb3edc04a5411a140cc0e3c57a1
Run 2026-11-12 00:38 to 01:22 UTC (06:08 to 06:52 IST). Recorded, not judged. Raw logs: /home/user/build/evidence-raw/P3a2-ee831364/ (outside the repo).
HEAD confirmed with `git rev-parse` = ee831364d83d4fb3edc04a5411a140cc0e3c57a1, tree clean. origin/main = 2a8c2aac.

## Not run, or run differently (first)
- tests/migration_numbers_mutants.py: NOT RUN to a result. The runner first runs the unmutated copy and stopped with "the unmutated copy does not pass its tests" (exit 1), twice (once in the queue, once alone with all 3 slots). Cause seen by running its 4 baseline test files by hand: tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in fails (the runner's empty ini file stops the perf marker deselecting it). No "N of N good" line exists for this script.
- `uv sync --locked --no-build` failed (error: hadavin-sdk editable can't be installed with --no-build, no binary distribution; log sync.log). I used `uv sync --locked --all-extras --group test` (without --no-build) instead; rc 0.
- First full pytest run FAILED (1 failed, 11205 passed) because I started my own Postgres without PGHOST/PGPORT in the server's environment: test_validate_harm.py[dblink-connect] could not reach the default socket. I restarted Postgres with them and reran: rc 0. Both logs kept (full-pytest-run1-badpgenv.log, full-pytest.log).
- bandit was run as `uv run --no-sync --with bandit bandit -q -r src demos tools -ll` (per common brief).
- Not run: ticket acceptance probes / hostile inputs (item 8; ticket file P3a.md is not in the branch and the notes file is builder account), perf run, tests/test_migration_numbers.py on origin/main (not asked in this brief), CI steps semgrep/zizmor/trivy (not named for this package).
- Mutant survivors depend on my setup (own Postgres 16.15, max_prepared_transactions=0, trust auth, superuser postgres); unknown whether the builder's 28 vs my 39 differ because of that.

## Results
| Item | Command (short) | Exit | Last line |
|---|---|---|---|
| migrate mutants | `heavy.sh uv run python tests/migrate_mutants.py` | **1** | `262 of 301 killed`; 39 SURVIVED (builder reported 28); behaviour 205 of 244, prose 11 of 11, test-helper 46 of 46; baseline rc=0 329 passed |
| numbers mutants | `python tests/migration_numbers_mutants.py` | **1** | RuntimeError: the unmutated copy does not pass its tests (x2) |
| flaky test on head, alone x3 | `flock x3 pytest ...test_the_timing_harness_flags_a_quadratic_stand_in` | 1, 1, 1 | `1 failed in 0.70s` each |
| full pytest run 1 (my pg env wrong) | heavy.sh pytest -m "not live and not perf" | **1** | 1 failed, 11205 passed, 1 skipped, 29 deselected in 337.70s |
| full pytest run 2 (pg env fixed) | same | 0 | 11206 passed, 1 skipped, 29 deselected in 347.90s |
| fail-before (new/changed test files on main src, --continue-on-collection-errors) | pytest 17 files | 1 | 47 failed, 319 passed, 3 deselected, 128 errors; first attempt without the flag: 8 collection errors, rc 2 |
| diff names | `git diff --name-only origin/main...HEAD` | 0 | 38 files (diff-names.txt) |
| ruff check src tests demos tools | | 0 | All checks passed! |
| ruff format --check | | 0 | 333 files already formatted |
| bandit -ll | | 0 | only "nosec encountered (B102)" warnings on src/hadavin_sdk/tools.py:389 |
| tools/scan_repo.py | | 0 | (empty output) |
| tests/stage_mutants.py | | 0 | 37 of 37 good; problems: [] |
| gitleaks git, origin/main..HEAD | | 0 | no leaks found |

## Survivors of migrate_mutants.py (39, exit 1)
Full lines with descriptions: migrate-survivors.txt. Ids: GM1 AC1 AC2 AC3 AC4 AC5 SD1 SD2 RN6 DP1 SC8 SC9 OW4 OW3 WD1 GO4 RA1 RA1b RA2 RK1 SC10 SC11 GO5 GO6 DP2 DP3 DP4 DP5 RF5 RO3 RO5 DP6 DP7 SD6 RA4 IM1 RK2 SC12 SC13.

## Fail-before
Files copied onto a detached worktree of origin/main (src from main; import path checked): the 28 added/modified files under tests/ of the diff (tests-delta-status.txt in raw folder). 17 test files run. Collection errors on main src (AttributeError or import): test_k2_migrations, test_migration_compare, test_migration_numbers_guards, test_migration_postgres, test_migration_rules, test_migration_steps, test_migration_verify, test_migration_verify_pg (and test_migration_wiring has errors at test level). Failed list: failbefore-failures.txt (47). Passed on old code (319): failbefore-passes.txt; per file: test_k5_fixes2 20, test_k5_round10_postgres 5, test_migration_matrix 56, test_migration_names 27, test_migration_numbers 129, test_p2_postgres 16, test_p7_store 21, warden_port/test_audit_chain 45.

## Cleanup
Postgres on port 56281 stopped and its folder, worktrees and venv removed (see end of file for confirmation).
Cleanup confirmed 2026-11-12 01:25 UTC: own Postgres stopped, 2 worktrees, venv and pg folder removed (env.sh script kept removed with folder). No commit, no push.
