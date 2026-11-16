# Raw evidence: branch core/fix-timing-harness-flake, head fa3f8c1b3966e2710a224bbdf3a8e95005f16428

EVIDENCE RUNNER record. It lists what was run and what came out. It contains no judgement and no fixes.
Model: Fable 5.2. Date: 2026-11-11, 14:24 to 15:05 UTC (19:54 to 20:35 IST). Machine: 4 cores, shared with other agents.
Base compared: origin/main 2a8c2aac89f83dd0a45af0412563b59ff4fe5632. Changed files on the branch: CHANGELOG.md,
tests/fixtures/timing.py, tests/migration_numbers_mutants.py, tests/test_k5_perf.py, tests/test_migration_numbers.py,
tests/test_timing_fixture.py (no file under src/ differs).
Raw logs and JUnit XML: /home/user/build/evidence-raw/flaky-fa3f8c1/ (not in the repository).
Every test command ran with `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL
-u GH_TOKEN -u GITHUB_TOKEN -u CLOUDSDK_AUTH_ACCESS_TOKEN` and the interpreter of /home/user/build/venv-evflaky
(`uv sync --all-extras --group test`, exit 0). "Load" is the 1, 5 and 15 minute load average from `uptime`.

## Failures and things to read first

1. Step 2, branch, under a deliberate overload (4 busy python loops started by this runner): 2 of 30 runs failed
   (pytest exit 1). Run 2: `test_the_timing_harness_passes_a_linear_and_an_n_log_n_stand_in[n-log-n]` failed with
   "AssertionError: _n_log_n is linear enough and must not be flagged" (a linear-enough stand-in was flagged).
   Run 18: `test_the_timing_harness_flags_a_quadratic_stand_in` failed with "AssertionError: a quadratic function
   must be flagged" (a quadratic stand-in was missed). Load during that block: 7.12 at start, 10.10 in the middle,
   10.85 at the end, on 4 cores; other agents' jobs were also running. File: step2-branch-overload-30-counts.txt.
2. Step 3: the redaction-pattern sweep `test_no_redaction_pattern_is_super_linear_on_its_own_keywords_repeated`
   took 77.01 s on the branch and 16.25 s on main (one run each; load 10.18 at the branch run, 11.42 at the main run).
   In the full suite (step 7) the same test took 75.61 s. `pytest -m perf tests/test_k5_perf.py` as a whole:
   98.61 s on the branch, 33.76 s on main.
3. Step 7 conditions: the bounded wait reached its 15 minute cap with 3 or more pytest processes still running, and
   the full suite was started anyway. From 14:52:41 UTC four busy loops of another session
   (`/home/user/build/venv-flaky/bin/python -c "while True: pass"`, not started by this runner, not touched) ran
   beside the whole full suite; load was 5.27 at its start and 14.18 at its end. The suite still ended with exit 0.
4. The count from `pgrep -fc "pytest"` includes this runner's own shell, because the shell's command text contains
   the word; the true number of other pytest processes was lower by 1 or 2. Not corrected.
5. Step 1 and step 4 on the main worktree imported the package `hadavin_sdk` from the branch worktree (the venv's
   editable install points there). No file under src/ differs between the two commits, so the code is the same text.
6. Step 5 ran each planted change once, not repeatedly.
7. gitleaks ran with `--exit-code 0` as the brief says, so its exit code is 0 whatever it finds; the finding is the
   log line "no leaks found".

## Not run

- No repeat of the 100-run and 30-run blocks on a quiet machine: the machine was never quiet (load 3.2 to 14).
- Reruns of failing files on main for step 7: not needed, the full suite had no failure.
- CodeQL, SonarCloud, CodeRabbit and the GitHub CI run: not part of this brief.
- The builder's report and logs were not read.

## Step 1. Baseline on origin/main, the single test, 30 separate pytest processes

Command (30 times, in /home/user/build/EV-flaky-main):
`python -m pytest -q -p no:cacheprovider --junitxml=run-N.xml "tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in"`

| result | runs |
|---|---|
| passed (exit 0) | 11 |
| failed (exit 1) | 19 |

First failure line: "AssertionError: a quadratic function must be flagged".
Load: start 3.19 3.71 3.86; middle 3.44 3.74 3.87; end 3.77 3.80 3.89. Took 30 s.

## Step 2. Branch, harness stand-in tests

Command: `python -m pytest -q -p no:cacheprovider --junitxml=run-N.xml tests/test_migration_numbers.py -m perf -k timing_harness`
("4 passed, 132 deselected" in the probe run). The four tests selected:
- test_the_timing_harness_flags_a_quadratic_stand_in
- test_the_timing_harness_passes_a_linear_and_an_n_log_n_stand_in[linear]
- test_the_timing_harness_passes_a_linear_and_an_n_log_n_stand_in[n-log-n]
- test_the_timing_harness_flags_a_quadratic_stand_in_that_is_fast_on_the_small_input

| test | 100 runs, no load of our own: passed / failed | 30 runs, 4 busy loops of our own: passed / failed |
|---|---|---|
| flags_a_quadratic_stand_in | 100 / 0 | 29 / 1 |
| passes ... [linear] | 100 / 0 | 30 / 0 |
| passes ... [n-log-n] | 100 / 0 | 29 / 1 |
| flags_a_quadratic ... fast_on_the_small_input | 100 / 0 | 30 / 0 |
| pytest exit codes | 0: 100 | 0: 28, 1: 2 |

Load, 100 runs (14:26:07 to 14:29:30 UTC): start 3.77 3.80 3.89; middle 5.89 4.45 4.11; end 7.21 5.39 4.49.
Load, 30 runs under overload (14:29:38 to 14:32:29 UTC): start 7.12 5.41 4.50; middle 10.10 6.80 5.08; end 10.85 7.82 5.58.
The 4 busy loops were `python3 -c "while True: pass"`, started 3 s before the first run and killed after the last;
a check after the kill found none of them alive.

## Step 3. Durations (`--durations=0`), one run each, with the Postgres DSN set

| command | branch | main |
|---|---|---|
| `pytest tests/test_timing_fixture.py` | exit 0, 38 passed in 0.98 s | exit 0, 10 passed in 0.05 s |
| `pytest -m perf tests/test_k5_perf.py` | exit 0, 8 passed in 98.61 s | exit 0, 8 passed in 33.76 s |

| test in tests/test_k5_perf.py | branch s | main s |
|---|---|---|
| test_no_redaction_pattern_is_super_linear_on_its_own_keywords_repeated (the sweep) | 77.01 | 16.25 |
| test_the_harness_flags_a_quadratic_pattern_and_passes_a_linear_one | 8.86 | 8.89 |
| test_the_slowest_measured_shape_at_the_cap_stays_under_a_ceiling | 3.77 | 1.91 |
| end_to_end ... [curl-u] | 3.22 | 3.62 |
| end_to_end ... [fullwidth] | 2.04 | 0.93 |
| end_to_end ... [zero-width] | 1.83 | 0.89 |
| end_to_end ... [json-escape] | 1.15 | 0.52 |
| end_to_end ... [password] | 0.70 | 0.71 |

Load: 10.18 7.86 5.65 when the branch runs began; 11.42 8.88 6.24 when the main runs began; 10.02 8.80 6.31 at the end.

## Step 4. Fail-before: the branch's test files on clean origin/main

Copied onto the main worktree: tests/test_k5_perf.py, tests/test_migration_numbers.py, tests/test_timing_fixture.py
(tests/fixtures/timing.py stayed as main has it). Command:
`python -m pytest -q -p no:cacheprovider -rfEs --junitxml=A.xml tests/test_k5_perf.py tests/test_migration_numbers.py tests/test_timing_fixture.py`
Exit 1: 48 failed, 134 passed. A second run that also copied tests/migration_numbers_mutants.py gave the same 48
failures. The main worktree was restored after each (`git status --short` empty).

| file | failed | first error line (group) |
|---|---|---|
| tests/test_k5_perf.py | 7 | TypeError: '>' not supported between instances of 'float' and 'NoneType' |
| tests/test_migration_numbers.py | 5 | 4 x the same TypeError with 'NoneType'; test_lexer_is_linear: the same with 'tuple' |
| tests/test_timing_fixture.py | 36 | 12 x TypeError: is_superlinear() got an unexpected keyword argument 'clock'; 14 x AttributeError: ... no attribute 'seconds_per_call'; 7 x Failed: DID NOT RAISE ValueError; 1 x ZeroDivisionError; 1 x assert 0.048 == 1.2e-05 ± 1.2e-11; 1 x assert False |

Per-test list with the first line of each: step4-fail-before.txt.

## Step 5. Planted regressions on the branch (tests/fixtures/timing.py), one run each

| plant | change | harness selection (4 tests) | extra: tests/test_timing_fixture.py (38 tests) |
|---|---|---|---|
| (a) | `PER_SIZE = 3.0` to `PER_SIZE = 1000.0` | exit 1; failed: flags_a_quadratic_stand_in, flags_a_quadratic_stand_in_that_is_fast_on_the_small_input; passed: [linear], [n-log-n] | exit 1; 14 failed, 24 passed |
| (b) | `* t_small` to `* max(t_small, 0.004)` in `time_limit` (main's 4 ms floor) | exit 1; failed: the same two; passed: [linear], [n-log-n] | exit 1; 10 failed, 28 passed |

The file was restored with `git checkout --` after each; `git status --short` was empty after each and at the end.
Load at both: 8.15 8.50 6.34. Names of the failing tests: step5-planted.txt.

## Step 6. Mutants

`python tests/migration_numbers_mutants.py` in the branch worktree: exit 0, 43 s, last line "40 of 40 good; problems: []".
Rows: 38 "ok KILLED", 2 "ok CRASH" (fix1: a missing text raises KeyError; o100: statement_text returns the bare text,
not the pair). Every row: step6-mutants.txt. `git status --short` empty afterwards.

## Step 7. One full suite on the branch with the DSN

Postgres 16.15, own cluster (`initdb -E UTF8 --locale=C.UTF-8 -A trust`), port 56100, listen 127.0.0.1, socket
directory /tmp, started as the postgres user with PGHOST, PGPORT, PGUSER in the server's environment; stopped and
its data directory removed at the end.
Wait before the start: 900 s (the cap), then started anyway.
Command: `PGHOST=127.0.0.1 PGPORT=56100 PGUSER=postgres HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:56100/postgres
timeout 1500 python -m pytest -q -p no:cacheprovider -rfEs --durations=15 --junitxml=full.xml`
Exit 0 after 693 s (14:51:54 to 15:03:27 UTC). Last line: "10583 passed, 1 skipped in 684.32s (0:11:24)".

| from the XML | count |
|---|---|
| tests | 10584 |
| passed | 10583 |
| failures | 0 |
| errors | 0 |
| skipped | 1 |

Skip: tests/contracts/test_llm.py:95 `test_a_malformed_answer_is_a_provider_error[bedrock]`, reason "Stubber refuses
a malformed Converse shape before the kind sees it".
Load: start 5.27 5.80 5.88; end 14.18 13.04 9.93. Times of the timing tests in this run: step7-full-suite-counts.txt.

## Step 8. Lint and scans (branch worktree)

| command | exit | last line |
|---|---|---|
| `uv run --all-extras --group test ruff check` | 0 | All checks passed! |
| `uv run --all-extras --group test ruff format --check` | 0 | 322 files already formatted |
| `uv run --with bandit bandit -ll -r src tools` | 0 | No issues identified. (severity Medium 0, High 0) |
| `python tools/scan_repo.py` | 0 | (no output) |
| `gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..fa3f8c1b" <worktree>` | 0 | 1 commits scanned; no leaks found |
| `gitleaks dir --redact --no-banner --exit-code 0 handover/evidence/timing-harness` | 0 | first run: "leaks found: 1" (generic-api-key rule, step7-full-suite-counts.txt line 29: a test id in the slowest-15 excerpt holding a made-up password-shaped fixture value); that excerpt line was replaced by a note; second run: "no leaks found" |

## Cleanup

Own busy loops: stopped. Own Postgres: stopped, data directory removed. Both temporary worktrees: clean
(`git status --short` empty) and removed. No commit, no push, no sub-agent, no spend. Processes of other sessions
were not touched.
