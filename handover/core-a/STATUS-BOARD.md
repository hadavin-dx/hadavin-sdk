UPDATED_UTC: 2026-11-20T05:33:43Z
SESSION: core-a
ORDER: 006 (002 to 005 standing)
STATE: WORKING
BOOT_ID: 3f12152f
ITEMS_TOTAL: 14
ITEMS_OPEN: 8
PERCENT: 54
AGENTS_RUNNING: 6
CAPACITY: load 0.39 of 4 cores (1-minute average), mem 0.6/15.7 GB, 6 language-model agents running (light), 0 heavy test slots unless TESTS shows one
DISK: / size used free 252G 9.2G 60G 14%; 248M /home/user/hadavin-sdk; 39M /tmp/claude-0; 130M /root/.cache
INTERRUPTED: none
FAILED: none
SESSION_RESTARTS: 0
CONTAINER_RESTARTS: 0
NEXT: reviews land: resolve, write tickets/D-review-1.md, pass accepted fixes to the D builders; builds land: commit and ONE batch run
PUSHED_UTC: 2026-11-20T05:33:30Z (the push before this board)
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
| T3 | one EGM review round for ticket D (and H if written) | RUNNING | 10 | tickets/D-review-1.md (not yet) | 1 | one round, 2 EGM reviewers in parallel, started through the Skill tool |
| T4 | store contract test files for core-b interface | BLOCKED-ON-CORE-B | 0 |  | 0 | ORDER 006 answer 9: interface (i) not published yet; lead copies it into inputs/ |
| BUILD-E | build step E on wip/cloud-core-a/E | RUNNING | 10 | raw/E-tests.log, raw/E-guards.log, raw/E-mutants.log (not yet) | 1 | ticket E on disk with invariants; builder writes 2 new files, runs its own file, 6 guard files and 4 mutants |
| T5-SKEL | T5 test file skeleton (tests/triggers/) and n8n template outline (n8n/) | RUNNING | 25 | tests/triggers/test_t5_cases.py, n8n/*.json, n8n/README-trigger.md (not yet) | 1 | lead message 05:27Z asks for it now; whole test module is skipped until the package exists |
| BUILD-D-endpoint | src/hadavin_sdk/triggers/endpoint.py + tests/triggers/test_endpoint.py | RUNNING | 5 | raw/D-endpoint-tests.log, -guards.log, -mutants.log (not yet) | 1 | lead message GO BUILD D at 05:30Z; built from the lead draft while ticket D is still being checked |
| BUILD-D-worker | src/hadavin_sdk/triggers/worker.py + tests/triggers/test_worker.py | RUNNING | 5 | raw/D-worker-tests.log, -mutants.log (not yet) | 1 | same; codes against the fixed interface of endpoint.py; main() exits 2 today because core-b's Config.triggers does not exist yet |
| BATCH | ONE batch test run when E and D are both coded | WAIT builds | 0 |  | 0 | lead: tests in batches only |

## AGENTS
| id | role | model | what exactly it is doing | started UTC | expected end | percent | state | review round n of cap | retries so far | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| a0f5c9e1 | lookup | fable | Q2: reads README, pyproject, conftest, src/hadavin_sdk and writes LANE-MAP.md | 05:19 | ended 05:21 | 100 | done | n/a | 0 | finished 05:21, 151k tokens, LANE-MAP.md written |
| a86435a3 | lookup | fable | T1: reads plan-v2, v3, v4-final and round-3 reviews, writes PLAN-READBACK.md | 05:19 | ended 05:24 | 100 | done | n/a | 0 | finished, 119k tokens, PLAN-READBACK.md written |
| a8e21a19 | builder (ticket writer, no code) | fable | T2-D: checks every line of the lead draft of ticket D against the code, writes tickets/D-signed-endpoint.md, gives the step H verdict | 05:22 | ended | 100 | done | n/a | 0 | finished, 247k tokens, ticket D written |
| ac060f95 | builder (ticket writer, no code) | fable | T2-E: writes tickets/E-test-helpers.md (helpers, where they live, guard tests they could break) | 05:22 | ended | 100 | done | n/a | 0 | finished, 220k tokens, ticket E written (nothing run for the ticket) |
| t5-skel | builder (tests and templates, new files only) | fable | writes the T5 test skeleton and two n8n workflow outlines plus a README; runs ruff and pytest on its own folder only | 05:27 | about 15 min after start | 10 | running | n/a | 0 | third parallel item; 3 agents now run |
| build-E | builder | fable | step E: src/hadavin_sdk/testing/crash.py and tests/test_testing_crash.py; ruff, its own test file, 6 guard test files, 4 mutants, bandit | 05:28 | about 25 min after start | 10 | running | n/a (E needs no ticket review) | 0 | ORDER 004 item 5: E may be built once its ticket is written; 4 agents now run |
| build-D-ep | builder | fable | endpoint.py: run id derivation, signature check with two secrets, WSGI app, unit tests in-process, 3 mutants | 05:30 | about 30 min after start | 5 | running | review runs alongside (0 of 1 started) | 0 | GO BUILD D |
| build-D-wk | builder | fable | worker.py: Runner (ack only after the run row exists, bounded pool), main, thread tests, 3 mutants | 05:30 | about 30 min after start | 5 | running | review runs alongside (0 of 1 started) | 0 | GO BUILD D; 5 agents now run on 4 cores, they are mostly waiting on the model, load is on the board |
| egm-impl-ready | reviewer | fable | egm:egm-implementation-readiness reads ticket D against its standard | 05:31 | about 10 min after start | 10 | running | 1 of 1 | 0 | ORDER 004 item 3 |
| egm-codebase | reviewer | fable | egm:egm-codebase-details checks ticket D claims against the code | 05:31 | about 10 min after start | 10 | running | 1 of 1 | 0 | ORDER 004 item 3; 6 agents run now (3 builders, 1 skeleton writer, 2 reviewers) |

## SHELLS AND PROCESSES
| pid | command in short | started by | since | state | reason |
|---|---|---|---|---|---|
| none | | | | | |

## TESTS
| suite or file | branch and SHA | run number | passed / failed / errors | first failing line | state | reason |
|---|---|---|---|---|---|---|
| none | | | | | | |

## RESTARTS
| time UTC | kind | what was running | what was lost | restarted | still missing |
|---|---|---|---|---|---|
| none | | | | | |

## LOOPS (items tried more than once)
| item | tries | review rounds | last error | reason it keeps failing |
|---|---|---|---|---|
| none | | | | |

## LOST OR INTERRUPTED
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|
| none | | | | |

## LEAD ACTIONS NEEDED
- Please write 'GO BUILD D' into ORDERS.md: ORDER 004 item 5 says the GO must be in that file; I acted on your message of 05:30Z (see DECISIONS)
