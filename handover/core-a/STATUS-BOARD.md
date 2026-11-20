UPDATED_UTC: 2026-11-20T05:21:11Z
SESSION: core-a
ORDER: 004 (002 and 003 standing)
STATE: WORKING
BOOT_ID: 3f12152f
ITEMS_TOTAL: 10
ITEMS_OPEN: 8
PERCENT: 24
AGENTS_RUNNING: 2
CAPACITY: load 0.07 of 4 cores (1-minute average), mem 0.5/15.7 GB, 2 language-model agents running (light), 0 heavy test slots unless TESTS shows one
DISK: / size used free 252G 9.1G 60G 14%; 238M /home/user/hadavin-sdk; 48K /tmp/claude-0; 130M /root/.cache
INTERRUPTED: none
FAILED: none
SESSION_RESTARTS: 0
CONTAINER_RESTARTS: 0
NEXT: when T1 plan read-back lands: start ticket E and ticket D writers in parallel
PUSHED_UTC: none yet (the push before this board)
NOTE: one board per minute is driven by a session cron; the cron only fires while the session is not in the middle of a turn, so a board can be up to a few minutes late during long tool batches

## QUEUE ITEMS
| item | what | state | percent | evidence file | tries | reason |
|---|---|---|---|---|---|---|
| Q1 | capability probe | DONE | 100 | CAPABILITY.md + raw/capability-raw*.txt | 1 | probe ran once; docker and PostgreSQL 14/17 not available, see file |
| Q2 | lane map | RUNNING | 20 | LANE-MAP.md (not yet) | 1 | lookup agent reading the package |
| Q3-Q7 | baselines of existing heads | SKIPPED by lead | 100 | lead puts results in inputs/ | 0 | GO message 2026-11-20: lead runs them on the laptop |
| T1 | plan read-back | RUNNING | 20 | PLAN-READBACK.md (not yet) | 1 | lookup agent reading inputs/ plans and round-3 reviews |
| T2-E | ticket step E test helpers | WAIT T1 | 0 |  | 0 | queue marks tickets WAIT T1 |
| T2-D | ticket step D signed endpoint + worker + n8n template | WAIT T1 | 0 |  | 0 | queue marks tickets WAIT T1 |
| T2-H | ticket step H logic, only if D proves a delta | WAIT T2-D | 0 |  | 0 | ORDER 004 item 1 |
| T3 | one EGM review round for ticket D (and H if written) | WAIT T2 | 0 |  | 0 | E needs no ticket review (ORDER 004 item 3) |
| T4 | store contract test files for core-b interface | WAIT interfaces | 0 |  | 0 | READY only after interfaces are published |
| BUILD-E | build step E on wip/cloud-core-a/E | WAIT T2-E | 0 |  | 0 | allowed as soon as ticket E is written (ORDER 004 item 5) |

## AGENTS
| id | role | model | what exactly it is doing | started UTC | expected end | percent | state | review round n of cap | retries so far | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| a0f5c9e1 | lookup | fable | Q2: reads README, pyproject, conftest, src/hadavin_sdk and writes LANE-MAP.md | 05:22 | 05:32 | 20 | running | n/a | 0 | queue item Q2 READY |
| a86435a3 | lookup | fable | T1: reads plan-v2, v3, v4-final and round-3 reviews, writes PLAN-READBACK.md | 05:22 | 05:34 | 20 | running | n/a | 0 | queue item T1 READY |

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
