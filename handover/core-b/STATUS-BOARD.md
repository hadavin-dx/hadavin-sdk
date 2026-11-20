UPDATED_UTC: 2026-11-20T05:20:39Z
SESSION: core-b
ORDER: 004
STATE: WORKING
BOOT_ID: 2ee8a4de
ITEMS_TOTAL: 6
ITEMS_OPEN: 5
PERCENT: 10
AGENTS_RUNNING: 1
CAPACITY: load 0.04 of 4 cores, mem 0/15 GB, disk 60G free, 13% used, agents light 1 heavy 0
DISK: / 60G free, 13% used; worktrees /tmp/core-b-wt 0
SESSION_RESTARTS: 0
CONTAINER_RESTARTS: 0
INTERRUPTED: none
FAILED: E1 session cron refused by permission check; board runs at the end of each tool batch instead (ESCALATIONS.md)
NEXT: T1 plan read-back, then interface tickets (i) store methods and (ii) reserve/settle API
PUSHED_UTC: 2026-11-20T04:40:08Z (previous push; this board is pushed right after writing)
IST: 10:50 IST

## AGENTS
| id | role | model | what | started UTC | expected end | % | state | review round | retries | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| a468ce14 | lookup | fable | Q2: reads the package and writes LANE-MAP.md | 04:5x | +8 min | UNVERIFIED | running | n/a | 0 | tickets need the file and line facts |
| a65b1e8c | reviewer (egm-comprehension) | fable | ORDER 001 dry run | 04:10 | done | 100 | done | 1 of 1 | 0 | proof only |
| ab7f938c | reviewer (egm-style) | fable | ORDER 001 dry run | 04:10 | done | 100 | done | 1 of 1 | 0 | proof only |

## SHELLS AND PROCESSES
| pid | command | started by | since | state | reason |
|---|---|---|---|---|---|
| none | PostgreSQL 16 probe server (port 55439) | me | 04:5x | stopped and folder deleted | capability probe only |

## TESTS
| suite | branch and SHA | run | passed / failed / errors | first failing line | state | reason |
|---|---|---|---|---|---|---|
| none | | | | | NOT RUN | baselines are run by the lead (GO message item 4); no code written yet |

## QUEUE ITEMS
| # | state | % | evidence file | tries | reason |
|---|---|---|---|---|---|
| Q1 capability probe | DONE | 100 | CAPABILITY.md, evidence/capability-raw.txt | 1 | no Docker service, no PostgreSQL 14 or 17, gh login invalid; PostgreSQL 16 works |
| Q2 lane map | RUNNING | UNVERIFIED | LANE-MAP.md (not yet) | 1 | one lookup agent |
| Q3 to Q9 baselines | SKIPPED BY LEAD | 0 | none | 0 | lead runs them on the laptop |
| T1 plan read-back | RUNNING | 5 | PLAN-READBACK.md (not yet) | 1 | I read the inputs myself |
| T2 tickets (interfaces i, ii first, then A, B, C, F-store) | WAIT T1 | 0 | | 0 | |
| T3 one EGM review round per ticket | WAIT T2 | 0 | | 0 | |
| T4 test files for other sessions | BLOCKED-OWNER | 0 | | 0 | needs a wip branch; owner named only cloud/core-b for this session |

## RESTARTS
| time | kind | what was running | lost | restarted | missing |
|---|---|---|---|---|---|
| none | | | | | |

## LOOPS
| item | tries | review rounds | last error | reason |
|---|---|---|---|---|
| none | | | | |

## LOST OR INTERRUPTED
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|
| none | | | | |

## LEAD ACTIONS NEEDED
- E1: the session cron was refused. Owner: allow it in the cloud session, or accept a board at the end of each tool batch.
- Owner: say yes in the cloud session to pushing wip/cloud-core-b/* branches (needed for step A code and T4). Until then I write tickets and interfaces only on cloud/core-b.
