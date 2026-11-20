UPDATED_UTC: 2026-11-20T05:22:33Z
SESSION: core-a
ORDER: 004 (002 and 003 standing)
STATE: WORKING
BOOT_ID: 3f12152f
ITEMS_TOTAL: 10
ITEMS_OPEN: 7
PERCENT: 38
AGENTS_RUNNING: 3
CAPACITY: load 0.02 of 4 cores (1-minute average), mem 0.5/15.7 GB, 3 language-model agents running (light), 0 heavy test slots unless TESTS shows one
DISK: / size used free 252G 9.1G 60G 14%; 238M /home/user/hadavin-sdk; 60K /tmp/claude-0; 130M /root/.cache
INTERRUPTED: none
FAILED: none
SESSION_RESTARTS: 0
CONTAINER_RESTARTS: 0
NEXT: when ticket E lands: cut wip/cloud-core-a/E from origin/main in its own worktree and build E; when ticket D lands: one EGM review round
PUSHED_UTC: none yet (the push before this board)
NOTE: one board per minute is driven by a session cron; the cron only fires while the session is not in the middle of a turn, so a board can be up to a few minutes late during long tool batches

## QUEUE ITEMS
| item | what | state | percent | evidence file | tries | reason |
|---|---|---|---|---|---|---|
| Q1 | capability probe | DONE | 100 | CAPABILITY.md + raw/capability-raw*.txt | 1 | probe ran once; docker and PostgreSQL 14/17 not available, see file |
| Q2 | lane map | DONE | 100 | LANE-MAP.md | 1 | written, 55 lines; tests column is from name search only (agent says so) |
| Q3-Q7 | baselines of existing heads | SKIPPED by lead | 100 | lead puts results in inputs/ | 0 | GO message 2026-11-20: lead runs them on the laptop |
| T1 | plan read-back | RUNNING | 50 | PLAN-READBACK.md (not yet) | 1 | lookup agent reading inputs/ plans and round-3 reviews |
| T2-E | ticket step E test helpers | RUNNING | 15 | tickets/E-test-helpers.md (not yet) | 1 | started before T1 ended: lead note 05:20Z gave draft tickets, see DECISIONS |
| T2-D | ticket step D signed endpoint + worker + n8n template | RUNNING | 15 | tickets/D-signed-endpoint.md (not yet) | 1 | starts from lead draft inputs/draft-tickets-C-D.md, checks every cited line |
| T2-H | ticket step H logic, only if D proves a delta | WAIT T2-D | 0 |  | 0 | ticket D agent gives the verdict on a delta; lead draft says cut |
| T3 | one EGM review round for ticket D (and H if written) | WAIT T2 | 0 |  | 0 | E needs no ticket review (ORDER 004 item 3) |
| T4 | store contract test files for core-b interface | WAIT interfaces | 0 |  | 0 | READY only after interfaces are published |
| BUILD-E | build step E on wip/cloud-core-a/E | WAIT T2-E | 0 |  | 0 | allowed as soon as ticket E is written (ORDER 004 item 5) |

## AGENTS
| id | role | model | what exactly it is doing | started UTC | expected end | percent | state | review round n of cap | retries so far | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| a0f5c9e1 | lookup | fable | Q2: reads README, pyproject, conftest, src/hadavin_sdk and writes LANE-MAP.md | 05:19 | ended 05:21 | 100 | done | n/a | 0 | finished 05:21, 151k tokens, LANE-MAP.md written |
| a86435a3 | lookup | fable | T1: reads plan-v2, v3, v4-final and round-3 reviews, writes PLAN-READBACK.md | 05:19 | 05:31 | 50 | running | n/a | 0 | queue item T1 READY |
| a8e21a19 | builder (ticket writer, no code) | fable | T2-D: checks every line of the lead draft of ticket D against the code, writes tickets/D-signed-endpoint.md, gives the step H verdict | 05:22 | about 15 min after start | 15 | running | n/a | 0 | ORDER 004 item 3 |
| ac060f95 | builder (ticket writer, no code) | fable | T2-E: writes tickets/E-test-helpers.md (helpers, where they live, guard tests they could break) | 05:22 | about 12 min after start | 15 | running | n/a | 0 | ORDER 004 item 3, E is built first |

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
- none right now
