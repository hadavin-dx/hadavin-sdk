## AGENTS
| id | role | model | what | started UTC | expected end | % | state | review round | retries | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| a5a79255 | builder | fable | step B source (migration 0006, grants, store, limits, CLI) in worktree /tmp/core-b-wt/B | 05:32 | +25 min | UNVERIFIED | running | review runs alongside | 0 | lead GO BUILD B |
| a862ea5f | builder | fable | step C source (config.py price rule, prices_as_of) in worktree /tmp/core-b-wt/C | 05:32 | +15 min | UNVERIFIED | running | review runs alongside | 0 | lead GO BUILD C |
| a86102dd | builder (tests) | fable | tests/test_audit_drain.py and mutants M1 to M9 for step A, worktree /tmp/core-b-wt/A-tests | 05:32 | +25 min | UNVERIFIED | running | none | 0 | tests by a different agent than the builder |
| af8c3d3b | lookup | fable | checks lead draft B against the code, writes tickets/B-stop-state.md | 05:27 | +5 min | UNVERIFIED | running | 0 of 1 | 0 | ORDER 004 item 3 |
| a2c397e1 | lookup | fable | checks lead draft C, writes tickets/C-price-constraint.md | 05:27 | +5 min | UNVERIFIED | running | 0 of 1 | 0 | ORDER 004 item 3 |
| a64fad56 | builder | fable | step A source: commit 5eb1e7e on cloud/core-b (63 lines added, 14 removed) | 05:27 | done | 100 | done | none | 0 | 127 passed, 5 skipped on 4 existing test files; full suite NOT run |
| ae122278 | lookup | fable | notes/heads-money.md | 05:22 | done | 100 | done | n/a | 0 | reserve/settle already exists on P4d-a2 (store) and P4b1 (caller) |
| a367057d | lookup | fable | notes/heads-stop-audit-price.md | 05:22 | done | 100 | done | n/a | 0 | |
| a468ce14 | lookup | fable | LANE-MAP.md | 05:19 | done | 100 | done | n/a | 0 | |
| a65b1e8c, ab7f938c | reviewers (egm) | fable | ORDER 001 dry run | 04:10 | done | 100 | done | 1 of 1 | 0 | proof only |

## SHELLS AND PROCESSES
| pid | command | started by | since | state | reason |
|---|---|---|---|---|---|
| 4886 | PostgreSQL 16.15 server, 127.0.0.1 port 55439, data in /tmp/core-b-pg, trust login, test data only | me | 05:31 | running | per-file tests of the builders (ORDER 005 item 4); I stop it when the builds end |

## TESTS
| suite | branch and SHA | run | passed / failed / errors | first failing line | state | reason |
|---|---|---|---|---|---|---|
| 4 existing files (test_p7_tick, warden_port/test_audit_chain, test_s2_audit, contracts/test_capabilities) | local/code-A 5b92c43 (now 5eb1e7e on cloud/core-b) | 1 | 127 passed / 0 failed / 5 skipped | none | done | step A builder's per-file check; Postgres cases skipped in that run |
| full suite | none | 0 | | | NOT RUN | one batch run when A, B and C are coded (lead order) |

## QUEUE ITEMS
| # | state | % | evidence file | tries | reason |
|---|---|---|---|---|---|
| Q1 capability probe | DONE | 100 | CAPABILITY.md, evidence/capability-raw.txt | 1 | no Docker service, no PostgreSQL 14 or 17, gh login invalid; PostgreSQL 16 works |
| Q2 lane map | DONE | 100 | LANE-MAP.md | 1 | test names come from a text search, not a run; some modules marked UNVERIFIED in the file |
| Q3 to Q9 baselines | SKIPPED BY LEAD | 0 | none | 0 | lead runs them on the laptop |
| T1 plan read-back | DONE | 100 | PLAN-READBACK.md | 1 | 4 conflicts between inputs and 4 questions listed there |
| INTERFACES (i) store methods, (ii) reserve/settle API | DONE | 100 | interfaces/README.md and 4 files | 1 | published version 1; taken from existing branch code (P4d-a2, P4b1), not reviewed, not run |
| T2 tickets (A, B, C, F-store) | RUNNING | 40 | tickets/A-audit-drain.md done; B, C by agents; F-store by me next | 1 | lead draft for F-store announced |
| BUILD A audit drain | RUNNING | 60 | commit 5eb1e7e (source); tests being written | 1 | source done; new test file and mutants not done yet |
| BUILD B stop state | RUNNING | 5 | none yet | 1 | |
| BUILD C price constraint | RUNNING | 5 | none yet | 1 | |
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
- inputs/request-from-core-a-001-config-triggers.md: seen; I build it after step C lands (both edit config.py), answer follows in requests/.
- PLAN-READBACK.md section 4: four conflicts between the inputs; I follow the later file in each.
