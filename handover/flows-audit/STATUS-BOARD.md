UPDATED_UTC: 2026-11-16T09:22:31Z
SESSION: flows-audit
ORDER: 015 queue (and 008 board)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 10
ITEMS_OPEN: 4
PERCENT: 78
AGENTS_RUNNING: 4
CAPACITY: 0.71 load of 4 cores, mem 0/15 GB, disk free 29G, agents 4 (light+heavy per list)
INTERRUPTED: none
NEXT: F1/F3 fixers land; F8 fixer after code review; F5 fix after F1
PUSHED_UTC: 2026-11-16T09:22:31Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 90 | CLAIMS-TABLE.md | fixer running, then round 2 reviews |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 92 | fill_flows/ | final fixer running, then delta check |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | waiting | 60 | RUNSHEET-WORDING.md | fix after F1 table lands |
| F6 | idle fallback audit | done | 100 | F6-AUDIT.md | 2 review rounds; n8n facts unverified |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied |
| F8 | stronger JSON flow checker | running | 85 | flow-check/REPORT.md | evidence rerun ok; zoom review 7 Majors; codebase review running |
| F9 | scene to flow map | running | 85 | SCENE-FLOW-MAP.md | fixed; round 2 review running |
| H1 | heavy test lane | done | 100 | heavy-test-lane/SUMMARY.md | 2 same failures in both runs, handover guards |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| af1f6cd392311e4c2 | fixer F3 final | sonnet | fill_flows round 2 fixes | 09:10 | 09:30 | 09:30 | running | fill_flows/ |
| ad7e698a4ee4826f8 | fixer F1 | sonnet | claims table batch | 09:15 | 09:35 | 09:30 | running | CLAIMS-TABLE.md |
| af4ac36f3c711b43c | egm-codebase F8 | sonnet | review flow checker | 09:21 | 09:35 | 09:30 | running | none |
| a200d51037af2b6f1 | egm-codebase F9 r2 | sonnet | scene map round 2 | 09:27 | 09:40 | 09:30 | running | none |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
