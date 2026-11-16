EVIDENCE RUNNER report, Q8a-2 head c19d87dc0588a27be7af234f2577c1b73eacf205 (checked: HEAD matches, tree clean, dirty=0 after all runs). I recorded only; nothing fixed, nothing judged. Full summary: /home/user/hadavin-sdk/handover/evidence/Q8a-2/c19d87d/RESULTS.md (not committed or pushed; gitleaks on that folder exit 0). Raw logs: /home/user/build/evidence-raw/q8a2-c19d87dc/. Clock 19:39-20:38 UTC (01:09-02:08 IST). Load average 1.5 to 8.8 from other agents. Queue waits: full suite about 13 min, mutants about 17 min. R-numbers: none cited (no bible read; ran commands only).

WHAT FAILED / DIFFERED / NOT RUN (first)
1. Setup deviation: `uv sync --locked --no-build ...` fails here (editable hadavin-sdk has no binary dist). I used `uv sync --locked --all-extras --group test` (same lock, no --no-build).
2. Flaky timing test `test_the_timing_harness_flags_a_quadratic_stand_in`, alone with all 3 slots locked: head 3 failed of 3; origin/main 1 passed, 2 failed. It passed inside the full run.
3. Burst test on OLD src 3210f93a: fails alone 5 of 5 (`assert ~21.1 < 2.5`), but inside a whole-file run on old src it passed in 2 of 3 runs (failed in 1). On head: 5 of 5 pass alone (1.8 s each), and pass in the whole file.
4. The held-connection observation (45/50, 47/50) did NOT reproduce: step-8 script re-run 5 times on head = 50 of 50 closed after the bound in every one of 15 patterns, and again 50 of 50 at +6 s; the same script on old src 3210f93a 3 runs = 50 of 50 in all 9 patterns. My copy of the script records each outcome (closed / reset / still open) and looks again at +6 s; every outcome was `closed(b'')`. Earlier counts of 45 and 47 were taken at 19-20+ load; I did not find a cause.
5. CHANGELOG measurement (50 silent connections opened at once, bound 2 s, loopback) re-run 5 times each: head 0 of 50 open at bound+0.5 s, longest 2.1 to 2.2 s; old src 41 to 43 of 50 open at bound+0.5 s (my read timeout was 40 s, so they were still open at 40 s). The CHANGELOG says "8 to 25 of 50"; my number is different (different opening method: barrier).
6. Mutant runner: builder's /home/user/build/q8a2-fb4/mut.py points at the builder's folder and venv; I ran an adapted copy (only REPO and venv path changed). ci.yml has no mutant runner for this package; the ticket names only tests/stage_mutants.py.
7. Not run: CI, CodeQL, SonarCloud, CodeRabbit; ci.yml perf job and pip-audit, Semgrep, zizmor, Trivy (not named by the ticket); merge with Q8a-1; real Slack kind over a socket; the diff was not reviewed.
8. Observation: in my probes a failed handler writes 1 ERROR line plus 1 DEBUG line with the same text.

TABLE
| item | exit | result |
| 1 changed files (origin/main...HEAD) | 0 | 15 files |
| 2 ruff check / format --check (src tests demos tools) | 0 / 0 | all passed; 319 files formatted |
| 3 bandit -ll (src demos tools) | 0 | no issues |
| 4 scan_repo.py | 0 | no findings |
| 4 stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| 4 gitleaks origin/main..HEAD | 0 | no leaks |
| 5 full pytest (heavy.sh, not live, not perf) | 0 | 10817 passed, 1 skipped (tests/contracts/test_llm.py:95), 28 deselected, 305.75 s |
| 6 receiver mutants (builder's 14, adapted copy) | 0 | baseline PASS (121 passed); 14 of 14 KILLED: m1, m1b, m1c, m2, m2b, m4a-e, m3a, m3b, m5, m6 (m6 backlog back to 5 is killed by the burst test) |
| 7 tests/test_q8a2_callback.py on head | 0 | 121 passed in 29.6 s |
| 7 same file, head tests on old src 3210f93a (3 runs) | 1 x3 | 13, 14, 13 failed. Failed in all 3: the 5 `..._also_a_connection_error_of_a_store` cases (m1), `..._logged_once_even_when_the_answer_cannot_be_written` (m2), the listen-backlog test, `..._a_handler_failure_and_a_hang_up_in_one_request_are_one_error_line`, the chain-of-five-kinds, chain-loop and own-context tests (m4), `test_the_error_line_is_what_the_changelog_says_it_is` (CHANGELOG claim), `test_log_message_shows_an_error_among_its_arguments_by_kind_only` (m5). Burst test: passed / failed / passed |
| 7 fail-before on origin/main (4 changed test files of the diff, main src) | 1 | 31 failed, 238 passed, 2 errors; test_q8a2_callback.py and test_p7_tick.py do not collect on main. Of 97 new test functions: 48 not collected, 8 fail, 41 pass (guard plant tests whose scanner lives in the test file); list in new-tests-on-main.txt |
| 8 own probes on head (scripts/probe_logging.py; old src output too) | 0 | path table: configured path 200; /slack/actions, /other, //channel/actions, trailing slash, ?query, upper case, / all 404. Handler failure with 7 kinds (RuntimeError, ConnectionRefused/Reset/Aborted, BrokenPipe, Timeout, OSError): status 500, exactly 1 ERROR line each, kind only, message text never in a log line. Old src: 0 ERROR lines for 4 of those kinds (DEBUG only) and the TimeoutError message text appeared in a log line. Handler fails + caller resets before answer: 1 ERROR (handler kind) + 1 DEBUG. Handler fine + caller resets: 0 ERROR. Reset in body: 0 ERROR, also right after a failed request. Hostile first line (ESC, CR, NUL): DEBUG only, `?` shown. Content-Length 14 digits 413, -1 400, empty 400, twice 400, 65537 413, 22 digits 413. Slow body, bound 1.5 s: closed after 1.51 s, no answer |
| 8/burst 150-connection test | head 5x pass; old 5x fail | see items 3 and 5 above |

Cleanup: own PostgreSQL 16 (port 56291) stopped and its folder deleted; wt-old and wt-main removed; worktree /home/user/build/EV-q8a2-c19d87dc/wt (head, clean) is left for the lead to remove; no process of mine is running. Checkpoint note: /home/user/build/checkpoints/EV-q8a2.md. Own token use not measured.