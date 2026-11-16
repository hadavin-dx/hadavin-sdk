# EVIDENCE RUNNER results, Q8a-2, head c19d87dc0588a27be7af234f2577c1b73eacf205 (fix batch 4)

Recorded only. Nothing judged, nothing fixed. Clock 19:39 to 20:38 UTC (01:09 to 02:08 IST). Raw logs: /home/user/build/evidence-raw/q8a2-c19d87dc/. Machine: 4 cores, load average 1.5 to 8.8 during the runs (other agents), so timings are not quiet-machine numbers. Queue wait for the heavy slots: full suite about 13 min, mutant run about 17 min.

## Read first: what failed, differs, or was not run

1. SETUP DEVIATION: `uv sync --locked --no-build ...` fails for this project (`hadavin-sdk` editable: "marked as --no-build but has no binary distribution"). I ran `uv sync --locked --all-extras --group test` (same lock, without `--no-build`) in my own venv. Both logs are in the raw folder (sync.log, sync2.log).
2. Mutant script as written by the builder points at the builder's folder and venv. I ran an ADAPTED COPY (scripts/builder-mut-adapted.py; only REPO and UV_PROJECT_ENVIRONMENT changed, mutants unchanged). `.github/workflows/ci.yml` has no mutant runner of its own; the only mutant run named by the ticket is `tests/stage_mutants.py`.
3. Full suite run once (rc 0). The known flaky timing test failed on the head in all 3 solo runs and on main in 2 of 3 (item 9). It passed inside the full run.
4. The burst test on the OLD source (3210f93a) fails when run alone (5 of 5) but passed in 2 of 3 whole-file runs of the same old source. So its result on old code depends on how it is run (details item 7).
5. The held-connection observation (45/50, 47/50 closed) was NOT reproduced: 100 percent closed in all 15 head patterns and all 9 old-source patterns (item 8).
6. Not run: CI, CodeQL, SonarCloud, CodeRabbit; the ci.yml `perf` job and security-job steps other than bandit and gitleaks (pip-audit, Semgrep, zizmor, Trivy: not named by the ticket, need network tools); the merge with the Q8a-1 branch; the real Slack kind over a socket. The diff was not reviewed.
7. In my probes a failed handler writes one ERROR line and also one DEBUG line with the same text (the stdlib error path). Recorded, not judged.

## Table (failures first)

| # | item | command / script | exit | result |
|---|---|---|---|---|
| 9 | flaky timing test `test_the_timing_harness_flags_a_quadratic_stand_in`, alone with all 3 slots locked | flock x3 pytest, 3 runs each | head 1,1,1; main 1,0,1 | head: 3 failed, 0 passed; origin/main: 1 passed, 2 failed (flaky-summary.txt) |
| 7 | burst test on old src 3210f93a, alone | pytest -k burst, 5 runs | 1 x5 | failed 5 of 5 (`assert 21.1 < (1.0 + 1.5)`, the longest connection lived about 21 s); head: passed 5 of 5 in 1.8 s each (burst.txt) |
| 7 | whole callback file with head tests on old src 3210f93a | pytest -rA, 3 runs | 1 x3 | 13, 14, 13 failed; burst test: passed, failed, passed (callback-old3210-results.txt is run 1) |
| 7 | fail-before on origin/main 2a8c2aa: the 4 changed test files of the diff, main src | pytest | 1 | 31 failed, 238 passed, 2 errors (failbefore-main-tail.txt, failbefore-main-failed.txt). `test_q8a2_callback.py` and `test_p7_tick.py` do not collect on main, so 0 tests of them ran |
| 1 | changed files | `git diff --name-only origin/main...HEAD` | 0 | 15 files (item1-names.txt) |
| 2 | ruff | `ruff check` / `ruff format --check` over src tests demos tools | 0 / 0 | All checks passed; 319 files already formatted |
| 3 | bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | no issues (2 nosec warnings at tools.py:389, bandit.log) |
| 4 | repo scan | `python tools/scan_repo.py` | 0 | no output lines of findings |
| 4 | staged mutants | `python tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` |
| 4 | gitleaks | `gitleaks git --log-opts=origin/main..HEAD` | 0 | no leaks found |
| 5 | full suite | heavy.sh pytest -q -m "not live and not perf" -rs | 0 | `10817 passed, 1 skipped, 28 deselected in 305.75s`; the skip is tests/contracts/test_llm.py:95. Head and clean tree checked after (dirty=0) |
| 6 | receiver mutants (builder's list, adapted copy) | heavy.sh python3 -I builder-mut-adapted.py | 0 | baseline PASS (121 passed); 14 of 14 KILLED (mutants.log) |
| 7 | callback file on head | pytest -rA | 0 | 121 passed in 29.6 s |
| 8 | step 8 held connections, head, 5 runs | scripts/test_evq8a2f_load.py | 0 x5 | 50 of 50 closed after the bound in each of 3 patterns in each run (15 of 15), again 50 of 50 at +6 s |
| 8 | same script on old src 3210f93a, 3 runs | same | 0 x3 | 50 of 50 closed in each of 9 patterns |
| 8 | CHANGELOG measurement, 50 silent connections opened at once, bound 2 s | scripts/burst50.py, 5 runs each | 0 | head: 0 of 50 open at bound+0.5 s, longest 2.1 to 2.2 s; old src: 41 to 43 of 50 open at bound+0.5 s, still open when my 40 s read timeout ended (burst50.txt) |
| 8 | own hostile probes (path table, 7 handler error kinds, leave-before-answer, reset in body, hostile first line, Content-Length forms, slow body) | scripts/probe_logging.py | 0 | see below |

## Item 6: the fix-list mutants (all KILLED, first failing test)

m1 type decides handler log, m1b handler failure not logged, m1c handle_error type only decides, m2 flag not set (second error line), m2b log after the answer (lost on write timeout), m4a no cap, m4b cap six, m4c no seen-set, m4d no dots, m4e hang-up context ignored, m3a hand-written printable range, m3b C0 only, m5 exception argument logged raw, m6 backlog back to the standard library's 5. Each ran with `-x`, so only the first failing test is named in mutants.log. m6 is killed by the burst test.

## Item 7: the new tests of this round, on head and on old source 3210f93a (head's test file, old src)

On head: all 121 pass. On old src, FAILED in all 3 whole-file runs: the five `test_a_handler_failure_is_error_whatever_its_kind_also_a_connection_error_of_a_store` cases, `test_a_handler_failure_is_logged_once_even_when_the_answer_cannot_be_written`, `test_the_listen_backlog_is_the_configured_one_not_the_standard_librarys_five`, `test_a_handler_failure_and_a_hang_up_in_one_request_are_one_error_line`, `test_a_chain_of_errors_is_named_to_five_kinds_and_then_dots`, `test_a_chain_that_loops_back_on_itself_stops_at_the_repeat`, `test_a_chain_of_one_error_that_is_its_own_context_does_not_loop`, `test_the_error_line_is_what_the_changelog_says_it_is` (the CHANGELOG error-line claim test), `test_log_message_shows_an_error_among_its_arguments_by_kind_only`. The burst test: see the table. Old-source run 2 had 14 failed (the burst test the 14th).
Against origin/main (new tests of the whole diff, listed in new-tests-on-main.txt): of 97 new test functions, 48 are not collected on main, 8 fail, 41 pass (the 41 are guard-scan plant tests whose scanner lives in the test file itself).

## Item 8: own probes on head (probe-head.txt; same script on old src in probe-old3210.txt)

- Path table: the configured path 200; `/slack/actions`, `/other`, `//channel/actions`, trailing slash, query string, upper case, `/`: all 404.
- Handler failure with RuntimeError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError, TimeoutError, OSError, ConnectionAbortedError: status 500 each; exactly 1 ERROR line each, text `a request ended with an error: <kind>`; the error message text never appears in any log line. On old src: 0 ERROR lines for 4 of these kinds (they were DEBUG), and for TimeoutError the message text appeared in a log line.
- Handler fails and the caller resets before the answer is written (RuntimeError, ConnectionRefusedError): 1 ERROR line (the handler's kind) plus a DEBUG line `ConnectionResetError while handling <kind>`. On old src the ERROR line named both kinds.
- Handler fine, caller resets before the answer: 0 ERROR lines, one DEBUG line. Caller resets in the body read: 0 ERROR, one DEBUG; same right after a failed request (flag not carried over).
- First line with an escape byte, CR and NUL: logged only at DEBUG, non-printable shown as `?`.
- Content-Length: 14 digits 413; `-1` 400; empty 400; header twice 400; 65537 413; 22 digits 413.
- Slow body, bound 1.5 s: connection closed after 1.51 s with no answer. Threads alive at the end: 1.

## Files

Scripts in scripts/ (env.sh.txt, builder-mut-adapted.py, burst50.py, probe_logging.py, test_evq8a2f_load.py: copy of the 3210f93 step-8 script, only change: it records every outcome of the closed-check and looks again at +6 s). Small raw excerpts beside this file.

Cleanup: own PostgreSQL 16 (port 56291) stopped and its folder deleted; no other process of mine is running. Worktree wt (head, clean) is left at /home/user/build/EV-q8a2-c19d87dc for the lead to remove; wt-old and wt-main (which held copied test files by design) are removed. Gitleaks on this folder: exit 0.
