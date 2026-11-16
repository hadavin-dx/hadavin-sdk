UPDATED_UTC: 2026-11-16T09:36:35Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 12
PERCENT: 70
AGENTS_RUNNING: 9
CAPACITY: 2.30 load of 4 cores, mem 0/15 GB, disk free 28G, agents 9 (light+heavy per list)
INTERRUPTED: none
FAILED: F8 checker: 4 nodes read $env, 2 webhooks lack auth (lead decides: change nodes or allow env); F3 mutants + security Majors (fixer running); roles Majors cut-over/test recipes (fixer running); claims table Blockers and 157 citation mismatches triaged, fix pending; F5 round 2 Blockers (fixer running); F6b Blocker false F-031 cite (fixer running)
NEXT: collect fixers (F5 F3 ROLES F6b F8) then reviewers; claims table checks
PUSHED_UTC: 2026-11-16T09:36:35Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 95 | CLAIMS-TABLE.md | round 2 applied; checker + reader running; citation fixes running |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 95 | fill_flows/ | round 2 fixed (68 tests); delta evidence running |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | waiting | 60 | RUNSHEET-WORDING.md | fix after F1 table lands |
| F6 | idle fallback audit | done | 100 | F6-AUDIT.md | 2 review rounds + reader pass; n8n facts unverified |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied |
| F8 | stronger JSON flow checker | running | 88 | flow-check/ | 3 reviews in; fixer running |
| F9 | scene to flow map | done | 100 | SCENE-FLOW-MAP.md | 2 review rounds; static |
| H1 | heavy test lane | done | 100 | heavy-test-lane/SUMMARY.md | 2 same failures in both runs, handover guards |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| aff58c29c08810449 | fixer F5 r2 | sonnet | run-sheet wording round 2 | 09:38 | 09:55 | 20 | running | RUNSHEET-WORDING.md |
| a72b276594a01d0e0 | fixer F3 r4 | sonnet | kill 3 mutants + security fixes | 09:40 | 09:58 | 20 | running | fill_flows/ |
| a6ad3edfc302e7503 | reviewer F8 r2 false passes | sonnet | checker review | 09:36 | 09:46 | 30 | running | - |
| a46dc96a5a052f767 | fixer ROLES r2 | sonnet | roles proposal fixes | 09:37 | 09:55 | 20 | running | ROLES-PROPOSAL.md |
| aa504d5c80158c02a | fixer F6b r2 | sonnet | recovery audit final | 09:37 | 09:50 | 20 | running | F6B-AUDIT.md |
| ab790c7cf5d1d6137 | fixer F8 r2 | sonnet | REPORT.md start-here + header | 09:37 | 09:50 | 20 | running | flow-check/ |
| abdcd0eb5b88874ac | fixer citation fixes | sonnet | verify corrected cites | 09:40 | 09:52 | 20 | running | CITATION-FIXES.md |
| a7f2cd9786d9853a0 | evidence claims table | sonnet | structure and count check | 09:41 | 09:48 | 20 | running | evidence-claims-r2.md |
| ad6734b1e2cd31372 | reviewer claims table reader | sonnet | naive reader | 09:41 | 09:48 | 30 | running | - |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
