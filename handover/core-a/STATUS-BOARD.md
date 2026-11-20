UPDATED_UTC: 2026-11-20T05:25:28Z
SESSION: core-a
ORDER: 006 (002 to 005 standing)
STATE: WORKING
BOOT_ID: 3f12152f
ITEMS_TOTAL: 10
ITEMS_OPEN: 6
PERCENT: 46
AGENTS_RUNNING: 2
CAPACITY: load 0.02 of 4 cores (1-minute average), mem 0.6/15.7 GB, 2 language-model agents running (light), 0 heavy test slots unless TESTS shows one
DISK: / size used free 252G 9.2G 60G 14%; 239M /home/user/hadavin-sdk; 39M /tmp/claude-0; 130M /root/.cache
INTERRUPTED: none
FAILED: none
SESSION_RESTARTS: 0
CONTAINER_RESTARTS: 0
NEXT: ticket E lands: build E on cloud/core-a in separate 'code E:' commits (ORDER 005 item 2); ticket D lands: one EGM review round with 2 reviewers
PUSHED_UTC: 2026-11-20T05:25:11Z (the push before this board)
NOTE: one board per minute is driven by a session cron; the cron only fires while the session is not in the middle of a turn, so a board can be up to a few minutes late during long tool batches; ORDER 005 read at 05:23 UTC: code goes on cloud/core-a in separate commits, no wip branch

## QUEUE ITEMS
| item | what | state | percent | evidence file | tries | reason |
|---|---|---|---|---|---|---|
| Q1 | capability probe | DONE | 100 | CAPABILITY.md + raw/capability-raw*.txt | 1 | probe ran once; PostgreSQL 16 starts as non-root (verified); docker and PostgreSQL 14/17 not available |
| Q2 | lane map | DONE | 100 | LANE-MAP.md | 1 | written, 55 lines; tests column is from name search only (agent says so) |
| Q3-Q7 | baselines of existing heads | SKIPPED by lead | 100 | lead puts results in inputs/ | 0 | GO message 2026-11-20: lead runs them on the laptop |
| T1 | plan read-back | DONE | 100 | PLAN-READBACK.md, QUESTIONS.md (10 questions) | 1 | written, 103 lines; 11 of 12 code facts verified in src, 1 does not match (count of test files building Runtime: review says 17, grep finds 7) |
| T2-E | ticket step E test helpers | RUNNING | 30 | tickets/E-test-helpers.md (not yet) | 1 | started before T1 ended: lead note 05:20Z gave draft tickets, see DECISIONS |
| T2-D | ticket step D signed endpoint + worker + n8n template | RUNNING | 30 | tickets/D-signed-endpoint.md (not yet) | 1 | starts from lead draft inputs/draft-tickets-C-D.md, checks every cited line |
| T2-H | ticket step H logic, only if D proves a delta | WAIT T2-D | 0 |  | 0 | ORDER 006: cut unless ticket D proves a delta |
| T3 | one EGM review round for ticket D (and H if written) | WAIT T2 | 0 |  | 0 | E needs no ticket review (ORDER 004 item 3) |
| T4 | store contract test files for core-b interface | BLOCKED-ON-CORE-B | 0 |  | 0 | ORDER 006 answer 9: interface (i) not published yet; lead copies it into inputs/ |
| BUILD-E | build step E on wip/cloud-core-a/E | WAIT T2-E | 0 |  | 0 | allowed as soon as ticket E is written (ORDER 004 item 5) |

## AGENTS
| id | role | model | what exactly it is doing | started UTC | expected end | percent | state | review round n of cap | retries so far | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| a0f5c9e1 | lookup | fable | Q2: reads README, pyproject, conftest, src/hadavin_sdk and writes LANE-MAP.md | 05:19 | ended 05:21 | 100 | done | n/a | 0 | finished 05:21, 151k tokens, LANE-MAP.md written |
| a86435a3 | lookup | fable | T1: reads plan-v2, v3, v4-final and round-3 reviews, writes PLAN-READBACK.md | 05:19 | ended 05:24 | 100 | done | n/a | 0 | finished, 119k tokens, PLAN-READBACK.md written |
| a8e21a19 | builder (ticket writer, no code) | fable | T2-D: checks every line of the lead draft of ticket D against the code, writes tickets/D-signed-endpoint.md, gives the step H verdict | 05:22 | about 15 min after start | 60 | running | n/a | 0 | ORDER 004 item 3; only 2 agents run because the other open items (H, T3, T4, build E) each wait on one of these two tickets or on core-b's interface |
| ac060f95 | builder (ticket writer, no code) | fable | T2-E: writes tickets/E-test-helpers.md (helpers, where they live, guard tests they could break) | 05:22 | about 12 min after start | 60 | running | n/a | 0 | ORDER 004 item 3, E is built first; only 2 agents run because the other open items (H, T3, T4, build E) each wait on one of these two tickets or on core-b's interface |

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
- none: ORDER 006 answered questions 1 to 10; the answers were sent to both running ticket writers
