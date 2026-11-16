# PR89 core/mutation-runner-keywords @ db0d9eb49f16b0873d8c7453a2ff5728a923f6c0: EVIDENCE (raw, no verdicts)

Run by: EVIDENCE RUNNER agent, model Sonnet 5.5 (claude-sonnet-5-5), 2026-11-11 about 13:30 to 14:00 UTC (19:00 to 19:30 IST).
Worktree: /home/user/build/EV-P89-db0d9eb (HEAD verified db0d9eb4...; `git status` clean after all runs). Venv: /home/user/build/venv-p89. Machine: 4 cores, shared with another session's pytest (pr85) running at the same time.
Postgres: own cluster, PostgreSQL 16.15, port 56010, trust auth, 127.0.0.1, `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:56010/postgres`. Stopped (`pg_ctl -m fast stop`) and data dir deleted at the end.

## Failures and problems first

1. Full suite exit code 1: 10648 tests, 2 failed, 0 errors, 1 skipped (junit-full.xml). Both failures also fail on origin/main 2a8c2aac in the same environment (see section 1). Neither is in a mutation-runner file.
2. The console log `pytest-full.log` is cut off mid-run (last write ~6 minutes before the run ended) in every full run, and the mutation run's stdout log was cut the same way once. Cause not found (a test or child process in the suite seems to disturb the redirected output). Counts therefore come from the JUnit XML (`junit-full.xml`), which was written by pytest at the end, not from the log.
3. FIRST attempt used a Postgres cluster created with SQL_ASCII encoding (my mistake): it gave 150 failures and 27 errors, all identical on origin/main. Moved to `superseded-sql-ascii-cluster/`; superseded by the UTF8 cluster run below.
4. gitleaks: NOT RUN (`which gitleaks`: not installed; I did not look for a download). Substitute only: a regex grep of the added lines of `git diff origin/main...HEAD` for AWS key ids, PEM private key headers, ghp_/sk-/xox tokens found no hit other than allowed EXAMPLE literal (none printed). This is not equivalent to gitleaks.
5. The PR's new test file `tests/test_mutation_runner_keywords.py` cannot even be imported against origin/main source (ImportError, section 4), so "fails on old code" per individual test was NOT measured for it; only the whole file's import failure and the mutation sample were.
6. Not run: the FULL mutation list (217 mutants; 155 keyword mutants per the file header). Only a 60-mutant sample ran (as briefed). CodeQL, SonarCloud, CodeRabbit not run (CI services). Windows not run.
7. 6 temp folders of the form `/tmp/mutants_*` and `/tmp/mutant_ini_*` remain in /tmp (created 13:57, the time of my run of the PR's keyword tests against the OLD runner). I did not delete them because I could not prove every one is mine.

## 1. Full suite (Postgres tests included)

Command: `UV_PROJECT_ENVIRONMENT=/home/user/build/venv-p89 HADAVIN_TEST_PG_DSN=... uv run --all-extras --group test pytest -v -p no:cacheprovider -rs --junitxml=junit-full.xml > pytest-full.log 2>&1; echo $? > pytest-full.rc`
Exit code: 1 (pytest-full.rc). Duration 5m58.9s wall (pytest-reported 355.5s). Files: pytest-full.rc, pytest-full.time, junit-full.xml, failures-list.txt, pytest-full.log (truncated, see above).
Counts: tests 10648, failures 2, errors 0, skipped 1.
Skip (1): tests/contracts/test_llm.py, reason "Stubber refuses a malformed Converse shape before the kind sees it".
Failures (2):
- tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in: `AssertionError: a quadratic function must be flagged` (a timing test; the machine was loaded by another session).
- tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]: `could not establish connection ... socket "/var/run/postgresql/.s..."`: my cluster listens on /tmp sockets, the dblink test connects to the default socket path (environment difference of my cluster).
Rerun of those two files on the PR head and on a clean checkout of origin/main (2a8c2aac89f8, base venv venv-p89-base): `pytest -q tests/test_migration_numbers.py tests/demo_askdata/test_validate_harm.py`, 386 tests each, 2 failures each, the same 2 tests, same messages (pytest-rerun-2failures-PR.log / -base.log, junit-rerun-PR.xml / junit-rerun-base.xml; the .log files are the cut-off console output, the .xml files are complete).

## 2. Lint, format, security, guards

- `uv run --all-extras --group test ruff check` -> exit 0 (ruff-check.log).
- `uv run --all-extras --group test ruff format --check` -> exit 0 (ruff-format.log).
- bandit: not in the venv (`python -m bandit`: No module named bandit). Ran `uv run --with bandit bandit -ll -r src tools` (bandit 1.9.4, the version pinned in pyproject's `scan` group) -> exit 0 (bandit.log). Summary: High 0, Medium 0, Low 12 (low is below the `-ll` threshold and not reported as issues).
- Repo guard: `python tools/scan_repo.py` -> exit 0, no output besides the uv warning (scan_repo.log). The guard tests tests/test_repo_rules.py, test_lockin_guard.py, test_scan_repo.py, test_migration_numbers_guards.py are part of the full suite above (no failure among them).

## 3. Mutation sample on the changed module

Script: sample_mut.py (in this folder), imports the PR's mutant list `tests/mutation_runner_mutants.py` (217 mutants), seed 89, samples 45 of the keyword-test mutants and 15 of the others (60 total), and runs the PR's own `tools.mutation_runner.run_mutants` with tests [tests/test_mutation_runner.py, tests/test_mutation_runner_keywords.py], extra_dirs tests/fixtures and tools, conftest tests/conftest.py, no database variable set.
Result: exit 0, 3m10s, "60 of 60 good; problems: []". 59 KILLED, 1 CRASH (the "a truncated junit stops the run" mutant, which declares allow_crash). The full per-mutant list (name, verdict, killing test) is in mutation-sample-results.txt (the console log mutation-sample.log has the last lines). `git status` of the worktree was clean afterwards (no leftover mutation in src/).

## 4. PR tests against the OLD source (origin/main 2a8c2aac src and tools, PR tests overlaid)

Built a temp tree from `git archive` of origin/main plus the PR's `tests/`; checked src/ and tools/ identical to origin/main and that `hadavin_sdk.testing.mutation` and `tools.mutation_runner` import from that tree. Tree deleted afterwards.
- tests/test_mutation_runner_keywords.py: collection ERROR, `ImportError: cannot import name 'PASS_ENV_ALLOWED' from 'tools.mutation_runner'`, so the whole new file fails on the old code (no per-test result possible).
- tests/test_mutation_runner.py: 59 tests, 3 failed: test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on, test_a_truncated_junit_marks_the_mutant_error_and_the_run_goes_on (both `module 'tools.mutation_runner' has no attribute 'read_junit'`), test_the_manifest_pins_the_files_a_demo_copies (hash pin: "changed: re-sync the demos...").
- tests/test_mutation_runner_meta.py: 6 tests, 1 failed: test_g_every_search_string_occurs_exactly_once_in_the_file_it_targets (`runner: the child inherits the whole environment: the search string occurs 0 times`).
Files: junit-old-src-*.xml, pytest-old-src-*.log, junit-PRtests-on-old-src.xml, pytest-PRtests-on-old-src.*.

## Not checked
Full 217-mutant run; per-test fail-on-old for the 134+ keyword tests; CodeQL/Sonar/CodeRabbit; Windows behaviour; gitleaks proper; the cause of the truncated console logs. Earlier partial note by the lead is kept as RESULTS-lead-partial-earlier.md.

## Cleanup done
Own Postgres stopped and its data dir removed; temp worktree EV-P89-base removed with `git worktree remove`; temp tree EV-P89-oldsrc deleted; venv /home/user/build/venv-p89-base kept (disk only). No process of mine left running. Nothing committed or pushed.

## Lead note 2026-11-11 (after the runner's report)
- Lead re-read junit-full.xml: tests 10648, failures 2, errors 0, skipped 1, time 355 s; the two failing tests are tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in (known flaky on main, own fix branch) and tests/demo_askdata/test_validate_harm.py [dblink-connect] (needs PGHOST/PGPORT/PGUSER on the server; environment). Mutation sample file: "60 of 60 good".
- REMOVED from the repository tree (kept on the cloud machine only, /home/user/build/evidence-raw/PR89-db0d9eb): junit-full.xml and the folder superseded-sql-ascii-cluster/. Reason: gitleaks 8.30.1 flags 353 strings in them (test-made fake credentials and random passwords of the deleted throwaway test database printed in raw failure output). They were pushed in earlier commits of core/cloud-handover before gitleaks was installed here: see questions-for-lead.md.
