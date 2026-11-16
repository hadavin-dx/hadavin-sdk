UPDATED_UTC: 2026-11-16T09:20:59Z
SESSION: flows-audit
ORDER: 015 queue (and 008 board)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 6
PERCENT: 74
AGENTS_RUNNING: 8
CAPACITY: 0.61 load of 4 cores, mem 0/15 GB, disk free 29G, agents 8 (light+heavy per list)
INTERRUPTED: none
NEXT: F1 fixer lands then F1 round 2 + F5 fixer; F3 delta check; F8/F6/F9 reviews
PUSHED_UTC: 2026-11-16T09:20:59Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 90 | CLAIMS-TABLE.md | fixer running, then round 2 reviews |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 92 | fill_flows/ | final fixer running, then delta check |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | waiting | 60 | RUNSHEET-WORDING.md | fix after F1 table lands |
| F6 | idle fallback audit | running | 85 | F6-AUDIT.md | reviewed, fixer running |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied |
| F8 | stronger JSON flow checker | running | 80 | flow-check/REPORT.md | built; 2 reviewers running |
| F9 | scene to flow map | running | 70 | SCENE-FLOW-MAP.md | reviewed, fixer running |
| H1 | heavy test lane | done | 100 | heavy-test-lane/SUMMARY.md | 2 same failures in both runs, handover guards |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| af1f6cd392311e4c2 | fixer F3 final | sonnet | fill_flows round 2 fixes | 09:10 | 09:30 | 09:20 | running | fill_flows/ |
| ad7e698a4ee4826f8 | fixer F1 | sonnet | claims table batch | 09:15 | 09:35 | 09:20 | running | CLAIMS-TABLE.md |
| af04e87f9617e79b8 | fixer F9 | sonnet | scene flow map fixes | 09:21 | 09:35 | 09:21 | running | SCENE-FLOW-MAP.md |
| af6d99f36b2c5aa09 | fixer F6 | sonnet | F6 audit fixes | 09:21 | 09:35 | 09:21 | running | F6-AUDIT.md |
| af4ac36f3c711b43c | egm-codebase F8 | sonnet | review flow checker | 09:21 | 09:35 | 09:21 | running | none |
| a53a6dec75ffb4273 | egm-zoom-out F8 | sonnet | review flow checker | 09:21 | 09:35 | 09:21 | running | none |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
