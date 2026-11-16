# Timing-helper fix: raw evidence, round 2 (STOPPED EARLY by lead order)

Evidence runner: records only, no judgement. Model = Fable 5.2. Branch `core/fix-timing-harness-flake`, head
`a8c269c8a3482d3673307f33d04bbee013eacbce`; base `origin/main` `2a8c2aac`; previous reviewed head `fa3f8c1b`.
Run 2026-11-11 16:06 to 16:20 UTC (21:36 to 21:50 IST), 4-processor shared machine. The builder's report was not read.
Raw logs: `/home/user/build/evidence-raw/flaky-a8c269c/` (folders `s1-head`, `s1-main`, `s2` ... `s11`). Scripts:
`/home/user/build/ev-flaky-r2-scripts/`. Every test command ran with the seven cloud and token variables removed (`env -u ...`),
Python 3.13.18, venv `/home/user/build/venv-evflaky2` (`uv sync --all-extras --group test`, exit 0).

## Not run, failed, or weakened (read first)

| Item | State |
|---|---|
| Step 10 (20 runs of `pytest -m perf tests/test_k5_perf.py tests/test_migration_numbers.py` on the head) | NOT RUN: the lead ordered a stop before it was queued |
| Step 10, extra 10 runs beside 4 busy loops | NOT RUN: step 4 had already used 215 of the 240 seconds of deliberate load allowed |
| Step 11 (measured big/small ratio of every real case) | NOT RUN to the end: started 16:18:32 UTC in a heavy slot, stopped by me after about 45 s on the lead's order; it prints only at its end, so no ratio was kept. Script ready: `ev-flaky-r2-scripts/s11.py` (never completed once, so untested) |
| Step 12, wall time next to processor time of one big call | NOT RUN (it is the last part of the step 11 script) |
| Step 12, the two greps | RUN, see below |
| Step 3, head against main durations | WEAKENED: the head's `test_k5_perf.py` run and the head's whole `-m perf` run overlapped my own step 4 load (8 busy loops, 16:13:03 to 16:16:38 UTC) and my own full-suite run; the main runs started after the load stopped. The two duration columns are NOT a like-for-like comparison. A clean repeat was planned and not done |
| Step 1 on origin/main | The one flaky test FAILED in 19 of 30 runs (this is the base, not the head) |
| Step 3 on origin/main | 1 failed (the same flaky test) in the file run and in the whole `-m perf` run |
| My slip | The first step 7 script recorded the exit code of a `date` call instead of pytest's (it showed 0). Re-run with the exit code saved on its own line; the wrong first attempt is kept in `s7-first-attempt-wrong-rc-recording/` |
| Step 9, gitleaks on this evidence folder | see the last section |
| Postgres setup detail | `initdb -A trust` gives trust on the local socket and `::1` as well as 127.0.0.1; the server listened on 127.0.0.1 only |

## Step 1: the flaky test and its siblings, separate pytest processes

Test names on the head (`--collect-only -k "timing_harness or stand_in"`, 4 of 136 collected):
`test_the_timing_harness_flags_a_quadratic_stand_in`, `test_the_timing_harness_passes_a_linear_and_an_n_log_n_stand_in[linear]`,
`...[n-log-n]`, `test_the_timing_harness_flags_a_quadratic_stand_in_that_is_fast_on_the_small_input`.

| Where | Command (after `python -m pytest -q -p no:cacheprovider`) | Runs | Exit 0 | Exit 1 | Load (1 min) start / middle / end | First assertion line of each distinct failure |
|---|---|---|---|---|---|---|
| head a8c269c | `tests/test_migration_numbers.py -k "timing_harness or stand_in"` | 60 | 60 | 0 | 3.50 / 4.70 / 3.79 | none |
| origin/main | `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` | 30 | 11 | 19 | 3.79 / 4.22 / 4.03 | `E       AssertionError: a quadratic function must be flagged` (19 times, line 836) |

Head: each of the 4 tests passed 60 of 60. Seconds per test on the head (min / median / max): quadratic 1.20 / 1.29 / 2.44;
linear 0.31 / 0.39 / 0.74; n-log-n 0.29 / 0.32 / 0.73; quadratic-fast-small 0.30 / 0.37 / 0.70. On main the one test took
0.53 / 0.57 / 0.70. Main exit codes in run order: `0 1 1 1 1 1 1 1 1 0 0 0 0 1 0 1 0 1 1 0 1 1 1 1 0 1 1 0 0 1`.
The machine load during step 1 was about 4, not the "about 10" of the brief; my own full-suite run was queued, then running from 16:11:09.

## Step 2: `tests/test_timing_fixture.py` on the head, 20 runs

20 runs, exit code 0 twenty times; 80 tests each, every test passed 20 of 20; no run differed in result. Process wall
seconds min 1.07, median 1.20, max 1.47. Load 4.03 / 4.33 / 4.40. Per-test seconds: `repeat-run-tables.md`.

## Step 3: the real users of the helper, once each, `--durations=15`

Files that import `tests/fixtures/timing.py` (grep over tests, tools, src): `tests/test_migration_numbers.py:15`,
`tests/test_k5_perf.py:28`, `tests/test_timing_fixture.py:14`; `tests/migration_numbers_mutants.py` names it as a mutation target.
How CI runs these (`.github/workflows/ci.yml` lines 92, 100): the main step is `pytest -q -m "not live and not perf" -rs`; the
timing tests run in their own step `pytest -q -m perf -rs` with `HADAVIN_TEST_PG_DSN` set. I used `-m perf` with the Postgres variables set.

| Run | Head: result, seconds, exit | origin/main: result, seconds, exit |
|---|---|---|
| `tests/test_migration_numbers.py -m perf` | 5 passed, 10.1 s, exit 0 (load 3.9, before my load step) | 1 failed 1 passed, 1.9 s, exit 1 (load 10.1 falling, after my load step) |
| `tests/test_k5_perf.py -m perf` | 8 passed, 121.4 s, exit 0 (load 3.9 rising to 10.1: MY load step ran beside it) | 8 passed, 26.0 s, exit 0 (load 9.7 falling to 8.1, no busy loops) |
| `tests/test_timing_fixture.py` | 80 passed, 0.81 s, exit 0 | 10 passed, 0.03 s, exit 0 |
| whole CI timing step `-m perf` | 31 passed, 188.5 s, exit 0 (entirely beside MY load step) | 1 failed 27 passed, 57.3 s, exit 1 (load 8.1 falling to 5.9) |

Slowest tests, seconds (head file run / main file run; see the warning above, the head figures were taken under my own load except the first two rows):

| Test | Head | origin/main |
|---|---|---|
| `test_lexer_is_linear` | 7.86 | 1.35 |
| `test_the_timing_harness_flags_a_quadratic_stand_in` | 1.21 | 0.54 (failed) |
| `test_no_redaction_pattern_is_super_linear_on_its_own_keywords_repeated` | 95.48 (116.35 in the whole `-m perf` run) | 12.72 (14.95) |
| `test_the_harness_flags_a_quadratic_pattern_and_passes_a_linear_one` | 11.18 (16.75) | 6.08 (5.56) |
| `test_redact_untrusted_end_to_end...[curl-u]` | 3.79 | 2.31 |
| `...[zero-width]` | 3.36 | 0.85 |
| `...[fullwidth]` | 2.40 | 1.09 |
| `...[password]` | 1.75 | 0.41 |
| `...[json-escape]` | 1.31 | 0.52 |
| `test_the_slowest_measured_shape_at_the_cap_stays_under_a_ceiling` | 2.13 | 1.99 |

## Step 4: deliberate load, one heavy slot

`heavy.sh timeout 240 s4-inner.sh`: slot wait 0 s. 8 busy loops (`python -c "while True: pass"`, each under `timeout 240`)
ran 16:13:03 to 16:16:38 UTC (215 s); 8 alive at the end of the runs, 0 alive after the stop; exit 0.
14 runs of the head's 4 stand-in tests fitted: exit 0 fourteen times, each test passed 14 of 14, 0 failures.
Load (1 min) before each run rose from 4.56 to 13.10; from run 5 on it was 10.7 to 13.1. Process seconds min 5.1, median 14.0, max 27.5.
Also running at that time and mine: the full suite (step 6) and step 3 on the head. Rows: `repeat-run-tables.md`.

## Step 5: the branch's own mutant list

`heavy.sh python tests/migration_numbers_mutants.py`: queued 16:08:35, slot 16:12:25 (wait 230 s), 38 s, exit 0.
Last line: `54 of 54 good; problems: []`. Rows: 51 `ok KILLED`, 3 `ok CRASH`, no other row. The 3 CRASH rows:
`fix1: a missing text raises KeyError`, `o100: statement_text returns the bare text, not the pair`,
`timing: a case that cannot be timed stops the sweep`. Worktree after the run: 0 changed files. All rows: `mutants-rows.md`.
No hand-made mutation was done (a copy of the worktree was not needed).

## Step 6: full suite once on the head, and the static checks

`heavy.sh ... pytest -q -p no:cacheprovider -m "not live and not perf" -rfEs --durations=15 --junitxml=...` with own Postgres 16.15
on port 56191: queued 16:07:29, slot 16:11:09 (wait 220 s), 351 s, exit 0. From the XML: 10595 tests, 0 failures, 0 errors,
1 skipped (10594 passed); pytest line `10594 passed, 1 skipped, 31 deselected in 348.08s`. Load 4.33 at start, 10.08 at end
(my load step ran beside its second half). The skip: `tests/contracts/test_llm.py:95`
`test_a_malformed_answer_is_a_provider_error[bedrock]`: "Stubber refuses a malformed Converse shape before the kind sees it".
The 31 deselected (timing) tests ran in step 3's whole `-m perf` run: 31 passed, exit 0.

| Check | Exit | Output |
|---|---|---|
| `ruff check` | 0 | All checks passed! |
| `ruff format --check` | 0 | 322 files already formatted |
| `uv run --with bandit bandit -ll -r src tools` | 0 | 0 issues shown at this level; totals Low 12, Medium 0, High 0 |
| `python tools/scan_repo.py` | 0 | empty output |
| suppression grep on `git diff origin/main...a8c269c8` | 0 | 2 hits, both the letters "nosec" inside the word "nanosecond": diff line 95 `+nanoseconds: with the real clock only a function that does next to nothing gets there; the tests reach it with a` and line 877 `+    )  # one call: a nanosecond, so the largest batch allowed is still far too short` |

## Step 7: fail-before (only the head's `tests/test_timing_fixture.py` laid over an exported copy)

| Tree | Exit | Result | Collection errors |
|---|---|---|---|
| fa3f8c1b + head test file | 1 | 36 failed, 44 passed (80) | none |
| origin/main + head test file | 1 | 79 failed, 1 passed (80) | none |

Per test and first failure lines: `fail-before-table.md`. On fa3f8c1b these tests failed in every case: smallest exponent (3),
big run not a time (5), sizes refused (6), gap of exactly four, empty unit, one call measured to its true time (5), batched to
batch length, pause while sized, slow call run once, two sizes take turns, collector off, clock is processor time, sweep names
each case; partly: pause in four of five batches (2 of 3 failed), slow spell over several batches (6 of 8 failed).

## Step 8: clock facts, verbatim

See `clock-facts.md`. In short, as printed: both clocks `clock_gettime(...)`, resolution 1e-09, monotonic;
main thread sleeping 1.0 s: process time 0.0001 s; a busy second thread beside a 1.0 s sleep: wall 1.0120 s, process time 0.7021 s
(thread time of the timed thread 0.0001 s); a child process burning 1.0 s of processor inside the timed section, waited for:
wall 1.1834 s, process time 0.0003 s.

## Step 12 (greps only)

`tests/test_k5_layers.py` exists on the head. `grep -n "perf_counter\|process_time\|timing\."` gives: `212: t = time.perf_counter()`,
`214: assert time.perf_counter() - t < 20`. It does not import the helper.
Other test files with `time.perf_counter` next to an assertion or a best-of (file:line): `tests/test_k5_fixes2.py:192,195` (< 5.0);
`tests/warden_port/test_redaction_review2.py:97,99` (< 15) and `:133,135`; `tests/test_k5_perf.py:119,121` (< 30.0);
`tests/test_k5_fixes6.py:134,136`; `tests/test_migration_numbers_guards.py:340,342` (< 5); `tests/test_g4_parity.py:263,266` (< 1.0);
`tests/test_runmap_partial_escape.py:37,39`. Importers of the helper are listed in step 3.

## Step 9: gitleaks

`gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..a8c269c8" <head worktree>`: exit 0, 3 commits scanned, no leaks found.
`gitleaks dir --redact --no-banner --exit-code 0 <this folder>` (run before this line was filled in): exit 0, no leaks found.

## Left on the machine for the agent that resumes

Kept on purpose: worktrees `/home/user/build/EV-flaky-a8c269c` and `/home/user/build/EV-flaky-main` (both clean), venv
`/home/user/build/venv-evflaky2`, stopped Postgres data folder `/home/user/build/pg-evflaky2`, exported copies
`/home/user/build/EV-flaky-fb-fa3f8c1` and `/home/user/build/EV-flaky-fb-main`. Stopped: every process I started (0 left), Postgres on 56191.
