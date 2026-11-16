UPDATED_UTC: 2026-11-16T09:43:06Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 7
PERCENT: 72
AGENTS_RUNNING: 6
CAPACITY: 4.79 load of 4 cores, mem 0/15 GB, disk free 28G, agents 6 (light+heavy per list)
INTERRUPTED: none
FAILED: F8: $env nodes, 2 webhooks without auth, 7 false-pass Majors (fixer running)
F3: 3 surviving mutants + 3 security Majors (fixer running)
ROLES script: 5 mutants survive (SQL in Code/MySQL/postgresTool/Set; fixer running)
claims: no fresh review of r3 yet (2 reviewers running); F-01 unreadable; 'the lead' wording left in pasted text
F5: T8 Blocker (final fixer running)
NEXT: collect F3, F8, F5, ROLES r3 reviewer and survivor fixer, 2 claims reviewers; then evidence reruns
PUSHED_UTC: 2026-11-16T09:43:06Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 95 | CLAIMS-TABLE.md | round 2 applied; checker + reader running; citation fixes running |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 95 | fill_flows/ | round 2 fixed (68 tests); delta evidence running |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | running | 85 | RUNSHEET-WORDING.md | final fixer running |
| F6 | idle fallback + recovery audit | done | 100 | F6-AUDIT.md, F6B-AUDIT.md | n8n facts unverified; F6b SQL untested |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied |
| F8 | stronger JSON flow checker | running | 88 | flow-check/ | 3 reviews in; fixer running |
| F9 | scene to flow map | done | 100 | SCENE-FLOW-MAP.md | 2 review rounds; static |
| H1 | heavy test lane | done | 100 | heavy-test-lane/SUMMARY.md | 2 same failures in both runs, handover guards |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| a72b276594a01d0e0 | fixer F3 r4 | sonnet | kill 3 mutants + security fixes | 09:40 | 09:58 | 20 | running | fill_flows/ |
| ab790c7cf5d1d6137 | fixer F8 r2 | sonnet | REPORT.md start-here + header | 09:37 | 09:50 | 20 | running | flow-check/ |
| (roles sec r3) | reviewer ROLES security r3 | sonnet | fresh security design | 09:57 | 10:05 | 30 | running | - |
| a95683a64bf2e3ca8 | fixer F5 final | sonnet | Blockers and Majors from r3 reader and facts | 10:03 | 10:13 | 20 | running | RUNSHEET-WORDING.md |
| (claims r3 fixer) | fixer claims table reader fixes | sonnet | Blockers/Majors from reader | 10:04 | 10:15 | 30 | running | CLAIMS-TABLE.md |
| (roles rerun) | evidence ROLES script rerun | sonnet | 18 own mutants | 10:08 | 10:16 | 30 | running | roles-coverage-check/evidence-rerun.md |
| a643eeae | ROLES survivors fixer | sonnet | fix 5 surviving mutants in coverage script | 09:44 | 09:55 | 5 | running | roles-coverage-check/fix-roles-r4.md |
| ae5d88f1 | claims reader r3 | egm-comprehension | naive read of CLAIMS-TABLE | 09:44 | 09:52 | 5 | running | inline |
| aa4dd7eb | claims facts r3 | egm-codebase-details | cites and totals check | 09:44 | 09:55 | 5 | running | inline |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
