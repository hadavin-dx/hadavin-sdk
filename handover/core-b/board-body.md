## AGENTS
| id | role | model | what | started UTC | expected end | % | state | review round | retries | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| a468ce14 | lookup | fable | Q2: reads the package and writes LANE-MAP.md | 05:19 | done | 100 | done | n/a | 0 | tickets need the file and line facts |
| ae122278 | lookup | fable | reads input branches P4b1, P4d, P4d-a2, P4a, T1-T2 for what reserve/settle code already exists; writes notes/heads-money.md | 05:27 | +10 min | UNVERIFIED | running | n/a | 0 | interface tickets must reuse, not rebuild |
| a367057d | lookup | fable | reads main and branches P2a-1, P4a for steps A, B, C facts; writes notes/heads-stop-audit-price.md | 05:27 | +10 min | UNVERIFIED | running | n/a | 0 | tickets A, B, C need file and line facts |
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
| Q2 lane map | DONE | 100 | LANE-MAP.md | 1 | test names come from a text search, not a run; some modules marked UNVERIFIED in the file |
| Q3 to Q9 baselines | SKIPPED BY LEAD | 0 | none | 0 | lead runs them on the laptop |
| T1 plan read-back | DONE | 100 | PLAN-READBACK.md | 1 | 4 conflicts between inputs and 4 questions listed there |
| T2 tickets (interfaces i, ii first, then A, B, C, F-store) | RUNNING | 5 | interfaces/, tickets/ (not yet) | 1 | waiting for the two lookup notes; I read store code meanwhile |
| T3 one EGM review round per ticket | WAIT T2 | 0 | | 0 | |
| T4 test files for other sessions | WAIT | 0 | | 0 | starts when interfaces are published; owner allowed wip/cloud-core-b/* at 05:21 |

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
- E1: the session cron was refused twice (second time after the owner's GO). Owner: allow it in the cloud session settings, or accept a board at the end of each tool batch.
- QUESTIONS.md 1 to 4 (cron fallback, which baseline test fails, step A build without extra GO, local PostgreSQL 16 for my lane run).
- PLAN-READBACK.md section 4: four conflicts between the inputs; I follow the later file in each.
