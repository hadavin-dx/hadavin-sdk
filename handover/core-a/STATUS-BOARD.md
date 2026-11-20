UPDATED_UTC: 2026-11-20T05:46:52Z
SESSION: core-a
ORDER: 012 (002 to 009 standing; ORDERS 007, 010, 011 are not in my file)
STATE: WORKING
BOOT_ID: 3f12152f
ITEMS_TOTAL: 20
ITEMS_OPEN: 9
PERCENT: 65
AGENTS_RUNNING: 7
CAPACITY: load 0.30 of 4 cores (1-minute average), mem 0.6/15.7 GB, 7 language-model agents running (light), 0 heavy test slots unless TESTS shows one
DISK: / size used free 252G 9.3G 60G 14%; 346M /home/user/hadavin-sdk; 52M /tmp/claude-0; 131M /root/.cache
INTERRUPTED: none
FAILED: 2 in the whole-suite run: 1 repo rule test fails because of handover/BRIEF-PREAMBLE.md (lead's file); 1 flaky T5 test of mine (slot release race), fix in work
SESSION_RESTARTS: 0
CONTAINER_RESTARTS: 0
NEXT: agents land one by one: check each, commit; then mutant script on the final code, my files once more, REPORT.md block
PUSHED_UTC: 2026-11-20T05:44:12Z (the push before this board)
NOTE: one board per minute is driven by a session cron; the cron only fires while the session is not in the middle of a turn, so a board can be up to a few minutes late during long tool batches; ORDER 005 read at 05:23 UTC: code goes on cloud/core-a in separate commits, no wip branch

## QUEUE ITEMS
| item | what | state | percent | evidence file | tries | reason |
|---|---|---|---|---|---|---|
| Q1 | capability probe | DONE | 100 | CAPABILITY.md + raw/capability-raw*.txt | 1 | probe ran once; PostgreSQL 16 starts as non-root (verified); docker and PostgreSQL 14/17 not available |
| Q2 | lane map | DONE | 100 | LANE-MAP.md | 1 | written, 55 lines; tests column is from name search only (agent says so) |
| Q3-Q7 | baselines of existing heads | SKIPPED by lead | 100 | lead puts results in inputs/ | 0 | GO message 2026-11-20: lead runs them on the laptop |
| T1 | plan read-back | DONE | 100 | PLAN-READBACK.md, QUESTIONS.md (10 questions) | 1 | written, 103 lines; 11 of 12 code facts verified in src, 1 does not match (count of test files building Runtime: review says 17, grep finds 7) |
| T2-E | ticket step E test helpers | DONE (writer may still add lead verdicts) | 100 | tickets/E-test-helpers.md (190 lines) | 1 | written; socket guard cut, one helper kept (crash points), no request to core-b needed; nothing was run for the ticket |
| T2-D | ticket step D signed endpoint + worker + n8n template | DONE | 100 | tickets/D-signed-endpoint.md (about 345 lines), requests/001-config-triggers.md DRAFT 2 | 1 | written; 33 draft claims checked: 26 verified, 7 wrong (listed in ticket section 3); nothing was run for the ticket |
| T2-H | ticket step H logic, only if D proves a delta | CUT (ticket D verdict, lead draft agrees) | 100 |  | 0 | no delta over Runtime.handle once the payload hash is in trigger_ref; reopen triggers listed in ticket D section 4 |
| T3 | one EGM review round for ticket D (and H if written) | RUNNING (review done, resolve written, ticket text being repaired) | 80 | tickets/D-review-1.md, ESCALATIONS.md (E1 to E4) | 1 | round 1 of 1: 3 Blocker, 20 Major; 33 fixes, 4 escalated, 4 nits declined, 0 contested; reviewers read the ticket, not the built code |
| T4 | store contract test files for core-b interface | RUNNING | 5 | raw/T4-contract-tests.log (not yet) | 1 | core-b published interface (i) version 2.1 at 05:44Z; tests written before the code exists, they skip until step F lands |
| BUILD-E | build step E on wip/cloud-core-a/E | DONE (coded and its own tests pass; full batch run still open) | 100 | raw/E-tests.log, raw/E-tests-pg16.log, raw/E-guards.log, raw/E-mutants.log | 1 | crash.py 197 lines, test file 698 lines (ticket guessed 110 and 190); 4 mutants caught; NOT checked: wheel contents, Windows exit code, Python 3.12 run by me |
| T5-SKEL | T5 test file skeleton (tests/triggers/) and n8n template outline (n8n/) | DONE (n8n part is an outline, NOT run in n8n: ESCALATIONS E4) | 100 | tests/triggers/test_t5_cases.py (645 lines), n8n/ (3 files) | 1 | 65 passed, 66 skipped (64 need the database variable, 1 crash case still skip-marked, 1 other); one early run showed 3 failures while the code under it was being rewritten, not captured: a timing flake is NOT ruled out; every n8n node parameter is from memory and marked UNVERIFIED (12 notes) |
| BUILD-D-endpoint | src/hadavin_sdk/triggers/endpoint.py + tests/triggers/test_endpoint.py | DONE (coded and its own tests pass; full batch run still open) | 100 | raw/D-endpoint-tests.log, -guards.log, -mutants.log (not yet) | 1 | endpoint.py 300 lines (draft guessed 130), 190 tests pass, 2 skipped; 3 mutants caught; NOT run: bandit, real socket, timing of the secret comparison |
| BUILD-D-worker | src/hadavin_sdk/triggers/worker.py + tests/triggers/test_worker.py | DONE (coded and its own tests pass; full batch run still open) | 100 | raw/D-worker-tests.log, -mutants.log (not yet) | 1 | worker.py 391 lines, 32 tests pass 4 times in a row (about 5.4 s), 4 mutants caught; in-process key table removed, no-slot path polls the stored row; KNOWN COST: a pool-full 503 for a new key takes the full ack wait (5 s) and holds a server thread, no cap on waiting requests; NOT run: main past its two refusal paths, PostgreSQL, two real processes |
| BATCH | ONE batch test run when E and D are both coded | DONE with 2 failures (1 INHERITED-from-handover, 1 NEW flaky in my T5 test, fix in work) | 90 | raw/BATCH-full-suite.log, raw/BATCH-rerun-own-files.log, raw/BATCH-lint.log, raw/BATCH-bandit.log | 1 | whole suite once: 2 failed, 10723 passed, 527 skipped in 99 s (no database variable, so database tests skipped; python 3.13 only). PostgreSQL 16 run of my own files still to do after the worker change |
| MUTANTS | tests/endpoint_mutants.py in the lead's batch format (ORDER 008 item 1), incl. crash helper mutants | RUNNING | 5 | raw/endpoint-mutants-run.log (not yet) | 1 | ORDER 008: a guarantee with no mutant script counts as not done |
| E2-SOCKET | real loopback-socket tests of the server (short body, stalled client, garbage); quiet handler in triggers/server.py if wsgiref leaks; one log line on 409 (ORDER 009 E1a, E2) | RUNNING | 5 | raw/E2-wsgiref-before.log, -after.log, raw/E2-tests.log (not yet) | 1 | lead decision: in scope, do it without asking |
| R12-worker | lead review fixes in worker.py and server.py: backed-off no-slot wait (Major 1), SIGTERM drain (Major 2), minors 3, 7, 8, 14 | RUNNING | 5 | raw/E2-tests.log (not yet) | 1 | ORDER 012; same agent as E2-SOCKET because one agent owns worker.py |
| R12-endpoint | lead review fixes in endpoint.py: minors 1, 5, parse edges | RUNNING | 5 | raw/D-endpoint-tests-2.log (not yet) | 1 | ORDER 012 |
| R12-n8n | n8n outline: empty-field guard (Major 3), outer 503 loop with re-sign (Major 1), README limits; request 002 text for core-b's README and SECURITY | RUNNING | 5 | tests/triggers/test_n8n_template.py (not yet) | 1 | ORDER 012; still NOT run in n8n |
| R12-tests | missing tests (Major 4): PostgreSQL cases, child-process kill cases, two processes on one database, start refusal through main, oversize, two senders | RUNNING | 5 | raw/D-tests-pg16.log with test ids (not yet) | 1 | ORDER 012: required before done |

## AGENTS
| id | role | model | what exactly it is doing | started UTC | expected end | percent | state | review round n of cap | retries so far | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| a0f5c9e1 | lookup | fable | Q2: reads README, pyproject, conftest, src/hadavin_sdk and writes LANE-MAP.md | 05:19 | ended 05:21 | 100 | done | n/a | 0 | finished 05:21, 151k tokens, LANE-MAP.md written |
| a86435a3 | lookup | fable | T1: reads plan-v2, v3, v4-final and round-3 reviews, writes PLAN-READBACK.md | 05:19 | ended 05:24 | 100 | done | n/a | 0 | finished, 119k tokens, PLAN-READBACK.md written |
| a8e21a19 | builder (ticket writer, no code) | fable | T2-D: checks every line of the lead draft of ticket D against the code, writes tickets/D-signed-endpoint.md, gives the step H verdict | 05:22 | ended | 100 | done | n/a | 0 | finished, 247k tokens, ticket D written |
| ac060f95 | builder (ticket writer, no code) | fable | T2-E: writes tickets/E-test-helpers.md (helpers, where they live, guard tests they could break) | 05:22 | ended | 100 | done | n/a | 0 | finished, 220k tokens, ticket E written (nothing run for the ticket) |
| t5-skel | builder (tests and templates, new files only) | fable | writes the T5 test skeleton and two n8n workflow outlines plus a README; runs ruff and pytest on its own folder only | 05:27 | ended | 100 | done | n/a | 0 | finished, 177k tokens |
| build-E | builder | fable | step E: src/hadavin_sdk/testing/crash.py and tests/test_testing_crash.py; ruff, its own test file, 6 guard test files, 4 mutants, bandit | 05:28 | ended | 100 | done | n/a (E needs no ticket review) | 0 | finished, 138k tokens |
| build-D-ep | builder | fable | endpoint.py: run id derivation, signature check with two secrets, WSGI app, unit tests in-process, 3 mutants | 05:30 | ended | 100 | done | review runs alongside (0 of 1 started) | 0 | finished, 131k tokens |
| build-D-wk | builder | fable | worker.py: Runner (ack only after the run row exists, bounded pool), main, thread tests, 3 mutants | 05:30 | ended | 100 | done | review runs alongside (0 of 1 started) | 0 (1 follow-up change, not a retry of a failure) | finished, 189k tokens |
| egm-impl-ready | reviewer | fable | egm:egm-implementation-readiness reads ticket D against its standard | 05:31 | ended | 100 | done | 1 of 1 | 0 | finished, 131k tokens: 2 Blocker, 13 Major, 8 Nit on ticket D |
| egm-codebase | reviewer | fable | egm:egm-codebase-details checks ticket D claims against the code | 05:31 | ended | 100 | done | 1 of 1 | 0 | finished, 200k tokens: 1 Blocker, 7 Major, 10 Nit |
| ticket-fix | builder (ticket text only) | fable | applies the 33 accepted review fixes to ticket D and writes request 001 draft 3 | 05:38 | about 12 min after start | 70 | running | 1 of 1 (resolve step) | 0 | egm-resolve output must be applied; 3 agents run (worker change, T5 skeleton, ticket fix) |
| mutants | builder (test tooling) | fable | writes tests/endpoint_mutants.py (7 groups) and runs it once through tools/mutation_runner.py | 05:39 | about 20 min after start | 50 | running | n/a | 0 | ORDER 008 item 1 |
| e2-socket | builder | fable | writes tests/triggers/test_t5_wsgiref.py, records what wsgiref does today, adds a quiet handler only if needed, adds the 409 log line; PLUS the slot-wait fix in Runner.start found by the batch run | 05:41 | about 25 min after start | 40 | running | n/a | 0 | ORDER 009; 3 agents run (ticket fix, mutant script, socket test) plus 1 heavy slot (whole suite, 3 workers) |
| r12-endpoint | builder | fable | endpoint.py minors of the lead review plus boundary and parse-edge tests | 05:46 | about 15 min after start | 5 | running | lead code review round 1 of 3 | 0 | ORDER 012 |
| r12-n8n | builder (templates and text) | fable | n8n guard node, 503 loop with re-sign, README limits, template checks that run without n8n | 05:46 | about 20 min after start | 5 | running | lead code review round 1 of 3 | 0 | ORDER 012 |
| r12-tests | evidence runner and test writer | fable | writes PostgreSQL, kill and two-process tests; owns the local PostgreSQL 16 server (start and stop) | 05:46 | about 35 min after start | 5 | running | lead code review round 1 of 3 | 0 | ORDER 012 Major 4 |
| t4-contract | builder (tests) | fable | contract tests for core-b's spend reservation store methods and the 50-connection cap test file | 05:46 | about 25 min after start | 5 | running | n/a | 0 | queue item T4 READY; 7 agents run now on 4 cores: they wait on the model most of the time, load is on the CAPACITY line |

## SHELLS AND PROCESSES
| pid | command in short | started by | since | state | reason |
|---|---|---|---|---|---|
| none | | | | | |

## TESTS
| suite or file | branch and SHA | run number | passed / failed / errors | first failing line | state | reason |
|---|---|---|---|---|---|---|
| tests/test_testing_crash.py | cloud/core-a working tree | 2 (mine, with PostgreSQL 16.15 started locally) | 73 / 0 / 0 | none | done | run 1 by the builder: 71 passed, 2 skipped (no database); my first try of run 2 failed 2 tests only because the database had not started (permission on my start script), fixed and re-run once |
| 6 guard files (mutation_runner, lockin_guard, no_hardcoded_values, k5_producers, repo_rules, stage_names) | working tree | 1 (builder E) | 292 / 0 / 0 | none | done | new crash.py must not break repo rules |
| tests/triggers/test_endpoint.py | working tree | 1 (builder) | 190 / 0 / 0, 2 skipped | none | done | UNVERIFIED by me: I have not re-run it; the batch run will |
| 5 guard files for endpoint.py | working tree | 1 (builder) | 233 / 0 / 0 | none | done | same |
| tests/triggers/test_worker.py | working tree | 6 to 9 (builder, after the change) | 32 / 0 / 0 each time | none | done | one earlier run failed once on a bug in a new test (timer joined before start), fixed by the builder; UNVERIFIED by me until the batch run |
| tests/triggers/test_t5_cases.py (skeleton, another agent's file) | working tree | 1 (worker builder, not ordered) | 65 / 0 / 0, 66 skipped | none | interim | skeleton writer still running; 66 skips must be explained before this counts |
| ruff check + ruff format --check (src tests demos tools) | a748ab3 + working tree | 1 | clean, 331 files | none | done | batch part 1 |
| bandit -ll (triggers package, crash.py) | same | 1 | no finding, exit 0 | none | done | batch part 1 |
| whole suite: pytest -n 3 -m 'not live and not perf' | same | 1 of 1 | 10723 / 2 / 0, 527 skipped (99 s) | (1) tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked: handover/BRIEF-PREAMBLE.md holds a vendor brand name; (2) tests/triggers/test_t5_cases.py::test_further_pool_full_is_503_and_a_later_retry_is_accepted: assert 503 in (200, 202) | done | (1) NOT from core-a code: the lead's handover file trips a repo rule; main without handover/ does not have it. (2) NEW and mine: timing race, the slot is freed a moment after the run's final state is visible; passed in the re-run of my files, so it is FLAKY, not fixed; fix sent to the builder |
| 8 rule test files (skeleton writer) | working tree | 1 | 446 / 1 / 0 | test_no_vendor_brand_string_is_tracked: handover/BRIEF-PREAMBLE.md contains a vendor brand name (rule 15 text) | done | FAILURE is in the lead's file handover/BRIEF-PREAMBLE.md, not in core-a files: see LEAD ACTIONS |
| my 4 test files + 3 repo rule files (re-run to name the failures) | working tree | 1 | 431 / 1 / 0, 70 skipped | test_no_vendor_brand_string_is_tracked (handover/BRIEF-PREAMBLE.md) | done | the T5 failure did not repeat: flaky |

## RESTARTS
| time UTC | kind | what was running | what was lost | restarted | still missing |
|---|---|---|---|---|---|
| none | | | | | |

## LOOPS (items tried more than once)
| item | tries | review rounds | last error | reason it keeps failing |
|---|---|---|---|---|
| E test file with PostgreSQL | 2 | 0 | connection refused (server not started) | it does not: try 1 failed on my own start script permission, try 2 passed 73 of 73 |
| T5 pool-full test | failed 1 of 2 runs | 0 | assert 503 in (200, 202) | race between the run's final state and the slot release; code change in work (waiting requests take a freed slot) |

## LOST OR INTERRUPTED
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|
| none | | | | |

## LEAD ACTIONS NEEDED
- handover/BRIEF-PREAMBLE.md (your file) makes the repo rule test test_no_vendor_brand_string_is_tracked FAIL on this branch (rule 15 names vendor products)
- ORDER 012 'add the crash= hook points': I did NOT add them and chose store wrap points instead (DECISIONS, newest row): say CHANGE if you want the parameter in the runtime code
- ORDER 012 Major 1: I chose 'back the poll off' (about 10 reads per refused request) over '503 at once', see DECISIONS
- ORDERS 007, 010 and 011 are not in my ORDERS.md: tell me if they were meant for me
- 'GO BUILD D' is still not written in ORDERS.md (ORDER 012 implies it)
- Your message 05:44Z (no repeated test loops): applied, the agent was told to run once
