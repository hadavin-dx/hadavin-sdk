UPDATED_UTC: 2026-11-16T09:33:34Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 5
PERCENT: 82
AGENTS_RUNNING: 9
CAPACITY: 0.83 load of 4 cores, mem 0/15 GB, disk free 28G, agents 9 (light+heavy per list)
INTERRUPTED: none
FAILED: F3 independent rerun: 3 of 13 mutants survived and security review found 3 Majors (fixer running, uncapped); roles proposal Blocker fixed, re-review running; claims table round 2 Blockers (fixer running); F5 round 2 reviews found 4 Blockers (fixer running); F6b audit had a defective reset recipe (fixed, re-review launching); 157 citation quotes unmatched (triage running); guard test red from own quoted brand string fixed
NEXT: collect F8/F1/F5/F3 fixers; second reviewers for each; ROLES and F6b r2 reviews
PUSHED_UTC: 2026-11-16T09:33:34Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 92 | CLAIMS-TABLE.md | round 2 fixer running; citation triage running |
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
| aaa5a08748ba9d17a | fixer F8 r1 | sonnet | flow checker fixes | 09:27 | 09:50 | 85 | running | flow-check/ |
| a2bafbe63ce21dd88 | fixer F1 r2 | sonnet | claims table round 2 + ORDER 017 facts | 09:30 | 09:55 | 50 | running | CLAIMS-TABLE.md |
| aff58c29c08810449 | fixer F5 r2 | sonnet | run-sheet wording round 2 | 09:38 | 09:55 | 20 | running | RUNSHEET-WORDING.md |
| a72b276594a01d0e0 | fixer F3 r4 | sonnet | kill 3 mutants + security review fixes | 09:40 | 09:58 | 20 | running | fill_flows/ |
| aee4bb56840c8d24b | citation triage | sonnet | classify unmatched quotes | 09:30 | 09:48 | 70 | running | CITATION-TRIAGE.md |
| ae317761f29afcd16 | reviewer ROLES r2 security | sonnet | least-privilege review | 09:40 | 09:50 | 30 | running | - |
| ac11eac3fda3d70bc | reviewer ROLES r2 reader | sonnet | naive reader | 09:40 | 09:48 | 30 | running | - |
| ac33c5c37ca79b1cb | reviewer F6b r2 facts | sonnet | cites and recipes | 09:41 | 09:50 | 20 | running | - |
| abb0f3dbf87d92397 | reviewer F6b r2 reader | sonnet | naive reader | 09:41 | 09:48 | 20 | running | - |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
